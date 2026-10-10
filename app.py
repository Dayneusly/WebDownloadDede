from __future__ import annotations

import os
import shutil
import threading
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request, send_file
from yt_dlp import YoutubeDL

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="youtube-download")
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()

QUALITY_PROFILES = {
    "4320": {
        "label": "4320p · 8K (maks. 60 fps)",
        "format": "bestvideo[height<=4320][fps<=60]+bestaudio/best[height<=4320][fps<=60]",
    },
    "2160": {
        "label": "2160p · 4K (maks. 60 fps)",
        "format": "bestvideo[height<=2160][fps<=60]+bestaudio/best[height<=2160][fps<=60]",
    },
    "1440": {
        "label": "1440p · 2K (maks. 60 fps)",
        "format": "bestvideo[height<=1440][fps<=60]+bestaudio/best[height<=1440][fps<=60]",
    },
    "1080": {
        "label": "1080p · Full HD (maks. 60 fps)",
        "format": "bestvideo[height<=1080][fps<=60]+bestaudio/best[height<=1080][fps<=60]",
    },
    "720": {
        "label": "720p · HD (maks. 60 fps)",
        "format": "bestvideo[height<=720][fps<=60]+bestaudio/best[height<=720][fps<=60]",
    },
    "best": {
        "label": "Tertinggi yang tersedia",
        "format": "bestvideo[fps<=60]+bestaudio/best[fps<=60]",
    },
}


def validate_youtube_url(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Masukkan tautan video YouTube.")
    url = value.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    is_youtube = (
        host == "youtube.com"
        or host.endswith(".youtube.com")
        or host == "youtu.be"
    )
    if parsed.scheme != "https" or not is_youtube:
        raise ValueError("Gunakan tautan HTTPS dari youtube.com atau youtu.be.")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Tautan video belum lengkap.")
    return url


def base_ydl_options() -> dict:
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


def format_summary(info: dict) -> list[dict]:
    rows: dict[tuple[int, int], dict] = {}
    for item in info.get("formats") or []:
        height = item.get("height")
        if not height or item.get("vcodec") == "none":
            continue
        fps = int(item.get("fps") or 0)
        key = (int(height), fps)
        row = {
            "height": int(height),
            "fps": fps,
            "ext": str(item.get("ext") or "").upper(),
        }
        if key not in rows:
            rows[key] = row
    return sorted(rows.values(), key=lambda item: (item["height"], item["fps"]), reverse=True)[:18]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/info")
def video_info():
    try:
        url = validate_youtube_url(request.args.get("url"))
        options = base_ydl_options()
        options.update({"skip_download": True, "extract_flat": False})
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Informasi video tidak ditemukan.")
        if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
            raise ValueError("Video siaran langsung atau terjadwal tidak didukung.")
        duration = info.get("duration")
        return jsonify({
            "id": info.get("id"),
            "title": info.get("title") or "Video YouTube",
            "channel": info.get("uploader") or info.get("channel") or "",
            "duration": duration,
            "formats": format_summary(info),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)[:500]}), 400


def update_job(job_id: str, **values) -> None:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is not None:
            job.update(values)


def download_video(job_id: str, url: str, quality: str) -> None:
    profile = QUALITY_PROFILES[quality]
    update_job(job_id, state="downloading", message="Menghubungkan ke YouTube…")

    def progress_hook(data: dict) -> None:
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            percent = round((data.get("downloaded_bytes", 0) / total) * 100, 1) if total else 0
            update_job(
                job_id,
                state="downloading",
                message="Mengunduh video…",
                percent=min(percent, 99.9),
                speed=data.get("_speed_str") or "",
                eta=data.get("_eta_str") or "",
            )
        elif data.get("status") == "finished":
            update_job(job_id, state="processing", message="Menggabungkan video dan audio…", percent=100)

    try:
        options = base_ydl_options()
        options.update({
            "format": profile["format"],
            "outtmpl": str(DOWNLOAD_DIR / "%(title).180B [%(id)s].%(ext)s"),
            "merge_output_format": "mkv",
            "progress_hooks": [progress_hook],
        })
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            raise RuntimeError("Unduhan tidak menghasilkan file.")

        video_id = str(info.get("id") or "")
        candidates = [
            path for path in DOWNLOAD_DIR.iterdir()
            if path.is_file()
            and f"[{video_id}]" in path.stem
            and not path.name.endswith((".part", ".ytdl"))
        ]
        if not candidates:
            prepared = Path(ydl.prepare_filename(info))
            if prepared.is_file():
                candidates = [prepared]
            else:
                for extension in (".mkv", ".mp4", ".webm"):
                    merged = prepared.with_suffix(extension)
                    if merged.is_file():
                        candidates = [merged]
                        break
        if not candidates:
            raise RuntimeError("File selesai diunduh tetapi tidak ditemukan di folder downloads.")

        final_file = max(candidates, key=lambda path: path.stat().st_mtime)
        update_job(
            job_id,
            state="done",
            message="Unduhan selesai.",
            percent=100,
            filename=final_file.name,
            size=final_file.stat().st_size,
        )
    except Exception as exc:
        detail = str(exc).strip()[:500] or "Terjadi kesalahan saat mengunduh."
        if "ffmpeg" in detail.lower():
            detail += " Pastikan FFmpeg sudah terpasang dan tersedia di PATH untuk menggabungkan format resolusi tinggi."
        update_job(job_id, state="error", message=detail)


@app.post("/api/download")
def start_download():
    payload = request.get_json(silent=True) or {}
    try:
        url = validate_youtube_url(payload.get("url"))
        quality = payload.get("quality", "2160")
        if quality not in QUALITY_PROFILES:
            raise ValueError("Pilihan resolusi tidak dikenal.")
        job_id = uuid.uuid4().hex
        with jobs_lock:
            jobs[job_id] = {
                "state": "queued",
                "message": "Menunggu giliran unduh…",
                "percent": 0,
                "quality": QUALITY_PROFILES[quality]["label"],
            }
        executor.submit(download_video, job_id, url, quality)
        return jsonify({"job_id": job_id}), 202
    except Exception as exc:
        return jsonify({"error": str(exc)[:500]}), 400


@app.get("/api/jobs/<job_id>")
def job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            return jsonify({"error": "Tugas unduhan tidak ditemukan."}), 404
        return jsonify(job.copy())


@app.get("/api/jobs/<job_id>/file")
def get_download(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        filename = job.get("filename") if job and job.get("state") == "done" else None
    if not filename:
        return jsonify({"error": "File belum siap diunduh."}), 404

    path = (DOWNLOAD_DIR / filename).resolve()
    if path.parent != DOWNLOAD_DIR.resolve() or not path.is_file():
        return jsonify({"error": "File tidak ditemukan."}), 404
    return send_file(path, as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    print("WebDownloadDede aktif di http://127.0.0.1:5000")
    print(f"Folder hasil unduhan: {DOWNLOAD_DIR}")
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)





