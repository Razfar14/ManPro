# Panduan Pengembangan Proyek: Behind The Headline (BTH)

**Mata Kuliah:** Manajemen Proyek TI (ManPro)  
**Institusi:** Program Studi Teknologi Informasi, Universitas Muhammadiyah Yogyakarta (UMY)  
**Kelompok:** Tongkosor  

---

## 1. Ringkasan Eksekutif Proyek

### 1.1 Judul Proyek
> **Behind The Headline**: Sistem Pencarian dan Analisis Berita Berbasis Kata Kunci dengan *Artificial Intelligence* (AI).

### 1.2 Masalah yang Diselesaikan
Arus informasi di media daring (CNN Indonesia, CNBC Indonesia, Tempo, Kompas, dll.) sangat cepat. Seringkali beberapa portal menerbitkan berita tentang peristiwa yang sama dengan judul yang mirip atau sensasional, namun menyajikan:
- Sudut pandang (*framing*) yang berlawanan,
- Pilihan narasumber yang berbeda,
- Data angka atau statistik yang tidak seragam,
- Detail kronologi yang tidak lengkap.

Hal ini membingungkan masyarakat mengenai validitas dan gambaran utuh dari suatu peristiwa.

### 1.3 Solusi Sistem
Sebuah platform cerdas berbasis NLP (*Natural Language Processing*) yang:
1. Memproses kata kunci atau topik pencarian,
2. Mengelompokkan (*clustering*) artikel serupa secara otomatis,
3. Menghasilkan ringkasan intisari eksekutif (*AI Executive Summary*),
4. Menyajikan **Matriks Komparasi Antarmedia** (menjajarkan perbedaan judul, narasumber, sudut pandang, dan data statistik),
5. Menyediakan visualisasi radar bias dan penelusuran kutipan narasumber.

### 1.4 Batasan Sistem (Scope Boundaries)
- **In Scope:**
  - Pengambilan artikel dari portal berita terbuka (CNN, CNBC, Tempo, Kompas) via scraping/API.
  - Model NLP untuk clustering topik, perangkuman, dan komparasi matriks fakta.
  - Antarmuka web responsif dan interaktif.
- **Out of Scope:**
  - **Bukan penentu hoaks mutlak:** AI bertindak sebagai pembanding dan perangkum fakta, bukan hakim yang memvonis berita "benar/hoaks" tanpa parameter pembanding objektif.
  - Sistem tidak mengubah atau memodifikasi redaksi tulisan penerbit asli.
  - Aplikasi mobile (fokus semester ini adalah sistem web).

---

## 2. Cara Menjalankan Prototype Web

Prototype web interaktif telah disiapkan di folder `prototype/` dengan antarmuka modern (Tailwind CSS, Lucide Icons, Chart.js) dan dataset realistis.

### Cara 1: Menggunakan Python Web Server (Direkomendasikan)
Di terminal PowerShell pada folder root project:
```powershell
python server.py
```
*Server otomatis menyajikan aplikasi di `http://localhost:8000` dan membuka browser default.*

### Cara 2: Langsung Buka File HTML (Tanpa Server)
Buka File Explorer, masuk ke folder `prototype/`, lalu klik dua kali file:
```
prototype/index.html
```

---

## 3. Fitur Utama yang Sudah Disimulasikan dalam Prototype

| No | Fitur | Penjelasan & Nilai Guna |
|:---|:---|:---|
| 1 | **Pencarian Isu & Autocomplete** | Pengguna dapat mengetik kata kunci atau memilih isu terkini (*PPN 12%*, *Banjir Jakarta*, *Subsidi EV*). |
| 2 | **Executive AI Summary** | Ringkasan intisari cepat, fakta yang disepakati (*consensus*), dan titik friksi (*divergence*). |
| 3 | **Matriks Komparasi Antarmedia** | Tabel perbandingan langsung: Nuansa Headline, Sudut Pandang, Narasumber, dan Data Statistik antarmedia. |
| 4 | **Uji Kutipan Narasumber** | Membandingkan bagaimana figur yang sama (misal Menkeu atau Ekonom) dikutip oleh redaksi yang berbeda. |
| 5 | **Radar Sudut Pandang (Bias)** | Visualisasi Chart.js 5 dimensi: Regulasi, Publik, Pasar Modal, Kritisisme, dan Kelengkapan Konteks. |
| 6 | **Lab Simulasi Analisis AI** | Fitur sandbox interaktif untuk menguji query kata kunci baru secara instan. |
| 7 | **Blueprint Tim Interaktif** | Modal panduan teknis yang merangkum tugas 7 anggota dan kontrak REST API. |

