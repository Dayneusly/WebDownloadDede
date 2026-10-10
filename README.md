# WebDownloadDede

Pengunduh video YouTube lokal dengan UI Streamlit dan pilihan kualitas hingga 4320p (8K), maksimal 60 fps bila tersedia pada sumber. Aplikasi juga mempertahankan versi Flask lama; untuk memakainya jalankan start_flask.bat.

## Menjalankan di Windows

1. Pastikan Python 3.10–3.14 sudah terpasang dan tersedia di PATH.
2. Jalankan start.bat. Skrip membuat virtual environment, memasang dependensi, lalu membuka Streamlit di http://127.0.0.1:8501.
3. Tempel URL dengan Ctrl+V atau tombol Tempel; tombol Hapus mengosongkan tautan.
4. Tekan Periksa video, pilih resolusi, lalu Mulai unduh.
5. File disimpan di folder downloads. Tekan Ctrl+C di jendela terminal untuk menghentikan server.

FFmpeg digunakan untuk menggabungkan stream video dan audio, dan Deno disarankan untuk dukungan ekstraksi YouTube penuh. Keduanya sudah dipasang/tersedia pada komputer yang dipakai membuat proyek ini; jika instalasi baru, lihat panduan Deno dan halaman Windows FFmpeg di bawah.

## Resolusi dan format

Pilihan 4320p meminta video setinggi maksimum 4320 baris (8K) dan sampai 60 fps. Hasil 4320p60 hanya mungkin jika video sumber memang menyediakan format itu. Bila tidak tersedia, aplikasi memilih format yang lebih rendah di dalam batas resolusi yang dipilih.

Stream video dan audio digabung tanpa encode ulang ke file MKV untuk menjaga kualitas codec sumber.

## GitHub dan Streamlit Community Cloud

Repositori ini menyimpan kode sumber. Aplikasi saat ini dikonfigurasi untuk berjalan lokal di Windows dan mengunduh file ke komputer yang menjalankannya. Mengunggah kode ke GitHub tidak otomatis membuat aplikasi berjalan di internet. Deploy cloud memerlukan konfigurasi tambahan, termasuk FFmpeg dan penyimpanan file pada server.

## Catatan penggunaan

Gunakan hanya video yang Anda unggah sendiri atau yang memang berhak Anda unduh. Aplikasi tidak mengelola login/cookies, tidak mengakses video privat, dan tidak melewati DRM atau pembatasan akses. Ikuti [Ketentuan Layanan YouTube](https://www.youtube.com/t/terms).

Referensi: [Streamlit docs](https://docs.streamlit.io/get-started/installation/command-line), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [panduan pemasangan Deno](https://docs.deno.com/runtime/getting_started/installation/), [unduhan FFmpeg](https://ffmpeg.org/download.html).
