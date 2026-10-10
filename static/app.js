const form = document.querySelector("#download-form");
const urlInput = document.querySelector("#video-url");
const qualitySelect = document.querySelector("#quality");
const mainButton = document.querySelector("#main-button");
const buttonLabel = document.querySelector("#button-label");
const notice = document.querySelector("#notice");
const videoPanel = document.querySelector("#video-panel");
const progressPanel = document.querySelector("#progress-panel");
const fileLink = document.querySelector("#file-link");
const pasteButton = document.querySelector("#paste-link");
const clearButton = document.querySelector("#clear-link");

let videoInfo = null;
let activeJobId = null;
let polling = false;

function setBusy(isBusy, label) {
  mainButton.disabled = isBusy;
  mainButton.classList.toggle("busy", isBusy);
  if (label) buttonLabel.textContent = label;
}

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  notice.hidden = !message;
}

function formatDuration(seconds) {
  if (seconds == null) return "Durasi tidak diketahui";
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  return hours
    ? hours + ":" + String(minutes).padStart(2, "0") + ":" + String(secs).padStart(2, "0")
    : minutes + ":" + String(secs).padStart(2, "0");
}

function syncClearButton() {
  clearButton.hidden = !urlInput.value.trim();
}

function showVideo(info) {
  document.querySelector("#video-title").textContent = info.title;
  const parts = [];
  if (info.channel) parts.push(info.channel);
  parts.push(formatDuration(info.duration));
  document.querySelector("#video-meta").textContent = parts.join(" · ");

  const formats = document.querySelector("#formats-list");
  formats.replaceChildren();
  const entries = info.formats || [];
  document.querySelector("#format-count").textContent = entries.length ? entries.length + " format video" : "format belum terdeteksi";
  if (!entries.length) {
    const chip = document.createElement("span");
    chip.className = "format-chip";
    chip.textContent = "Kualitas akan ditentukan saat unduh";
    formats.append(chip);
  } else {
    entries.forEach((item, index) => {
      const chip = document.createElement("span");
      chip.className = "format-chip" + (index === 0 ? " best" : "");
      chip.textContent = item.height + "p" + (item.fps ? " · " + item.fps + " fps" : "") + (item.ext ? " · " + item.ext : "");
      formats.append(chip);
    });
  }
  videoPanel.hidden = false;
}

urlInput.addEventListener("input", () => {
  syncClearButton();
  if (videoInfo) {
    videoInfo = null;
    videoPanel.hidden = true;
    progressPanel.hidden = true;
    fileLink.hidden = true;
    buttonLabel.textContent = "Periksa video";
    showNotice("");
  }
});

clearButton.addEventListener("click", () => {
  urlInput.value = "";
  urlInput.dispatchEvent(new Event("input", { bubbles: true }));
  urlInput.focus();
  showNotice("");
});

pasteButton.addEventListener("click", async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      throw new Error("Akses clipboard tidak tersedia.");
    }
    const pasted = await navigator.clipboard.readText();
    if (!pasted.trim()) {
      showNotice("Clipboard kosong.", true);
      return;
    }
    urlInput.value = pasted.trim();
    urlInput.dispatchEvent(new Event("input", { bubbles: true }));
    urlInput.focus();
    showNotice("Tautan ditempel. Tekan Periksa video untuk melanjutkan.");
  } catch (error) {
    showNotice("Tidak bisa membaca clipboard. Izinkan akses clipboard atau tempel dengan Ctrl+V.", true);
  }
});

syncClearButton();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (activeJobId || mainButton.disabled) return;

  const url = urlInput.value.trim();
  if (!videoInfo) {
    setBusy(true, "Memeriksa video…");
    showNotice("");
    try {
      const response = await fetch("/api/info?url=" + encodeURIComponent(url));
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Video tidak dapat diperiksa.");
      videoInfo = data;
      showVideo(data);
      buttonLabel.textContent = "Mulai unduh";
      showNotice("Video terdeteksi. Resolusi yang dipilih akan digunakan jika tersedia.");
    } catch (error) {
      showNotice(error.message, true);
    } finally {
      setBusy(false, videoInfo ? "Mulai unduh" : "Periksa video");
    }
    return;
  }

  setBusy(true, "Menyiapkan unduhan…");
  showNotice("");
  fileLink.hidden = true;
  progressPanel.hidden = false;
  document.querySelector("#progress-message").textContent = "Memasukkan ke antrean…";
  document.querySelector("#progress-percent").textContent = "0%";
  document.querySelector("#progress-fill").style.width = "0%";
  try {
    const response = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, quality: qualitySelect.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unduhan tidak dapat dimulai.");
    activeJobId = data.job_id;
    buttonLabel.textContent = "Sedang mengunduh…";
    setBusy(true);
    pollJob();
  } catch (error) {
    progressPanel.hidden = true;
    showNotice(error.message, true);
    setBusy(false, "Mulai unduh");
  }
});

async function pollJob() {
  if (polling || !activeJobId) return;
  polling = true;
  try {
    const response = await fetch("/api/jobs/" + encodeURIComponent(activeJobId));
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Status unduhan tidak tersedia.");

    document.querySelector("#progress-message").textContent = data.message || "Memproses…";
    const percent = Math.round(data.percent || 0);
    document.querySelector("#progress-percent").textContent = percent + "%";
    document.querySelector("#progress-fill").style.width = percent + "%";
    document.querySelector("#progress-speed").textContent = data.speed ? "Kecepatan " + data.speed : "";
    document.querySelector("#progress-eta").textContent = data.eta ? "Sisa " + data.eta : "";

    if (data.state === "done") {
      fileLink.href = "/api/jobs/" + encodeURIComponent(activeJobId) + "/file";
      fileLink.download = data.filename || "";
      fileLink.hidden = false;
      showNotice("Video selesai diunduh dan tersimpan di folder downloads.");
      activeJobId = null;
      setBusy(false, "Selesai");
      return;
    }
    if (data.state === "error") {
      showNotice(data.message || "Unduhan gagal.", true);
      activeJobId = null;
      setBusy(false, "Coba lagi");
      return;
    }
  } catch (error) {
    showNotice(error.message, true);
    activeJobId = null;
    setBusy(false, "Coba lagi");
  } finally {
    polling = false;
  }
  if (activeJobId) window.setTimeout(pollJob, 1100);
}