---

## 4. Rincian Pembagian Tugas & Roadmap untuk 7 Anggota Tim

```
                                  [ ARSITEKTUR TIM ]
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
 [ AI & Modeling ]               [ Backend & API ]                 [ Server & DevOps ]
  Raja Zhafar                     Maul & Narendra                   Zidan & Faiz
        |                                 |                                 |
        +---------------------------------+---------------------------------+
                                          |
                                 [ UI/UX & Frontend ]
                                     Dhika & Dipa
```

### 4.1 Divisi AI Training & Modeling
**Anggota:** Raja Zhafar Akbar Rangkuty  
**Tanggung Jawab:**
1. **Validasi 50 Berita Sampel (PoC):** Mengumpulkan 50 artikel sampel dari 4 portal untuk menguji akurasi ekstraksi sebelum integrasi skala penuh.
2. **Text Preprocessing Pipeline:** Pembersihan teks (menghilangkan boilerplate redaksi seperti *"Baca Juga"* atau copyright footer), tokenisasi, dan stopword removal bahasa Indonesia.
3. **Model Clustering & Topic Modeling:** Menggunakan *IndoBERT-embedding* atau *Sentence-Transformers* (`sentence-transformers/all-MiniLM-L6-v2`) untuk mengelompokkan artikel dengan *Cosine Similarity* atau *HDBSCAN*.
4. **Information & Quote Extraction:** Menggunakan NER (*Named Entity Recognition*) untuk mengekstrak entitas Orang (*Person*), Organisasi (*Organization*), dan angka/persentase.
5. **Comparative & Summarization Engine:** Merancang prompt engineering terstruktur (menggunakan Google Gemini API atau model T5 Indo) untuk menghasilkan output JSON berformat matriks komparasi.

### 4.2 Divisi Backend & API Development
**Anggota:** Maul & Narendra Nabil Putra  
**Tanggung Jawab:**
1. **REST API Framework:** Membangun backend dengan **FastAPI** (Python) atau Flask.
2. **Modul Web Scraping:** Menulis crawler artikel dengan `BeautifulSoup4` atau `Playwright` untuk mengambil berita dari RSS feed / portal CNN, CNBC, Tempo, dan Kompas.
3. **Database Schema:** Merancang tabel PostgreSQL / SQLite untuk menyimpan:
   - `articles` (id, title, url, publisher, published_at, raw_text, clean_text)
   - `clusters` (id, cluster_name, created_at)
   - `comparisons` (id, cluster_id, consensus_json, divergence_json, matrix_json)
4. **Implementasi Endpoints:**
   - `GET /api/v1/search?q={query}` : Mencari artikel atau klaster yang sudah ada.
   - `POST /api/v1/scrape/trigger` : Memicu scraper untuk kata kunci tertentu.
   - `POST /api/v1/analyze/cluster` : Menjalankan pipeline AI Raja pada klaster berita.
5. **Caching & Asynchronous Processing:** Memakai Celery / Redis agar scraping dan inference AI tidak membekukan (*blocking*) response web.

### 4.3 Divisi Server & DevOps
**Anggota:** Zidan & Faiz  
**Tanggung Jawab:**
1. **Containerization (Docker):**
   - Menulis `Dockerfile` untuk Frontend, Backend FastAPI, dan Scraper.
   - Membuat `docker-compose.yml` yang menghubungkan container Backend, Database PostgreSQL, Redis, dan Nginx.
2. **Pengadaan & Setup Server:** Menyiapkan VPS Linux (Ubuntu 22.04 LTS), mengatur firewall UFW, SSH key access.
3. **Mitigasi Pemblokiran Scraping:** Konfigurasi rotasi *User-Agent*, jeda waktu per request (*rate-limiting*), dan integrasi proxy jika diperlukan agar tidak terkena ban IP dari portal berita.
4. **Reverse Proxy & Domain:** Konfigurasi Nginx sebagai reverse proxy dengan sertifikat SSL gratis Let's Encrypt (HTTPS).
5. **CI/CD Pipeline:** Menyiapkan GitHub Actions untuk memeriksa linting dan uji integrasi otomatis saat melakukan push ke repository.

