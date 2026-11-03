# Behind The Headline (BTH) - Web Prototype & Ingestion System

Sistem Pencarian dan Analisis Komparasi Berita Berbasis Kata Kunci dengan *Artificial Intelligence* (AI).

> Proyek Mata Kuliah: **Manajemen Proyek TI (ManPro)**  
> Program Studi Teknologi Informasi, Universitas Muhammadiyah Yogyakarta (UMY)  
> Kelompok: **Tongkosor**

---

## 🚀 Cara Menjalankan Aplikasi

Pastikan Python (3.10+) sudah terpasang, lalu jalankan di terminal:
```bash
python server.py
```
Aplikasi akan otomatis menyajikan prototype di browser pada alamat `http://localhost:8000`.

Untuk menguji seluruh fungsionalitas REST API & Ingestion:
```bash
python test_backend.py
```

---

## 📁 Struktur Direktori Proyek

```
Project/
├── backend/
│   ├── ingestion/
│   │   ├── indo_news_api.py       # Sumber 1: Berita Indo API & api-berita-indonesia
│   │   ├── google_news_rss.py     # Sumber 2: Google News RSS (dengan redirect resolver)
│   │   ├── global_news_api.py     # Sumber 3: NewsAPI, Currents, MediaStack
│   │   ├── media_rss.py           # Sumber 4: RSS Resmi CNN, CNBC, Tempo
│   │   └── aggregator.py          # Unified Ingestion Multi-Source
│   ├── scraper/
│   │   ├── user_agents.py         # Rotasi User-Agent & Anti-Block Header
│   │   └── full_text_extractor.py # Scraping Teks Penuh & Pembersih Boilerplate
│   ├── ai_engine/
│   │   ├── base.py                # Interface BaseAIEngine
│   │   ├── prototype_nlp.py       # Mesin AI Prototype (Ringkasan & Matriks Komparasi)
│   │   └── adapter_guide.py       # Template integrasi AI untuk Raja Zhafar
│   ├── config.py                  # Konfigurasi Server & Kunci API
│   └── data_store.py              # In-memory store & dataset fallback realistis
├── prototype/                     # Antarmuka Web (Figma Style)
│   ├── index.html                 # Beranda & Grid Berita Terkini
│   ├── hasil.html                 # Hasil Pencarian, AI Summary, & Tabel Komparasi
│   ├── detail.html                # Teks Lengkap Artikel, AI Summary, & Liputan Pembanding
│   ├── style.css                  # Desain CSS Figma (Navy, Hero, Responsif)
│   └── script.js                  # Kontroler Dinamis Terhubung ke REST API
├── files (1)/                     # Salinan sinkron aset web
├── server.py                      # Flask Fullstack Server (Web UI + REST API)
├── test_backend.py                # Suite Uji Otomatis Sistem
├── LAPORAN_FITUR_DAN_PANDUAN.md   # Laporan lengkap fitur & panduan kelanjutan tim
├── PANDUAN_PENGEMBANGAN.md        # Dokumen rancangan ManPro
└── README.md                      # Dokumentasi ringkas proyek
```

---

## 👥 Tim Pengembang (7 Anggota)

1. **Raja Zhafar Akbar Rangkuty** - *AI Training & Modeling*
2. **Narendra Nabil Putra** - *Backend & API Development*
3. **Maul** - *Backend & API Development*
4. **Zidan** - *Server & DevOps*
5. **Faiz** - *Server & DevOps*
6. **Radiva Septiana Marcelita (Dipa)** - *UI/UX & Frontend Development*
7. **Andhika Nurjamil (Dhika)** - *UI/UX & Frontend Development*

---

*Lihat [LAPORAN_FITUR_DAN_PANDUAN.md](LAPORAN_FITUR_DAN_PANDUAN.md) untuk detail fitur lengkap dan panduan integrasi model AI.*
# ManPro
