from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from yt_dlp import YoutubeDL

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

QUALITY_PROFILES = {
    "4320": {
        "label": "4320p · 8K · sampai 60 fps",
        "format": "bestvideo[height<=4320][fps<=60]+bestaudio/best[height<=4320][fps<=60]",
    },
    "2160": {
        "label": "2160p · 4K · sampai 60 fps",
        "format": "bestvideo[height<=2160][fps<=60]+bestaudio/best[height<=2160][fps<=60]",
    },
    "1440": {
        "label": "1440p · 2K · sampai 60 fps",
        "format": "bestvideo[height<=1440][fps<=60]+bestaudio/best[height<=1440][fps<=60]",
    },
    "1080": {
        "label": "1080p · Full HD · sampai 60 fps",
        "format": "bestvideo[height<=1080][fps<=60]+bestaudio/best[height<=1080][fps<=60]",
    },
    "720": {
        "label": "720p · HD · sampai 60 fps",
        "format": "bestvideo[height<=720][fps<=60]+bestaudio/best[height<=720][fps<=60]",
    },
    "best": {
        "label": "Tertinggi yang tersedia · sampai 60 fps",
        "format": "bestvideo[fps<=60]+bestaudio/best[fps<=60]",
    },
}


def validate_youtube_url(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Masukkan tautan video YouTube.")
    url = value.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not (
        host == "youtube.com" or host.endswith(".youtube.com") or host == "youtu.be"
    ):
        raise ValueError("Gunakan tautan HTTPS dari youtube.com atau youtu.be.")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Tautan video belum lengkap.")
    return url


def ydl_options() -> dict:
    deno = shutil.which("deno")
    if not deno:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            package_root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
            candidates = sorted(package_root.glob("DenoLand.Deno*/deno.exe"))
            if candidates:
                deno_dir = str(candidates[-1].parent)
                os.environ["PATH"] = deno_dir + os.pathsep + os.environ.get("PATH", "")
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
        "windowsfilenames": True,
    }
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            package_root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
            candidates = sorted(package_root.glob("Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe"))
            if candidates:
                ffmpeg = str(candidates[-1])
    if ffmpeg:
        options["ffmpeg_location"] = str(Path(ffmpeg).parent)
    return options


def video_formats(info: dict) -> list[str]:
    found = set()
    for item in info.get("formats") or []:
        height = item.get("height")
        if not height or item.get("vcodec") == "none":
            continue
        fps = int(item.get("fps") or 0)
        found.add((int(height), fps, str(item.get("ext") or "").upper()))
    return [
        f"{height}p" + (f" · {fps} fps" if fps else "") + (f" · {ext}" if ext else "")
        for height, fps, ext in sorted(found, reverse=True)[:18]
    ]


def get_video_info(url: str) -> dict:
    with YoutubeDL({**ydl_options(), "skip_download": True, "extract_flat": False}) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("Informasi video tidak ditemukan.")
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise ValueError("Video siaran langsung atau terjadwal tidak didukung.")
    info["display_formats"] = video_formats(info)
    return info


def get_output_file(info: dict) -> Path | None:
    video_id = str(info.get("id") or "")
    candidates = [
        path for path in DOWNLOAD_DIR.iterdir()
        if path.is_file()
        and f"[{video_id}]" in path.stem
        and not path.name.endswith((".part", ".ytdl"))
    ]
    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime)
    prepared = Path(info.get("_filename") or "")
    if prepared.is_file():
        return prepared
    return None


def download_video(url: str, quality: str) -> Path:
    profile = QUALITY_PROFILES[quality]
    progress = st.progress(0)
    status = st.empty()

    def progress_hook(data: dict) -> None:
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            percent = (data.get("downloaded_bytes", 0) / total) if total else 0
            progress.progress(min(max(percent, 0.0), 0.999))
            details = data.get("_percent_str") or "Mengunduh…"
            speed = data.get("_speed_str")
            eta = data.get("_eta_str")
            if speed:
                details += " · " + speed
            if eta:
                details += " · sisa " + eta
            status.caption(details)
        elif data.get("status") == "finished":
            progress.progress(1.0)
            status.caption("Menggabungkan video dan audio…")

    options = ydl_options()
    options.update({
        "format": profile["format"],
        "outtmpl": str(DOWNLOAD_DIR / "%(title).180B [%(id)s].%(ext)s"),
        "merge_output_format": "mkv",
        "progress_hooks": [progress_hook],
    })
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
    final_file = get_output_file(info or {})
    if not final_file:
        raise RuntimeError("Unduhan selesai tetapi file tidak ditemukan di folder downloads.")
    progress.progress(1.0)
    status.caption("Unduhan selesai.")
    return final_file


