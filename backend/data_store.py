"""
Data Store & Cache Terpadu Behind The Headline
Menyimpan artikel terindeks, hasil scraping teks lengkap, serta menyediakan dataset fallback
realistis untuk simulasi offline / tahap pengujian tanpa ketergantungan internet.
"""

import time
from typing import Dict, List, Optional, Any
from backend.ingestion.base import ArticleItem

# Dataset realistis komprehensif untuk pengujian & fallback offline (50 berita PoC Raja & Tim)
CURATED_DATASET: List[Dict[str, Any]] = [
    # Topik 1: Kenaikan Tarif PPN 12%
    {
        "id": "art-ppn-cnn-01",
        "title": "Pemerintah Pastikan Tarif PPN 12 Persen Berlaku Mulai 1 Januari 2025 Sesuai UU HPP",
        "url": "https://www.cnnindonesia.com/ekonomi/20250101-ppn-12-persen-uu-hpp",
        "publisher": "CNN Indonesia",
        "category": "Ekonomi",
        "published_at": "2026-10-28T09:15:00Z",
        "snippet": "Menteri Keuangan menegaskan penyesuaian tarif PPN menjadi 12 persen merupakan amanat Undang-Undang Harmonisasi Peraturan Perpajakan (UU HPP) untuk memperkuat fondasi fiskal negara.",
        "image_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Tim Ekonomi CNN",
        "full_text": """Jakarta, CNN Indonesia -- Menteri Keuangan Sri Mulyani Indrawati menegaskan bahwa implementasi kenaikan tarif Pajak Pertambahan Nilai (PPN) dari 11 persen menjadi 12 persen pada 1 Januari 2025 merupakan pelaksanaan amanat Undang-Undang Nomor 7 Tahun 2021 tentang Harmonisasi Peraturan Perpajakan (UU HPP).

Pemerintah menargetkan penyesuaian ini mampu memberikan tambahan penerimaan negara sekitar Rp 70 triliun hingga Rp 80 triliun per tahun, yang akan dialokasikan kembali untuk belanja perlindungan sosial dan pembangunan infrastruktur dasar.

Menkeu menekankan bahwa barang kebutuhan pokok masyarakat (sembako), jasa kesehatan, jasa pendidikan, dan jasa transportasi umum tetap dikecualikan atau dibebaskan dari pungutan PPN guna melindungi kelompok masyarakat rentan dan miskin.

"Kita memerlukan fondasi penerimaan negara yang kokoh dan berkesinambungan untuk membiayai belanja negara, namun di saat yang sama instrumen bantalan sosial tetap diperkuat," ujar Menkeu di Gedung DPR RI."""
    },
    {
        "id": "art-ppn-cnbc-02",
        "title": "PPN 12% Membayang, Pengusaha Ritel Khawatirkan Dampak Pelemahan Daya Beli dan Inflasi",
        "url": "https://www.cnbcindonesia.com/market/20250101-ritel-ppn-12-daya-beli",
        "publisher": "CNBC Indonesia",
        "category": "Ekonomi",
        "published_at": "2026-10-28T10:30:00Z",
        "snippet": "Asosiasi Pengusaha Ritel Indonesia (Aprindo) memperkirakan kenaikan PPN 12% berpotensi menekan konsumsi domestik sebesar 1,2% serta menambah beban inflasi tahunan hingga 0,4%.",
        "image_url": "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Analis CNBC",
        "full_text": """Jakarta, CNBC Indonesia -- Rencana pemberlakuan tarif PPN 12% menuai kekhawatiran dari pelaku industri ritel dan pasar modal. Asosiasi Pengusaha Ritel Indonesia (Aprindo) memproyeksikan potensi koreksi indeks penjualan riil sebesar 1,2% pada kuartal pertama implementasi aturan baru tersebut.

Ketua Umum Aprindo, Roy Nicholas Mandey, menyampaikan bahwa tekanan biaya operasional yang meningkat seiring kenaikan tarif pajak berisiko diteruskan ke harga jual konsumen akhir. Hal ini dapat memicu efek berantai pada inflasi umum sekitar 0,3% hingga 0,5%.

Para pelaku pasar saham juga mencermati pergerakan saham-saham emiten sektor barang konsumsi (FMCG) yang berpotensi mengalami kontraksi margin laba bersih jika elastisitas permintaan masyarakat terhadap harga terbukti tinggi."""
    },
    {
        "id": "art-ppn-tempo-03",
        "title": "Kenaikan PPN 12%: Ekonom dan Serikat Buruh Soroti Tekanan Berat pada Kelas Menengah",
        "url": "https://www.tempo.co/bisnis/20250101-ppn-12-kelas-menengah-buruh",
        "publisher": "Tempo",
        "category": "Ekonomi",
        "published_at": "2026-10-28T11:45:00Z",
        "snippet": "Direktur Eksekutif Celios menyatakan kelas menengah yang tidak menerima bansos akan menjadi kelompok paling terpukul akibat penyesuaian tarif PPN di tengah tren pemutusan hubungan kerja.",
        "image_url": "https://images.unsplash.com/photo-1580519542036-c47de6196ba5?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Reporter Tempo",
        "full_text": """Jakarta, Tempo.co -- Kenaikan tarif PPN 12% mendapatkan sorotan tajam dari kalangan ekonom independen dan organisasi serikat buruh. Direktur Eksekutif Center of Economic and Law Studies (Celios), Bhima Yudhistira, menilai kebijakan ini tidak tepat waktu di tengah penurunan jumlah penduduk kelas menengah sebesar 9,4 juta orang dalam lima tahun terakhir.

Menurut kajian Celios, kenaikan PPN 12% dapat meningkatkan biaya hidup rata-rata keluarga urban sebesar 2,8% hingga 3,5%, sementara pendapatan riil cenderung stagnan. Di sisi lain, kelompok kelas menengah tidak memiliki jaring pengaman seperti bantuan sosial tunai (bansos) yang hanya menyasar desil terbawah.

Presiden Konfederasi Serikat Pekerja Indonesia (KSPI), Said Iqbal, mendesak pemerintah dan parlemen menunda implementasi kenaikan tarif hingga upah minimum riil mencatatkan pertumbuhan di atas laju inflasi riil."""
    },

    # Topik 2: Banjir Jakarta & Normalisasi Sungai Ciliwung
    {
        "id": "art-banjir-cnn-04",
        "title": "Pemprov DKI dan Kementerian PU Percepat Normalisasi Ciliwung Pasca Genangan",
        "url": "https://www.cnnindonesia.com/nasional/20260910-banjir-jakarta-normalisasi",
        "publisher": "CNN Indonesia",
        "category": "Lingkungan",
        "published_at": "2026-09-15T08:00:00Z",
        "snippet": "Pemerintah Provinsi DKI Jakarta mengalokasikan anggaran pembebasan lahan sebesar Rp 850 miliar untuk merampungkan sodetan dan normalisasi tanggul Sungai Ciliwung.",
        "image_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Biro Jakarta CNN",
        "full_text": """Jakarta, CNN Indonesia -- Pemprov DKI Jakarta bersama Kementerian Pekerjaan Umum bergerak cepat mempercepat proyek normalisasi Sungai Ciliwung sepanjang 17 kilometer yang sempat tertunda. Alokasi anggaran sebesar Rp 850 miliar disiapkan tahun anggaran ini untuk pembebasan lahan bantaran sungai.

Kepala Dinas Sumber Daya Air DKI menyatakan pengerjaan polder dan penguatan tanggul di kawasan rawan seperti Bidara Cina dan Kampung Melayu berhasil mengurangi durasi genangan dari 14 jam menjadi 4 jam pada curah hujan ekstrem pekan lalu."""
    },
    {
        "id": "art-banjir-cnbc-05",
        "title": "Kerugian Ekonomi Akibat Banjir Jakarta Capai Miliaran Rupiah, Logistik Terganggu",
        "url": "https://www.cnbcindonesia.com/news/20260910-kerugian-banjir-jakarta-logistik",
        "publisher": "CNBC Indonesia",
        "category": "Lingkungan",
        "published_at": "2026-09-15T09:20:00Z",
        "snippet": "Kamar Dagang dan Industri (Kadin) DKI menghitung estimasi kerugian perputaran barang dan jasa akibat genangan jalur logistik mencapai Rp 45 miliar per hari.",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Riset CNBC",
        "full_text": """Jakarta, CNBC Indonesia -- Genangan air di sejumlah titik arteri ibu kota membawa dampak langsung terhadap rantai pasok industri. Kadin DKI Jakarta mencatat keterlambatan distribusi armada logistik di kawasan pergudangan Jakarta Barat dan Utara memicu kerugian hingga puluhan miliar rupiah.

Pelaku usaha retail dan ekspor-impor mendorong kepastian percepatan proyek drainase makro terintegrasi agar kerentanan operasional tidak terulang setiap puncak musim hujan."""
    },
    {
        "id": "art-banjir-tempo-06",
        "title": "Tata Ruang Jakarta dan Krisis Resapan Air: Walhi Kritik Solusi Betonisasi Sungai",
        "url": "https://www.tempo.co/metro/20260910-banjir-jakarta-walhi-tata-ruang",
        "publisher": "Tempo",
        "category": "Lingkungan",
        "published_at": "2026-09-15T11:00:00Z",
        "snippet": "Wahana Lingkungan Hidup Indonesia (Walhi) menegaskan normalisasi dengan betonisasi tidak menyelesaikan akar masalah jika ruang terbuka hijau DKI tetap di bawah 10%.",
        "image_url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Investigasi Tempo",
        "full_text": """Jakarta, Tempo.co -- Penanganan banjir Jakarta dinilai belum menyentuh akar masalah tata kelola ruang dan krisis daerah resapan air hulu ke hilir. Manajer Kampanye Walhi Jakarta menyoroti proyek betonisasi dinding sungai yang mengabaikan restorasi ekosistem alami sempadan sungai.

Walhi mencatat luas Ruang Terbuka Hijau (RTH) Jakarta saat ini baru mencapai 9,8 persen, jauh dari mandat regulasi sebesar 30 persen. Tanpa moratorium alih fungsi lahan di kawasan Bogor-Puncak-Cianjur, debit air kiriman dipastikan akan selalu melebihi kapasitas drainase kota."""
    },

    # Topik 3: Pemilu & Pilkada Serentak (Politik)
    {
        "id": "art-pilkada-cnn-07",
        "title": "KPU Pastikan Logistik Surat Suara Pilkada Serentak Terdistribusi 98 Persen",
        "url": "https://www.cnnindonesia.com/nasional/20261012-kpu-logistik-pilkada",
        "publisher": "CNN Indonesia",
        "category": "Politik",
        "published_at": "2026-10-14T07:15:00Z",
        "snippet": "Komisi Pemilihan Umum memastikan seluruh logistik utama surat suara dan kotak suara telah mencapai KPUD di seluruh provinsi tepat waktu.",
        "image_url": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Biro Politik CNN",
        "full_text": """Jakarta, CNN Indonesia -- Komisi Pemilihan Umum (KPU) RI menyatakan kesiapan penyelenggaraan Pilkada Serentak di 545 daerah telah mencapai 98 persen. Distribusi surat suara dan kotak suara di wilayah terdepan, terluar, dan tertinggal (3T) mendapat prioritas pengiriman dengan pengawalan aparat TNI dan Polri."""
    },
    {
        "id": "art-pilkada-cnbc-08",
        "title": "Perputaran Uang Selama Kampanye Pilkada Diestimasi Sumbang 0,2% ke PDB Daerah",
        "url": "https://www.cnbcindonesia.com/market/20261012-ekonomi-pilkada-belanja-kampanye",
        "publisher": "CNBC Indonesia",
        "category": "Politik",
        "published_at": "2026-10-14T09:40:00Z",
        "snippet": "Sektor percetakan, transportasi, dan perhotelan di daerah mencatat lonjakan pendapatan signifikan menjelang pemungutan suara serentak.",
        "image_url": "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Analis Makro CNBC",
        "full_text": """Jakarta, CNBC Indonesia -- Gelaran Pilkada Serentak memberikan stimulus ekonomi jangka pendek bagi berbagai sektor industri di daerah. Lembaga riset ekonomi memproyeksikan belanja kampanye para kandidat dan operasional pengawasan pemilu mengalirkan likuiditas segar hingga puluhan triliun rupiah ke perputaran ekonomi lokal."""
    },
    {
        "id": "art-pilkada-tempo-09",
        "title": "Bawaslu Petakan 180 Kabupaten/Kota Rawan Politik Uang dan Netralitas ASN",
        "url": "https://www.tempo.co/nasional/20261012-bawaslu-indeks-kerawanan-pilkada",
        "publisher": "Tempo",
        "category": "Politik",
        "published_at": "2026-10-14T11:10:00Z",
        "snippet": "Indeks Kerawanan Pemilu (IKP) mencatat isu pelanggaran netralitas aparatur sipil negara dan penyalahgunaan wewenang petahana menjadi perhatian terbesar.",
        "image_url": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Tim Investigasi Tempo",
        "full_text": """Jakarta, Tempo.co -- Badan Pengawas Pemilihan Umum (Bawaslu) merilis peta Indeks Kerawanan Pemilu (IKP) menjelang pemungutan suara pilkada. Sebanyak 180 daerah dikategorikan memiliki tingkat kerawanan tinggi terkait mobilisasi birokrasi, netralitas ASN, dan distribusi bansos yang beririsan dengan elektoral kandidat petahana."""
    },

    # Topik 4: Transformasi AI & Regulasi Teknologi
    {
        "id": "art-ai-cnn-10",
        "title": "Kemenkomdigi Siapkan Peta Jalan Etika Kecerdasan Buatan (AI) Nasional",
        "url": "https://www.cnnindonesia.com/teknologi/20261020-etika-ai-kemenkominfo",
        "publisher": "CNN Indonesia",
        "category": "Teknologi",
        "published_at": "2026-10-22T10:00:00Z",
        "snippet": "Pemerintah merancang pedoman etika pemanfaatan kecerdasan buatan bagi pengembang aplikasi lokal untuk mencegah diskriminasi algoritmik dan kebocoran privasi.",
        "image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Divisi Teknologi CNN",
        "full_text": """Jakarta, CNN Indonesia -- Kementerian Komunikasi dan Digital menyusun peta jalan komprehensif terkait etika pemanfaatan teknologi Generative AI di Indonesia. Panduan ini mewajibkan transparansi data training, perlindungan hak cipta pencipta konten lokal, serta sistem mitigasi konten disinformasi deepfake."""
    },
    {
        "id": "art-ai-cnbc-11",
        "title": "Investasi Pusat Data AI Global Mengalir Deras ke Indonesia, Nilainya Tembus Rp 40 Triliun",
        "url": "https://www.cnbcindonesia.com/tech/20261020-investasi-data-center-ai",
        "publisher": "CNBC Indonesia",
        "category": "Teknologi",
        "published_at": "2026-10-22T13:30:00Z",
        "snippet": "Raksasa teknologi global memperluas kapasitas hyperscale data center berbasis energi hijau di Cikarang dan Batam guna menyokong lonjakan komputasi AI Asia Tenggara.",
        "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Tech Analyst CNBC",
        "full_text": """Jakarta, CNBC Indonesia -- Gelombang investasi infrastruktur AI terus melesat di Indonesia. Nilai realisasi investasi pusat data (data center) berstandar tier-4 diperkirakan melampaui Rp 40 triliun pada tahun ini, didorong kebutuhan pemrosesan model bahasa besar oleh korporasi perbankan dan e-commerce."""
    },
    {
        "id": "art-ai-tempo-12",
        "title": "Tantangan Kedaulatan Data dan Ancaman Penggusuran Tenaga Kerja Akibat Otomasi AI",
        "url": "https://www.tempo.co/tekno/20261020-kedaulatan-data-otomasi-ai-pekerja",
        "publisher": "Tempo",
        "category": "Teknologi",
        "published_at": "2026-10-22T15:15:00Z",
        "snippet": "Pakar komputasi dan serikat pekerja mengingatkan ancaman pergeseran jutaan pekerjaan administratif jika reskilling tenaga kerja muda tidak segera diprioritaskan.",
        "image_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Kolom Teknologi Tempo",
        "full_text": """Jakarta, Tempo.co -- Di balik pesatnya adopsi AI, kalangan akademisi dan pegiat ketenagakerjaan menyuarakan pentingnya audit independen kedaulatan data dan program transisi tenaga kerja adil. Tanpa intervensi kebijakan pendidikan terarah, disrupsi AI dikhawatirkan memperlebar kesenjangan ekonomi digital antardaerah."""
    },

    # Topik 5: Penegakan Hukum & Pemberantasan Korupsi (Hukum)
    {
        "id": "art-hukum-cnn-13",
        "title": "KPK Sita Aset Rp 350 Miliar Terkait Perkara Dugaan Korupsi Pengadaan Barang",
        "url": "https://www.cnnindonesia.com/nasional/20261025-kpk-sita-aset-korupsi",
        "publisher": "CNN Indonesia",
        "category": "Hukum",
        "published_at": "2026-10-25T08:45:00Z",
        "snippet": "Komisi Pemberantasan Korupsi mengoptimalkan pemulihan kerugian keuangan negara (asset recovery) melalui penyitaan rekening, tanah, dan kendaraan mewah para tersangka.",
        "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Biro Hukum CNN",
        "full_text": """Jakarta, CNN Indonesia -- Penyidik Komisi Pemberantasan Korupsi berhasil mengamankan aset senilai lebih dari Rp 350 miliar dalam penyidikan tindak pidana korupsi dan pencucian uang. Juru Bicara KPK menegaskan pendekatan pemiskinan koruptor dan pemulihan aset negara menjadi prioritas utama penindakan."""
    },
    {
        "id": "art-hukum-cnbc-14",
        "title": "Kepastian Hukum Jadi Sorotan Investor, RUU Perampasan Aset Kembali Dituntut Segera Disahkan",
        "url": "https://www.cnbcindonesia.com/market/20261025-ruu-perampasan-aset-investor",
        "publisher": "CNBC Indonesia",
        "category": "Hukum",
        "published_at": "2026-10-25T11:20:00Z",
        "snippet": "Asosiasi investor asing menilai kejelasan instrumen hukum penyitaan aset kejahatan finansial krusial untuk mendongkrak peringkat kemudahan berusaha (Ease of Doing Business).",
        "image_url": "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Analis Regulasi CNBC",
        "full_text": """Jakarta, CNBC Indonesia -- Pelaku pasar modal dan penanam modal asing kembali menyuarakan urgensi pengesahan RUU Perampasan Aset Tindak Pidana. Kerangka regulasi anti korupsi yang transparan dan tegas dinilai merupakan pondasi utama perbaikan iklim investasi dan kepastian hukum jangka panjang."""
    },
    {
        "id": "art-hukum-tempo-15",
        "title": "Indeks Persepsi Korupsi dan Mandeknya Reformasi Institusi Penegak Hukum",
        "url": "https://www.tempo.co/hukum/20261025-ipk-transparency-international",
        "publisher": "Tempo",
        "category": "Hukum",
        "published_at": "2026-10-25T14:00:00Z",
        "snippet": "Transparency International Indonesia memaparkan stagnasi skor IPK disebabkan lemahnya independensi lembaga antirasuah dan maraknya konflik kepentingan di parlemen.",
        "image_url": "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=600&auto=format&fit=crop&q=80",
        "source_type": "cache",
        "author": "Tim Investigasi Tempo",
        "full_text": """Jakarta, Tempo.co -- Stagnasi pemberantasan korupsi di Indonesia terus mendapat sorotan dari koalisi masyarakat sipil. Laporan terbaru menggarisbawahi keengganan pembuat undang-undang memperkuat regulasi pemberantasan suap sektor swasta dan perlindungan saksi pelapor (whistleblower)."""
    }
]