### 4.4 Divisi UI/UX & Frontend Development
**Anggota:** Radiva Septiana Marcelita (Dipa) & Andhika Nurjamil (Dhika)  
**Tanggung Jawab:**
1. **Desain Figma:** Menyempurnakan wireframe dan prototipe desain di Figma sesuai feedback dosen dan tim.
2. **Implementasi Komponen Web:** Mengembangkan komponen UI modern (bisa menggunakan React/Next.js/Vite atau menyempurnakan struktur vanilla Tailwind dari prototype ini).
3. **Visualisasi Data Interaktif:** Mengintegrasikan Chart.js / ApexCharts untuk radar visualisasi sudut pandang dan tingkat keselarasan informasi.
4. **Highlighting Perbedaan:** Menerapkan kode warna visual (Hijau untuk fakta konsensus, Amber/Kuning untuk divergensi, Merah untuk perbedaan kontradiktif).
5. **Aksesibilitas & Mode Gelap:** Menjaga kontras teks, tipografi terbaca (*Plus Jakarta Sans*), dan kenyamanan membaca berita panjang (*readability*).

---

## 5. Kontrak Spesifikasi REST API

Backend Maul & Narendra harus menyediakan response format JSON yang sesuai dengan konsumsi Frontend Dhika & Dipa:

### Endpoint: `GET /api/v1/search`
**Query Parameters:** `q=kenaikan+ppn&media=all&limit=10`  
**Sample JSON Response:**
```json
{
  "status": "success",
  "query": "kenaikan ppn",
  "totalClusters": 1,
  "clusters": [
    {
      "clusterId": "cl-ppn-12",
      "title": "Polemik Kenaikan Tarif PPN Menjadi 12% Per 1 Januari",
      "category": "Ekonomi",
      "articleCount": 4,
      "sources": ["CNN Indonesia", "CNBC Indonesia", "Tempo.co", "Kompas.id"],
      "lastUpdated": "2026-10-28T09:15:00Z"
    }
  ]
}
```

### Endpoint: `POST /api/v1/analyze/cluster`
**Request Body:**
```json
{
  "clusterId": "cl-ppn-12"
}
```
**Sample JSON Response:**
```json
{
  "status": "success",
  "clusterId": "cl-ppn-12",
  "executiveSummary": "Keempat media sepakat bahwa dasar hukum penyesuaian tarif PPN adalah UU HPP...",
  "consensusFacts": [
    "Pemerintah berencana menaikkan tarif PPN dari 11% menjadi 12% sesuai amanat UU No. 7/2021.",
    "Kebutuhan pangan pokok tetap berstatus bebas PPN."
  ],
  "divergences": [
    {
      "aspect": "Fokus Sudut Pandang",
      "cnn": "Kepatuhan regulasi dan perlindungan sembako",
      "cnbc": "Dampak terhadap inflasi dan saham konsumer",
      "tempo": "Beban kelas menengah dan penolakan buruh",
      "kompas": "Ruang fiskal vs perlindungan konsumsi"
    }
  ],
  "quotes": [
    {
      "speaker": "Sri Mulyani Indrawati",
      "role": "Menteri Keuangan RI",
      "cnn": "Ini adalah mandat UU yang sudah disepakati bersama parlemen...",
      "tempo": "Menkeu menyatakan tidak ada alasan membatalkan amanat UU..."
    }
  ]
}
```

---

## 6. Milestone & Tahapan Kerja (WBS 4 Tahap)

| Tahap | Aktivitas Utama | Penanggung Jawab | Output |
|:---|:---|:---|:---|
| **Tahap 1: Pengumpulan Data** | Scraping 50 artikel berita sampel, pembersihan data teks mentah | Raja, Maul, Narendra | Dataset JSON 50 artikel terindeks |
| **Tahap 2: AI & NLP PoC** | Uji akurasi clustering dan prompt komparasi fakta dengan model AI | Raja | Script modul NLP teruji & formula prompt |
| **Tahap 3: Sistem & Web** | Pembuatan REST API, UI pencarian, tabel matriks komparasi | Maul, Narendra, Dhika, Dipa | Integrasi API dengan antarmuka web |
| **Tahap 4: Testing & Deploy** | Setup VPS, containerization Docker, QA dan simulasi beban | Zidan, Faiz | Sistem live di server dengan domain/IP publik |

---

## 7. Kesimpulan & Langkah Selanjutnya

Dengan tersedianya web prototype ini:
1. **Dosen & Penguji:** Dapat langsung melihat visualisasi nyata dari apa yang ditargetkan kelompok Tongkosor tanpa menunggu kode backend selesai.
2. **Tim Pengembang (Raja dkk):** Memiliki patokan visual, skema input-output data, dan pembagian tugas yang terukur sehingga pengembangan dapat langsung dieksekusi secara paralel.