def paste_from_clipboard() -> None:
    try:
        if os.name != "nt":
            raise RuntimeError("Tombol clipboard tersedia saat aplikasi berjalan lokal di Windows. Gunakan Ctrl+V.")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
            check=True,
        )
        value = result.stdout.strip()
        if not value:
            raise RuntimeError("Clipboard kosong.")
        st.session_state.video_url = value
        st.session_state.video_info = None
        st.session_state.clipboard_message = "Tautan ditempel dari clipboard."
    except Exception as exc:
        st.session_state.clipboard_message = str(exc) or "Clipboard tidak dapat dibaca."


def clear_link() -> None:
    st.session_state.video_url = ""
    st.session_state.video_info = None
    st.session_state.clipboard_message = ""


def reset_info() -> None:
    st.session_state.video_info = None


st.set_page_config(page_title="WebDownloadDede", page_icon="⬇️", layout="centered")
st.markdown(
    """
    <style>
      .block-container {max-width: 850px; padding-top: 2.6rem; padding-bottom: 3rem;}
      h1 {letter-spacing: -0.04em;}
      .hero-copy {color: #697586; font-size: 1.05rem;}
      div.stButton > button {border-radius: 9px; min-height: 2.7rem; font-weight: 650;}
      div[data-testid="stSelectbox"] div[data-baseweb="select"] {border-radius: 9px;}
      .local-note {padding: .8rem 1rem; border: 1px solid #e1e7ef; border-radius: 10px; background: #f7f9fc; color: #647184;}
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "video_url": "",
    "video_info": None,
    "clipboard_message": "",
    "last_download_path": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.title("WebDownloadDede")
st.markdown('<p class="hero-copy">Unduh video yang memang boleh kamu simpan, hingga 8K · 4320p60 jika tersedia dari sumber.</p>', unsafe_allow_html=True)

paste_col, url_col, clear_col = st.columns([1.1, 7, 1.2], vertical_alignment="bottom")
with paste_col:
    st.button("Tempel", use_container_width=True, on_click=paste_from_clipboard, help="Tempel tautan dari clipboard")
with url_col:
    st.text_input(
        "Tautan video YouTube",
        placeholder="https://www.youtube.com/watch?v=...",
        key="video_url",
        on_change=reset_info,
    )
with clear_col:
    st.button("Hapus", use_container_width=True, on_click=clear_link, help="Kosongkan kolom tautan")

if st.session_state.clipboard_message:
    st.caption(st.session_state.clipboard_message)

quality = st.selectbox(
    "Resolusi maksimum",
    options=list(QUALITY_PROFILES),
    index=1,
    format_func=lambda key: QUALITY_PROFILES[key]["label"],
    help="Aplikasi memilih format tertinggi yang sesuai batas ini. Resolusi 8K60 hanya tersedia bila video sumber menyediakannya.",
)

check_col, _ = st.columns([1.5, 3])
with check_col:
    check_video = st.button("Periksa video", type="primary", use_container_width=True)

if check_video:
    try:
        url = validate_youtube_url(st.session_state.video_url)
        with st.spinner("Memeriksa video dan format yang tersedia…"):
            st.session_state.video_info = get_video_info(url)
        st.session_state.clipboard_message = ""
    except Exception as exc:
        st.session_state.video_info = None
        st.error(str(exc)[:500])

info = st.session_state.video_info
if info:
    st.divider()
    st.subheader(info.get("title") or "Video YouTube")
    details = []
    if info.get("uploader") or info.get("channel"):
        details.append(str(info.get("uploader") or info.get("channel")))
    if info.get("duration") is not None:
        seconds = int(info["duration"])
        details.append(f"Durasi {seconds // 60}:{seconds % 60:02d}")
    if details:
        st.caption(" · ".join(details))

    st.markdown("**Resolusi sumber yang terdeteksi**")
    formats = info.get("display_formats") or []
    if formats:
        st.caption("  ·  ".join(formats))
    else:
        st.caption("Format akan dipilih saat unduhan dimulai.")

    if st.button("Mulai unduh", type="primary", use_container_width=True):
        try:
            url = validate_youtube_url(st.session_state.video_url)
            with st.status("Menyiapkan unduhan…", expanded=True) as status_box:
                final_file = download_video(url, quality)
                status_box.update(label="Unduhan selesai.", state="complete", expanded=False)
            st.session_state.last_download_path = str(final_file)
        except Exception as exc:
            status_box.update(label="Unduhan gagal.", state="error", expanded=True)
            message = str(exc).strip()[:500] or "Terjadi kesalahan saat mengunduh."
            if "ffmpeg" in message.lower():
                message += " Pastikan FFmpeg terpasang."
            st.error(message)

if st.session_state.last_download_path:
    last_file = Path(st.session_state.last_download_path)
    if last_file.is_file():
        st.success("Unduhan tersimpan: " + last_file.name)
        st.caption(str(last_file))
        if os.name == "nt" and st.button("Buka folder unduhan"):
            os.startfile(str(DOWNLOAD_DIR))

st.markdown(
    '<div class="local-note">Aplikasi berjalan lokal. Gunakan hanya konten yang kamu miliki atau berhak unduh; file tersimpan di folder downloads.</div>',
    unsafe_allow_html=True,
)