class DataStore:
    """Manajer penyimpanan memori, cache, dan dataset fallback sistem BTH."""

    def __init__(self):
        self.articles_by_id: Dict[str, Dict[str, Any]] = {}
        self.cached_searches: Dict[str, List[Dict[str, Any]]] = {}
        # Inisialisasi dengan data kurasi awal
        for item in CURATED_DATASET:
            self.articles_by_id[item["id"]] = item

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        return self.articles_by_id.get(article_id)

    def save_article(self, item: ArticleItem, full_text: str = "") -> Dict[str, Any]:
        data = item.to_dict()
        if full_text:
            data["full_text"] = full_text
        self.articles_by_id[item.id] = data
        return data

    def get_latest(self, category: str = "all", limit: int = 15) -> List[Dict[str, Any]]:
        results = list(self.articles_by_id.values())
        if category and category != "all":
            results = [a for a in results if a.get("category", "").lower() == category.lower()]
        return results[:limit]

    def search_local(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        if not query_words:
            return list(self.articles_by_id.values())[:limit]

        scored_articles = []
        for art in self.articles_by_id.values():
            text_corpus = f"{art.get('title', '')} {art.get('snippet', '')} {art.get('category', '')} {art.get('full_text', '')}".lower()
            score = 0
            for w in query_words:
                if w in art.get('title', '').lower():
                    score += 5
                if w in text_corpus:
                    score += 1
            if score > 0:
                scored_articles.append((score, art))

        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [art for _, art in scored_articles[:limit]]

# Singleton instance
store = DataStore()
