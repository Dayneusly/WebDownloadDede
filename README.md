# WebDownloadDede

Aplikasi Streamlit untuk mengunduh video yang memang boleh disimpan, dengan pilihan kualitas hingga 4320p (8K) dan maksimal 60 fps bila tersedia dari sumber. Aplikasi Flask lokal lama masih tersedia melalui `start_flask.bat`.

## Menjalankan di Windows

1. Pastikan Python 3.10–3.14 sudah terpasang dan tersedia di PATH.
2. Jalankan start.bat. Skrip membuat virtual environment, memasang dependensi, lalu membuka Streamlit di http://127.0.0.1:8501.
3. Tempel URL dengan Ctrl+V, tombol Tempel, atau menu Tempel pada ponsel; tombol Hapus mengosongkan tautan.
4. Tekan Periksa video, pilih resolusi, lalu Mulai unduh.
5. File disimpan di folder downloads. Tekan Ctrl+C di jendela terminal untuk menghentikan server.

FFmpeg digunakan untuk menggabungkan stream video dan audio, dan Deno disarankan untuk dukungan ekstraksi YouTube penuh. Keduanya sudah dipasang/tersedia pada komputer yang dipakai membuat proyek ini; jika instalasi baru, lihat panduan Deno dan halaman Windows FFmpeg di bawah.

## Resolusi dan format

Pilihan 4320p meminta video setinggi maksimum 4320 baris (8K) dan sampai 60 fps. Hasil 4320p60 hanya mungkin jika video sumber memang menyediakan format itu. Bila tidak tersedia, aplikasi memilih format yang lebih rendah di dalam batas resolusi yang dipilih.

Stream video dan audio digabung tanpa encode ulang ke file MKV untuk menjaga kualitas codec sumber.

## Deploy ke Streamlit Community Cloud

Repo ini sudah memiliki dependensi cloud di `requirements.txt` dan `packages.txt`. Untuk menerbitkannya:

1. Hubungkan akun GitHub ke [Streamlit Community Cloud](https://share.streamlit.io/).
2. Buat app dari repo `Dayneusly/WebDownloadDede`, branch `main`, entrypoint `streamlit_app.py`.
3. Setelah proses deploy berhasil, ubah akses app menjadi **Public** bila ingin siapa pun yang memiliki URL dapat membukanya.

Repo GitHub ini publik, jadi kode sumber dan riwayat commit dapat dilihat siapa saja. App publik: https://webdownloaddede.streamlit.app/. Jangan mengunggah secret atau token ke repo.

### Batas hosting gratis

Aplikasi tidak lagi memasang batas ukuran 150 MB. File diunduh lewat browser ke perangkat pengunjung dan disimpan sementara di server. Kapasitas sebenarnya tetap mengikuti batas memori, CPU, dan penyimpanan Streamlit Community Cloud yang dapat berubah; file 4K/8K besar masih mungkin gagal jika melebihi resource yang tersedia. Lihat [batas resource Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-resources-and-limits). Untuk unduhan besar dan stabil, jalankan aplikasi lokal atau gunakan hosting/VPS dengan kapasitas yang sesuai.

Jika unduhan menampilkan **HTTP 403**, server YouTube menolak permintaan stream. Ini bukan karena ponsel; aplikasi memproses video dari server cloud. Coba resolusi lebih rendah atau gunakan fitur unduh resmi YouTube. Aplikasi tidak menggunakan login/cookies dan tidak melewati pembatasan akses. [Panduan yt-dlp tentang PO Token](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) menjelaskan bahwa perubahan pemeriksaan YouTube dapat menyebabkan 403 pada format tertentu.

## Catatan penggunaan

Gunakan hanya video yang Anda unggah sendiri atau yang memang berhak Anda unduh. Aplikasi tidak mengelola login/cookies, tidak mengakses video privat, dan tidak melewati DRM atau pembatasan akses. Ikuti [Ketentuan Layanan YouTube](https://www.youtube.com/t/terms).

Referensi: [Streamlit docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [panduan pemasangan Deno](https://docs.deno.com/runtime/getting_started/installation/), [unduhan FFmpeg](https://ffmpeg.org/download.html).
