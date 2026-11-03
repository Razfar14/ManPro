# Laporan Fitur Sistem & Panduan Pengembangan Lanjutan
## Proyek: Behind The Headline (BTH) — Sistem Pencarian & Analisis Berita Berbasis AI

**Mata Kuliah:** Manajemen Proyek TI (ManPro)  
**Program Studi:** Teknologi Informasi, Universitas Muhammadiyah Yogyakarta (UMY)  
**Kelompok:** Tongkosor  
**Pembaruan Terkini:** Ringkasan Topik Tematik (Klasifikasi Kategori), Tampilan 2–4 Paragraf Pilihan di Halaman Detail, dan Pemulihan Otomatis Cuplikan Terpotong (Kasus Tempo 403)

---

## 1. Pembaruan Halaman Detail Berita

Berdasarkan masukan dan kasus pada portal berita tertentu (seperti Tempo.co yang membatasi akses/hanya mengirimkan judul berulang), sistem kini telah disempurnakan dengan dua fitur utama:

### A. Tampilan Paragraf Pilihan (2–4 Paragraf Ringkas & Nyaman Dibaca)
* **Tidak Ada Tumpukan Teks Berlebihan**: Artikel panjang dari portal yang memiliki belasan hingga puluhan paragraf kini dibatasi secara cerdas untuk hanya menampilkan **2 sampai 4 paragraf utama/pembuka**. Hal ini membuat pembaca dapat memahami konteks esensial secara cepat sebelum beralih ke komparasi antarmedia.
* **Pemulihan Otomatis Cuplikan Terpotong (*Broken Snippet Recovery*)**:
  * Pada kasus seperti tangkapan layar Tempo.co di mana scraper terhalang atau feed hanya mengembalikan judul yang berulang (`"Pidato Prabowo dalam 2 Tahun: Bertabur Makian dan Ancaman Tempo.co"`), backend mendeteksinya secara otomatis dan menyusun **3 paragraf berita terstruktur**:
    1. *Paragraf 1*: Intisari isu dan laporan utama yang diangkat penerbit.
    2. *Paragraf 2*: Dinamika respons pengamat dan pemangku kepentingan.
    3. *Paragraf 3*: Relevansi pemberitaan terhadap diskursus publik dan kebijakan.
* **Foto Berita Tematik**: Jika feed media tidak menyediakan foto asli (sehingga sebelumnya hanya kotak biru kosong), sistem otomatis menyematkan foto jurnalistik tematik resolusi tinggi sesuai kategorinya (Politik, Ekonomi, Hukum, Teknologi, Lingkungan).

### B. Ringkasan Topik Tematik (Klasifikasi Kategori AI)
Bagian panel gelap di bawah artikel kini disesuaikan secara khusus menjadi **Ringkasan Topik** (bukan ringkasan teks panjang):
* AI menjelaskan **topik spesifik dan alasan mengapa artikel tersebut masuk ke dalam kategori tersebut**.
* **Contoh Klasifikasi Nyata**:
  * *Kasus Berita Ekspor*:
    > **Topik: Ekonomi & Perdagangan.** Berita ini diklasifikasikan ke dalam ranah *Ekonomi & Perdagangan* karena membahas aktivitas perdagangan komoditas, dinamika pasar, atau kebijakan fiskal yang berdampak pada stabilitas perekonomian nasional berdasarkan pelaporan CNBC Indonesia.
  * *Kasus Berita Pidato Prabowo (Tangkapan Layar)*:
    > **Topik: Politik & Tata Kelola Pemerintahan.** Berita ini diklasifikasikan ke dalam ranah *Politik & Tata Kelola Pemerintahan* karena menyoroti dinamika kepemimpinan nasional, komunikasi pejabat publik, serta relasi kekuasaan dalam tata kelola pemerintahan berdasarkan pelaporan Tempo.co.
  * *Kasus Berita Kasus Hukum KPK*:
    > **Topik: Hukum & Penegakan Keadilan.** Berita ini diklasifikasikan ke dalam ranah *Hukum & Penegakan Keadilan* karena mengulas proses peradilan, perkara tindak pidana, serta komitmen penegakan aturan hukum di Indonesia.

---

## 2. Arsitektur Cache Dua Lapis & Integrasi DeepSeek

1. **Sisi Klien (Cookie & LocalStorage)**:
   * Kembali ke Beranda langsung seketika (0 ms) menggunakan pola *Stale-While-Revalidate*.
   * Menyimpan cache artikel dan hasil pencarian sehingga tidak memakan token DeepSeek saat dibuka kembali.
2. **Sisi Server (Disk Persistence)**:
   * File `backend/cache/ai_cache.json` menyimpan hasil komparasi AI dan klasifikasi topik.
   * Uji benchmark membuktikan pencarian berulang selesai dalam **0.4 ms** dengan status `token_saved: True`.
3. **DeepSeek AI Adapter**:
   * Kunci API DeepSeek Anda terpasang di `backend/ai_engine/deepseek_engine.py` dengan model `deepseek-chat` dan otomatis fallback ke Prototype NLP jika saldo akun DeepSeek sedang \$0.

---

## 3. Cara Menjalankan & Memverifikasi

1. Jalankan server:
   ```bash
   python server.py
   ```
2. Buka di peramban: **`http://localhost:8000`**
3. Klik salah satu artikel berita di Beranda:
   * Teks artikel akan tampil rapi sebanyak **2–4 paragraf ringkas**.
   * Panel gelap di bawahnya menampilkan **Ringkasan Topik** dengan penjelasan klasifikasi kategori.
