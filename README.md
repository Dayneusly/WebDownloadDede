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

Repo GitHub saat ini privat. Streamlit meminta izin GitHub tambahan untuk membaca repo privat; bila tidak ingin memberikan izin itu, repo harus dibuat publik dan kode sumbernya akan terlihat. Jangan mengunggah secret atau token ke repo.

### Batas hosting gratis

Streamlit Community Cloud memiliki sumber daya dan penyimpanan sementara yang terbatas. File video cloud dibatasi hingga 150 MB dan diunduh lewat browser ke perangkat pengunjung; hasil 4K/8K yang lebih besar perlu dijalankan lokal atau di hosting berbayar. File di hosting gratis bersifat sementara dan bisa hilang saat app dimulai ulang. Unduhan besar juga memakai memori server.

## Catatan penggunaan

Gunakan hanya video yang Anda unggah sendiri atau yang memang berhak Anda unduh. Aplikasi tidak mengelola login/cookies, tidak mengakses video privat, dan tidak melewati DRM atau pembatasan akses. Ikuti [Ketentuan Layanan YouTube](https://www.youtube.com/t/terms).

Referensi: [Streamlit docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [panduan pemasangan Deno](https://docs.deno.com/runtime/getting_started/installation/), [unduhan FFmpeg](https://ffmpeg.org/download.html).
