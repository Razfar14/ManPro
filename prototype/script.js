/**
 * Behind The Headline (BTH) - Client Controller & Cache Manager
 * Pembaruan:
 * 1. Layout Meja Redaksi 3-Kolom (Kilas Terkini, Headline Utama, Sorotan AI & Isu Berkembang) ala CNN.
 * 2. Strip Pantauan Isu & Radar Media ala CNBC Indonesia.
 * 3. Filter kategori instan di beranda & Rubrik Pilihan 3 Sektor.
 * 4. Navigasi Burger Menu responsif, Loading Circle Foto, Skeleton Shimmer, & Filter Topik Nyeleneh.
 */

// =========================================================================
// 0. MODUL UTILITAS, KEAMANAN HTML, CACHE & COOKIE MANAGER
// =========================================================================
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const BTHCache = {
  setCookie(name, value, days = 7) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
  },

  getCookie(name) {
    return document.cookie.split("; ").reduce((r, v) => {
      const parts = v.split("=");
      return parts[0] === encodeURIComponent(name) ? decodeURIComponent(parts[1]) : r;
    }, "");
  },

  save(key, data, ttlSeconds = 86400 * 7) {
    try {
      const payload = {
        _timestamp: Date.now(),
        _ttl: ttlSeconds * 1000,
        data: data
      };
      localStorage.setItem(`bth_${key}`, JSON.stringify(payload));
      this.setCookie(`bth_has_${key}`, "1", 7);
    } catch (e) {
      console.warn("[BTH Cache] LocalStorage tidak dapat ditulis:", e);
    }
  },

  load(key) {
    try {
      const raw = localStorage.getItem(`bth_${key}`);
      if (!raw) return null;
      const payload = JSON.parse(raw);
      if (Date.now() - payload._timestamp < payload._ttl) {
        return payload.data;
      }
    } catch (e) {
      console.warn("[BTH Cache] Gagal membaca cache:", e);
    }
    return null;
  },

  remove(key) {
    try {
      localStorage.removeItem(`bth_${key}`);
    } catch (e) {
      // ignore
    }
  }
};

BTHCache.setCookie("bth_last_visit", new Date().toISOString(), 7);

// Set tanggal hari ini di topbar jika elemen tersedia
const liveDateBadge = document.getElementById("liveDateBadge");
if (liveDateBadge) {
  const todayStr = new Date().toLocaleDateString("id-ID", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric"
  });
  liveDateBadge.textContent = `${todayStr} · Pantauan Berita & Komparasi AI`;
}

// =========================================================================
// 0B. BURGER MENU NAVIGATION & VALIDASI PENCARIAN KOSONG
// =========================================================================
function initBurgerMenu() {
  const nav = document.querySelector(".nav");
  const toggleBtn = document.getElementById("navToggle");
  const navList = document.getElementById("navList");
  if (!nav || !toggleBtn || !navList) return;

  function setMenuOpen(open) {
    nav.classList.toggle("is-open", open);
    toggleBtn.setAttribute("aria-expanded", String(open));
    toggleBtn.setAttribute("aria-label", open ? "Tutup menu kategori" : "Buka menu kategori");
  }

  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = nav.classList.contains("is-open");
    setMenuOpen(!isOpen);
  });

  navList.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMenuOpen(false));
  });

  document.addEventListener("click", (e) => {
    if (nav.classList.contains("is-open") && !nav.contains(e.target)) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav.classList.contains("is-open")) {
      setMenuOpen(false);
      toggleBtn.focus();
    }
  });
}

function initSearchValidation() {
  const form = document.getElementById("searchForm") || document.querySelector("form.search");
  const input = document.getElementById("q");
  const errorBox = document.getElementById("searchError");
  if (!form || !input) return;

  function showError(msg) {
    input.classList.remove("is-invalid");
    void input.offsetWidth;
    input.classList.add("is-invalid");
    if (errorBox) {
      errorBox.textContent = msg;
      errorBox.hidden = false;
    }
    input.focus();
  }

  function clearError() {
    input.classList.remove("is-invalid");
    if (errorBox) {
      errorBox.textContent = "";
      errorBox.hidden = true;
    }
  }

  form.addEventListener("submit", (e) => {
    const trimmed = input.value.trim();
    if (!trimmed) {
      e.preventDefault();
      showError("Silakan isi kolom pencarian dengan kata kunci atau topik berita terlebih dahulu.");
      return;
    }
    input.value = trimmed;
    clearError();
  });

  input.addEventListener("input", () => {
    if (input.value.trim().length > 0) {
      clearError();
    }
  });
}

initBurgerMenu();
initSearchValidation();

// =========================================================================
// 0C. PHOTO LOADING CIRCLE HELPER
// =========================================================================
function buildPhotoMarkup(imageUrl, altText, isLarge = false) {
  if (!imageUrl) {
    return `<span class="photo-fallback">Foto Berita</span>`;
  }
  const spinnerClass = isLarge ? "spinner" : "spinner sm";
  const lazyAttr = isLarge ? "" : ' loading="lazy"';
  return `
    <div class="photo-loader"><span class="${spinnerClass}" aria-label="Memuat foto"></span></div>
    <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(altText)}"${lazyAttr}>
  `;
}

function attachImageLoaders(rootElement) {
  if (!rootElement) return;
  const images = rootElement.querySelectorAll(".ph img, .photo img");
  images.forEach((img) => {
    const box = img.parentElement;
    const loader = box ? box.querySelector(".photo-loader") : null;

    function handleLoaded() {
      img.classList.add("loaded");
      if (loader) loader.remove();
    }

    function handleError() {
      if (loader) loader.remove();
      img.remove();
      if (box && !box.querySelector(".photo-fallback")) {
        const fb = document.createElement("span");
        fb.className = "photo-fallback";
        fb.textContent = "Foto Berita";
        box.appendChild(fb);
      }
    }

    if (img.complete) {
      if (img.naturalWidth > 0) {
        handleLoaded();
      } else {
        handleError();
      }
    } else {
      img.addEventListener("load", handleLoaded, { once: true });
      img.addEventListener("error", handleError, { once: true });
    }
  });
}

// =========================================================================
// 0D. DETEKSI TOPIK NYELENEH (FALLBACK OFFLINE / CLIENT)
// =========================================================================
const ABSURD_TOPIC_MESSAGE = "Maaf, saya tidak dapat menyajikan berita tersebut.";

function isAbsurdTopicClient(query) {
  const q = (query || "").trim();
  if (q.length < 2 || /^[\d\W_]+$/.test(q)) return true;
  const qLow = q.toLowerCase();
  if (/(.)\1{3,}/.test(qLow) || /\b(wk){2,}|(ha){3,}|(he){3,}\b/.test(qLow)) return true;
  const mashes = ["asdf", "qwer", "zxcv", "hjkl", "yuio", "fghj", "dfgh"];
  if (mashes.some((m) => qLow.includes(m))) return true;

  const validAcronyms = new Set([
    "kpk", "dpr", "mpr", "dpd", "ppn", "bbm", "pssi", "bmkg", "ihsg", "umkm",
    "tni", "polri", "asn", "bumn", "kpu", "kbri", "lpsk", "bpk", "bnpb", "brin",
    "pdip", "pkb", "pks", "ppp", "pan", "psi", "krl", "mrt", "lrt", "ikn", "ojk",
    "bpjs", "apbn", "apbd", "kuhp", "hpp", "fmcg", "kspi", "bawaslu", "komdigi"
  ]);
  const words = qLow.match(/[a-z]+/g) || [];
  if (words.length === 0) return true;
  for (const w of words) {
    if (validAcronyms.has(w)) continue;
    if (w.length >= 5 && !/[aeiou]/.test(w)) return true;
    if (/[bcdfghjklmnpqrstvwxyz]{5,}/.test(w)) return true;
  }

  const chatRe = /^(halo|hai|hi|hello|apa kabar|siapa kamu|siapa pacar|tolong buatkan|buatkan (puisi|cerpen|pantun|lirik|kode)|resep\s+\w+|cara memasak|arti mimpi|ramalan zodiak|tebak.?tebakan)\b/i;
  if (chatRe.test(qLow)) return true;

  const impossibleRe = /\b(kucing|anjing|sapi|kambing|ayam|bebek|ikan|semut|nyamuk|kecoa|tikus|kodok|katak|monyet|gajah|jerapah|buaya|cicak|tokek|ular|cacing|burung|batu|kursi|meja|sendok|galon|ember|sandal|sepatu|kulkas|kipas|sapu|tembok|pohon|awan|bulan|matahari|planet)\b.*\b(terbang|naik motor|naik mobil|nyetir|jualan|nikah|menikah|kawin|pacaran|korupsi|nyapres|jadi presiden|main bola|main futsal|ngopi|merokok|berbicara|pidato|kuliah|sekolah|demo|balapan|bertelur|makan batu|makan paku|minum bensin|main game|jadi menteri|jadi dpr)\b/i;
  if (impossibleRe.test(qLow)) return true;

  const absurdTerms = [
    "alien", "ufo", "unicorn", "naga", "zombie", "vampir", "drakula", "pocong",
    "kuntilanak", "genderuwo", "tuyul", "spongebob", "patrick", "doraemon",
    "nobita", "naruto", "sasuke", "goku", "ultraman", "pikachu", "godzilla",
    "voldemort", "thanos", "skibidi", "brainrot", "santet", "pelet", "dukun",
    "babi ngepet", "wewe gombel", "makan paku", "makan batu", "goreng es",
    "rebus es batu", "kucing bertelur", "presiden mars", "jualan di mars"
  ];
  const entertainmentCtx = ["film", "movie", "anime", "manga", "komik", "serial", "game", "bioskop", "netflix"];
  const hasEnt = entertainmentCtx.some((c) => qLow.includes(c));
  if (!hasEnt && absurdTerms.some((t) => new RegExp(`\\b${t}\\b`, "i").test(qLow))) {
    return true;
  }

  return false;
}

// =========================================================================
// DATASET CADANGAN JIKA OFFLINE
// =========================================================================
const FALLBACK_NEWS = [
  {
    id: "art-ppn-cnn-01",
    kategori: "Ekonomi",
    judul: "Pemerintah Pastikan Tarif PPN 12 Persen Berlaku Mulai 1 Januari 2025 Sesuai UU HPP",
    media: "CNN Indonesia",
    waktu: "2 jam lalu",
    warna: "#2b3b60",
    url: "https://www.cnnindonesia.com/ekonomi/20250101-ppn-12-persen-uu-hpp",
    foto: "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80",
    snippet: "Menteri Keuangan menegaskan penyesuaian tarif PPN menjadi 12 persen merupakan amanat UU HPP untuk memperkuat fondasi fiskal negara.",
    topic_summary: "Topik: Ekonomi & Fiskal. Berita ini diklasifikasikan ke dalam ranah Ekonomi & Fiskal karena membahas penyesuaian tarif PPN yang memengaruhi penerimaan APBN sekitar Rp 70-80 triliun serta perlindungan barang kebutuhan pokok bagi masyarakat rentan.",
    full_text: "Jakarta, CNN Indonesia -- Menteri Keuangan Sri Mulyani Indrawati menegaskan bahwa implementasi kenaikan tarif Pajak Pertambahan Nilai (PPN) dari 11 persen menjadi 12 persen pada 1 Januari 2025 merupakan pelaksanaan amanat UU HPP.\n\nPemerintah menargetkan penyesuaian ini mampu memberikan tambahan penerimaan negara sekitar Rp 70 triliun hingga Rp 80 triliun per tahun untuk membiayai perlindungan sosial dan infrastruktur dasar.\n\nMenkeu menekankan bahwa barang kebutuhan pokok masyarakat (sembako), jasa kesehatan, jasa pendidikan, dan jasa transportasi umum tetap dikecualikan atau dibebaskan dari pungutan PPN."
  },
  {
    id: "art-ppn-cnbc-02",
    kategori: "Ekonomi",
    judul: "PPN 12% Membayang, Pengusaha Ritel Khawatirkan Dampak Pelemahan Daya Beli dan Inflasi",
    media: "CNBC Indonesia",
    waktu: "3 jam lalu",
    warna: "#4c5e83",
    url: "https://www.cnbcindonesia.com/market/20250101-ritel-ppn-12-daya-beli",
    foto: "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=600&auto=format&fit=crop&q=80",
    snippet: "Asosiasi Pengusaha Ritel Indonesia (Aprindo) memperkirakan kenaikan PPN 12% berpotensi menekan konsumsi domestik sebesar 1,2%.",
    topic_summary: "Topik: Ekonomi & Pasar Ritel. Berita ini diklasifikasikan ke dalam topik Ekonomi & Pasar Ritel karena menyoroti kekhawatiran asosiasi pengusaha (Aprindo) terhadap potensi koreksi konsumsi domestik 1,2% dan tekanan inflasi tahunan.",
    full_text: "Jakarta, CNBC Indonesia -- Rencana pemberlakuan tarif PPN 12% menuai kekhawatiran dari pelaku industri ritel dan pasar modal. Aprindo memproyeksikan potensi koreksi indeks penjualan riil sebesar 1,2% pada kuartal pertama.\n\nKetua Umum Aprindo menyampaikan bahwa tekanan biaya operasional yang meningkat seiring kenaikan tarif pajak berisiko diteruskan ke harga jual konsumen akhir."
  },
  {
    id: "art-ppn-tempo-03",
    kategori: "Ekonomi",
    judul: "Kenaikan PPN 12%: Ekonom dan Serikat Buruh Soroti Tekanan Berat pada Kelas Menengah",
    media: "Tempo",
    waktu: "4 jam lalu",
    warna: "#29395e",
    url: "https://www.tempo.co/bisnis/20250101-ppn-12-kelas-menengah-buruh",
    foto: "https://images.unsplash.com/photo-1580519542036-c47de6196ba5?w=600&auto=format&fit=crop&q=80",
    snippet: "Direktur Eksekutif Celios menyatakan kelas menengah yang tidak menerima bansos akan menjadi kelompok paling terpukul akibat penyesuaian tarif PPN.",
    topic_summary: "Topik: Ekonomi & Kesejahteraan Buruh. Berita ini diklasifikasikan ke dalam ranah Ekonomi & Kesejahteraan Buruh karena mengulas meningkatnya beban biaya hidup kelas menengah sebesar 2,8-3,5% serta tuntutan serikat pekerja.",
    full_text: "Jakarta, Tempo.co -- Kenaikan tarif PPN 12% mendapatkan sorotan tajam dari kalangan ekonom independen dan organisasi serikat buruh. Celios menilai kebijakan ini tidak tepat waktu di tengah penurunan jumlah penduduk kelas menengah.\n\nMenurut kajian Celios, kenaikan PPN 12% dapat meningkatkan biaya hidup rata-rata keluarga urban sebesar 2,8% hingga 3,5%."
  },
  {
    id: "art-banjir-cnn-04",
    kategori: "Lingkungan",
    judul: "Pemprov DKI dan Kementerian PU Percepat Normalisasi Ciliwung Pasca Genangan",
    media: "CNN Indonesia",
    waktu: "5 jam lalu",
    url: "https://www.cnnindonesia.com/nasional/20260910-banjir-jakarta-normalisasi",
    foto: "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=600&auto=format&fit=crop&q=80",
    snippet: "Pemerintah Provinsi DKI Jakarta mengalokasikan anggaran pembebasan lahan sebesar Rp 850 miliar untuk merampungkan normalisasi Sungai Ciliwung.",
    topic_summary: "Topik: Lingkungan & Infrastruktur. Berita ini diklasifikasikan ke dalam ranah Lingkungan & Infrastruktur karena membahas percepatan normalisasi Sungai Ciliwung dengan anggaran Rp 850 miliar guna menekan risiko banjir di Jakarta.",
    full_text: "Jakarta, CNN Indonesia -- Pemprov DKI Jakarta bersama Kementerian Pekerjaan Umum bergerak cepat mempercepat proyek normalisasi Sungai Ciliwung sepanjang 17 kilometer yang sempat tertunda. Alokasi anggaran sebesar Rp 850 miliar disiapkan tahun anggaran ini untuk pembebasan lahan bantaran sungai.\n\nKepala Dinas Sumber Daya Air DKI menyatakan pengerjaan polder dan penguatan tanggul di kawasan rawan seperti Bidara Cina dan Kampung Melayu berhasil mengurangi durasi genangan dari 14 jam menjadi 4 jam pada curah hujan ekstrem pekan lalu."
  },
  {
    id: "art-pilkada-cnn-07",
    kategori: "Politik",
    judul: "KPU Pastikan Logistik Surat Suara Pilkada Serentak Terdistribusi 98 Persen",
    media: "CNN Indonesia",
    waktu: "6 jam lalu",
    url: "https://www.cnnindonesia.com/nasional/20261012-kpu-logistik-pilkada",
    foto: "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=600&auto=format&fit=crop&q=80",
    snippet: "Komisi Pemilihan Umum memastikan seluruh logistik utama surat suara dan kotak suara telah mencapai KPUD di seluruh provinsi tepat waktu.",
    topic_summary: "Topik: Politik & Tata Kelola Pemerintahan. Berita ini diklasifikasikan ke dalam ranah Politik & Tata Kelola Pemerintahan karena menyoroti kesiapan distribusi logistik Pilkada Serentak sebesar 98 persen di 545 daerah oleh KPU RI.",
    full_text: "Jakarta, CNN Indonesia -- Komisi Pemilihan Umum (KPU) RI menyatakan kesiapan penyelenggaraan Pilkada Serentak di 545 daerah telah mencapai 98 persen. Distribusi surat suara dan kotak suara di wilayah terdepan, terluar, dan tertinggal (3T) mendapat prioritas pengiriman dengan pengawalan aparat TNI dan Polri.\n\nKetua KPU menegaskan koordinasi bersama pemerintah daerah dan Bawaslu terus diperkuat agar tahapan pemungutan serta penghitungan suara berjalan transparan dan tepat waktu."
  },
  {
    id: "art-ai-cnn-10",
    kategori: "Teknologi",
    judul: "Kemenkomdigi Siapkan Peta Jalan Etika Kecerdasan Buatan (AI) Nasional",
    media: "CNN Indonesia",
    waktu: "7 jam lalu",
    url: "https://www.cnnindonesia.com/teknologi/20261020-etika-ai-kemenkominfo",
    foto: "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&auto=format&fit=crop&q=80",
    snippet: "Pemerintah merancang pedoman etika pemanfaatan kecerdasan buatan bagi pengembang aplikasi lokal untuk mencegah diskriminasi algoritmik.",
    topic_summary: "Topik: Teknologi & Transformasi Digital. Berita ini diklasifikasikan ke dalam ranah Teknologi & Transformasi Digital karena mengulas penyusunan regulasi etika Generative AI, perlindungan privasi data, dan mitigasi konten deepfake oleh Kemenkomdigi.",
    full_text: "Jakarta, CNN Indonesia -- Kementerian Komunikasi dan Digital menyusun peta jalan komprehensif terkait etika pemanfaatan teknologi Generative AI di Indonesia. Panduan ini mewajibkan transparansi data training, perlindungan hak cipta pencipta konten lokal, serta sistem mitigasi konten disinformasi deepfake.\n\nPemerintah juga mendorong kolaborasi antara pelaku industri pusat data, akademisi, dan pengembang startup lokal untuk memperkuat ekosistem kecerdasan buatan nasional yang berdaulat."
  },
  {
    id: "art-hukum-cnn-13",
    kategori: "Hukum",
    judul: "KPK Sita Aset Rp 350 Miliar Terkait Perkara Dugaan Korupsi Pengadaan Barang",
    media: "CNN Indonesia",
    waktu: "8 jam lalu",
    url: "https://www.cnnindonesia.com/nasional/20261025-kpk-sita-aset-korupsi",
    foto: "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&auto=format&fit=crop&q=80",
    snippet: "Komisi Pemberantasan Korupsi mengoptimalkan pemulihan kerugian keuangan negara melalui penyitaan rekening dan aset tersangka.",
    topic_summary: "Topik: Hukum & Penegakan Keadilan. Berita ini diklasifikasikan ke dalam ranah Hukum & Penegakan Keadilan karena membahas tindakan penyitaan aset Rp 350 miliar oleh KPK dalam upaya pemulihan kerugian keuangan negara (asset recovery).",
    full_text: "Jakarta, CNN Indonesia -- Penyidik Komisi Pemberantasan Korupsi berhasil mengamankan aset senilai lebih dari Rp 350 miliar dalam penyidikan tindak pidana korupsi dan pencucian uang. Juru Bicara KPK menegaskan pendekatan pemiskinan koruptor dan pemulihan aset negara menjadi prioritas utama penindakan.\n\nSelain penyitaan aset fisik berupa tanah dan bangunan, penyidik juga menelusuri aliran dana melalui koordinasi bersama PPATK guna memulihkan kerugian negara secara maksimal."
  }
];

const params = new URLSearchParams(window.location.search);
const currentQuery = (params.get("q") || "").trim();
const currentId = (params.get("id") || "").trim();
const isFileProtocol = window.location.protocol === "file:";
const isLocalHost = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
const isStaticDevPort = isLocalHost && window.location.port !== "" && window.location.port !== "8000";
const API_BASE_URL = isStaticDevPort ? "http://localhost:8000" : "";
let backendUnavailable = false;

async function apiGet(endpoint) {
  if (isFileProtocol || backendUnavailable) return null;
  const targetUrl = `${API_BASE_URL}${endpoint}`;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), isStaticDevPort ? 4000 : 25000);
    const res = await fetch(targetUrl, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    if (isStaticDevPort) {
      backendUnavailable = true;
      console.info("[BTH Mode Live Server] Backend Python (port 8000) belum dijalankan. Menggunakan dataset lokal.");
    } else {
      console.warn(`[BTH API] Endpoint ${endpoint} tidak terjangkau (${err.message}). Beralih ke data lokal.`);
    }
    return null;
  }
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return "Terkini";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const diffHours = Math.round((Date.now() - d.getTime()) / (1000 * 60 * 60));
    if (diffHours <= 0) return "Baru saja";
    if (diffHours < 24) return `${diffHours} jam lalu`;
    return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
  } catch (e) {
    return "Terkini";
  }
}

function cleanSnippetText(snippet, title, publisher) {
  if (!snippet) return "";
  const s = snippet.replace(/\s+/g, " ").trim();
  const t = (title || "").trim().toLowerCase();
  if (!s || s.toLowerCase() === t || (s.toLowerCase().startsWith(t) && s.length <= t.length + (publisher || "").length + 12)) {
    return "";
  }
  return s.length > 140 ? s.slice(0, 137) + "..." : s;
}

// =========================================================================
// 1. BERANDA (index.html): MEJA REDAKSI 3 KOLOM + GRID + FILTER KATEGORI
// =========================================================================
const grid = document.getElementById("grid");
const featuredStory = document.getElementById("featuredStory");
const liveUpdatesContainer = document.getElementById("liveUpdatesContainer");
const developingContainer = document.getElementById("developingContainer");
const categoryShowcase = document.getElementById("categoryShowcase");
const categoryFilterPills = document.getElementById("categoryFilterPills");
const refreshBtn = document.getElementById("refreshBtn");
const lastUpdatedText = document.getElementById("lastUpdatedText");

if (grid) {
  let allHomepageArticles = [];
  let activeCategoryFilter = "all";

  function renderGridSkeleton(count = 8) {
    grid.innerHTML = Array.from({ length: count }, () => `
      <article class="card" aria-hidden="true">
        <div class="ph">
          <div class="photo-loader"><span class="spinner sm"></span></div>
        </div>
        <div class="info">
          <span class="skeleton sk-chip"></span>
          <span class="skeleton sk-line sk-w-100"></span>
          <span class="skeleton sk-line sk-w-90"></span>
          <span class="skeleton sk-line sk-w-65"></span>
          <span class="skeleton sk-line sm sk-w-45" style="margin-top:auto"></span>
        </div>
      </article>
    `).join("");
  }

  function renderNewsroomDesk(articles) {
    if (!articles || articles.length === 0) return;

    const lead = articles[0];
    const leftLead = articles[1] || articles[0];
    const leftList = articles.slice(2, 6);
    const rightList = articles.slice(6, 10).length > 0 ? articles.slice(6, 10) : articles.slice(1, 4);
    const subBullets = articles.slice(1, 3);

    // 1. Kolom Tengah: Headline Utama ala CNN
    if (featuredStory && lead) {
      const leadId = lead.id || "art-ppn-cnn-01";
      const leadKat = lead.category || lead.kategori || "Nasional";
      const leadJudul = lead.title || lead.judul || "Berita Utama";
      const leadPub = lead.publisher || lead.media || "Media Nasional";
      const leadTime = formatRelativeTime(lead.published_at || lead.waktu);
      const leadImg = lead.image_url || lead.foto;
      const leadSnippet = cleanSnippetText(lead.snippet, leadJudul, leadPub) ||
        `Laporan utama dari ${leadPub} menyoroti perkembangan penting di sektor ${leadKat}. Klik untuk membaca ringkasan paragraf pilihan serta analisis komparasi topik AI.`;

      const bulletsHtml = subBullets.map((b) => {
        const bId = b.id || "art-ppn-cnn-01";
        const bTitle = b.title || b.judul || "";
        const bPub = b.publisher || b.media || "Media";
        return `<li><a href="detail.html?id=${encodeURIComponent(bId)}">${escapeHtml(bTitle)} <span style="color:var(--muted);font-weight:400">(${escapeHtml(bPub)})</span></a></li>`;
      }).join("");

      featuredStory.innerHTML = `
        <article class="main-headline-card">
          <div class="ph">${buildPhotoMarkup(leadImg, leadJudul, true)}</div>
          <div class="main-headline-body">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span class="chip spotlight">HEADLINE UTAMA</span>
              <span class="chip">${escapeHtml(leadKat)}</span>
              <span class="meta" style="margin-top:0">${escapeHtml(leadPub)} · ${escapeHtml(leadTime)}</span>
            </div>
            <h2><a href="detail.html?id=${encodeURIComponent(leadId)}">${escapeHtml(leadJudul)}</a></h2>
            <p>${escapeHtml(leadSnippet)}</p>
            ${bulletsHtml ? `<ul class="main-subbullets">${bulletsHtml}</ul>` : ""}
          </div>
        </article>
      `;
      attachImageLoaders(featuredStory);
    }

    // 2. Kolom Kiri: Kilas Berita Terkini (Live Updates)
    if (liveUpdatesContainer && leftLead) {
      const lId = leftLead.id || "art-ppn-cnn-01";
      const lTitle = leftLead.title || leftLead.judul || "Berita Terkini";
      const lPub = leftLead.publisher || leftLead.media || "Media";
      const lKat = leftLead.category || leftLead.kategori || "Nasional";
      const lSnippet = cleanSnippetText(leftLead.snippet, lTitle, lPub) ||
        `Sorotan ${lPub} mengenai perkembangan terbaru isu ${lKat} yang menjadi perhatian publik.`;

      const listHtml = leftList.map((item) => {
        const id = item.id || "art-ppn-cnn-01";
        const title = item.title || item.judul || "";
        const pub = item.publisher || item.media || "Media";
        const time = formatRelativeTime(item.published_at || item.waktu);
        return `
          <li>
            <a href="detail.html?id=${encodeURIComponent(id)}">${escapeHtml(title)}</a>
            <small>${escapeHtml(pub)} · ${escapeHtml(time)}</small>
          </li>
        `;
      }).join("");

      liveUpdatesContainer.innerHTML = `
        <div class="desk-lead-left">
          <span class="chip" style="margin-bottom:8px">${escapeHtml(lKat)}</span>
          <h3><a href="detail.html?id=${encodeURIComponent(lId)}">${escapeHtml(lTitle)}</a></h3>
          <p>${escapeHtml(lSnippet)}</p>
        </div>
        <span class="desk-live-badge">● Umpan Berita Masuk</span>
        <ul class="desk-list-left">${listHtml}</ul>
      `;
    }

    // 3. Kolom Kanan: Developing Stories dengan Thumbnail
    if (developingContainer) {
      developingContainer.innerHTML = `<div class="developing-list">${rightList.map((item) => {
        const id = item.id || "art-ppn-cnn-01";
        const title = item.title || item.judul || "";
        const pub = item.publisher || item.media || "Media";
        const img = item.image_url || item.foto || "";
        return `
          <div class="developing-item">
            <div class="ph">${buildPhotoMarkup(img, title)}</div>
            <div>
              <h4><a href="detail.html?id=${encodeURIComponent(id)}">${escapeHtml(title)}</a></h4>
              <small>${escapeHtml(pub)}</small>
            </div>
          </div>
        `;
      }).join("")}</div>`;
      attachImageLoaders(developingContainer);
    }
  }

  function renderCategoryShowcase(articles) {
    if (!categoryShowcase || !articles || articles.length === 0) return;
    const groups = [
      { title: "Politik & Hukum", query: "Politik", match: ["politik", "hukum", "nasional"] },
      { title: "Ekonomi & Fiskal", query: "Ekonomi", match: ["ekonomi", "bisnis"] },
      { title: "Teknologi & Lingkungan", query: "Teknologi", match: ["teknologi", "lingkungan"] }
    ];

    categoryShowcase.innerHTML = groups.map((g) => {
      const matched = articles.filter((a) => {
        const c = (a.category || a.kategori || "").toLowerCase();
        return g.match.some((m) => c.includes(m));
      }).slice(0, 3);
      const list = matched.length > 0 ? matched : articles.slice(0, 3);

      return `
        <div class="rubric-col">
          <div class="rubric-col-head">
            <h3>${escapeHtml(g.title)}</h3>
            <a href="hasil.html?q=${encodeURIComponent(g.query)}">Bandingkan Isu →</a>
          </div>
          <ul class="rubric-list">
            ${list.map((item) => `
              <li>
                <a href="detail.html?id=${encodeURIComponent(item.id || "art-ppn-cnn-01")}">${escapeHtml(item.title || item.judul)}</a>
                <small>${escapeHtml(item.publisher || item.media || "Media Nasional")} · ${escapeHtml(formatRelativeTime(item.published_at || item.waktu))}</small>
              </li>
            `).join("")}
          </ul>
        </div>
      `;
    }).join("");
  }

  function renderFilteredGrid() {
    const filtered = activeCategoryFilter === "all"
      ? allHomepageArticles
      : allHomepageArticles.filter((a) => (a.category || a.kategori || "").toLowerCase() === activeCategoryFilter.toLowerCase());

    const listToRender = filtered.length > 0 ? filtered : allHomepageArticles;

    grid.innerHTML = listToRender.map((item) => {
      const artId = item.id || "art-ppn-cnn-01";
      const kategori = item.category || item.kategori || "Nasional";
      const judul = item.title || item.judul || "Judul Berita";
      const publisher = item.publisher || item.media || "Media Indonesia";
      const timeStr = formatRelativeTime(item.published_at || item.waktu);
      const imageUrl = item.image_url || item.foto;
      const snippet = cleanSnippetText(item.snippet, judul, publisher);

      return `
        <article class="card">
          <div class="ph">${buildPhotoMarkup(imageUrl, judul)}</div>
          <div class="info">
            <span class="chip">${escapeHtml(kategori)}</span>
            <h3><a href="detail.html?id=${encodeURIComponent(artId)}">${escapeHtml(judul)}</a></h3>
            ${snippet ? `<p class="card-snippet">${escapeHtml(snippet)}</p>` : ""}
            <div class="meta">${escapeHtml(publisher)} · ${escapeHtml(timeStr)}</div>
          </div>
        </article>
      `;
    }).join("");
    attachImageLoaders(grid);
  }

  function renderHomepageAll(articles) {
    if (!articles || articles.length === 0) return;
    allHomepageArticles = articles;
    renderNewsroomDesk(articles);
    renderFilteredGrid();
    renderCategoryShowcase(articles);

    if (lastUpdatedText) {
      const nowTime = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
      lastUpdatedText.textContent = `Menampilkan ${articles.length} berita lintas redaksi · Diperbarui pukul ${nowTime} WIB`;
    }
  }

  if (categoryFilterPills) {
    categoryFilterPills.querySelectorAll(".cat-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        categoryFilterPills.querySelectorAll(".cat-pill").forEach((b) => b.classList.remove("on"));
        btn.classList.add("on");
        activeCategoryFilter = btn.getAttribute("data-cat") || "all";
        renderFilteredGrid();
      });
    });
  }

  async function loadHomepageNews(forceRefresh = false) {
    if (forceRefresh) {
      BTHCache.remove("homepage_articles");
    }
    const cachedArticles = !forceRefresh ? BTHCache.load("homepage_articles") : null;
    if (cachedArticles && cachedArticles.length > 0) {
      renderHomepageAll(cachedArticles);
    } else {
      renderGridSkeleton(8);
    }

    const data = await apiGet("/api/v1/news/latest?limit=16");
    if (data && data.articles && data.articles.length > 0) {
      BTHCache.save("homepage_articles", data.articles, 600);
      renderHomepageAll(data.articles);
    } else if (!cachedArticles) {
      renderHomepageAll(FALLBACK_NEWS);
    }
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadHomepageNews(true);
    });
  }

  loadHomepageNews(false);
}

// =========================================================================
// 2. HASIL PENCARIAN (hasil.html): SKELETON, FILTER NYELENEH & KOMPARASI
// =========================================================================
const qInput = document.getElementById("q");
if (qInput && currentQuery) {
  qInput.value = currentQuery;
}

if (currentQuery) {
  document.querySelectorAll(".nav li a").forEach((link) => {
    if (link.textContent.trim().toLowerCase() === currentQuery.toLowerCase()) {
      link.classList.add("on");
    } else if (link.getAttribute("href") === "index.html") {
      link.classList.remove("on");
    }
  });
}

const toggle = document.getElementById("aiToggle");
if (toggle) {
  toggle.addEventListener("click", () => {
    const off = document.body.classList.toggle("hide-ai");
    toggle.setAttribute("aria-pressed", String(!off));
    toggle.style.opacity = off ? 0.45 : 1;
  });
}

const compareTable = document.getElementById("compareTable");
const aiSummaryElem = document.getElementById("aiSummary");
const beritaListElem = document.getElementById("beritaList");
const beritaCountElem = document.getElementById("beritaCount");
const compareSectionElem = document.getElementById("compareSection");
const beritaSectionElem = document.getElementById("beritaSection");
const aiNoteElem = document.getElementById("aiNote");
const insightGridElem = document.getElementById("insightGrid");
const consensusListElem = document.getElementById("consensusList");
const divergenceListElem = document.getElementById("divergenceList");

if (compareTable && aiSummaryElem) {
  function setResultsVisibility(visible) {
    if (compareSectionElem) compareSectionElem.hidden = !visible;
    if (beritaSectionElem) beritaSectionElem.hidden = !visible;
    if (aiNoteElem) aiNoteElem.hidden = !visible;
  }

  function renderSearchSkeleton() {
    setResultsVisibility(true);
    if (insightGridElem) insightGridElem.hidden = true;
    aiSummaryElem.innerHTML = `
      <span class="skeleton on-dark sk-line sk-w-100"></span>
      <span class="skeleton on-dark sk-line sk-w-90"></span>
      <span class="skeleton on-dark sk-line sk-w-80"></span>
      <span class="skeleton on-dark sk-line sk-w-65"></span>
    `;
    const tbody = document.getElementById("compareBody");
    if (tbody) {
      tbody.innerHTML = ["Data angka", "Narasumber", "Fokus berita"].map((aspek) => `
        <tr>
          <td>${aspek}</td>
          <td><span class="skeleton sk-line sk-w-90"></span></td>
          <td><span class="skeleton sk-line sk-w-80"></span></td>
          <td><span class="skeleton sk-line sk-w-90"></span></td>
        </tr>
      `).join("");
    }
    if (beritaListElem) {
      beritaListElem.innerHTML = Array.from({ length: 3 }, () => `
        <article class="item" aria-hidden="true">
          <span class="skeleton sk-line sm sk-w-45"></span>
          <span class="skeleton sk-line lg sk-w-90" style="margin-top:10px"></span>
          <span class="skeleton sk-line sm sk-w-45" style="margin-top:10px"></span>
        </article>
      `).join("");
    }
  }

  function renderEmptyOrInvalidState(messageText) {
    aiSummaryElem.innerHTML = `<p style="margin-top:0">${escapeHtml(messageText)}</p>`;
    const tbody = document.getElementById("compareBody");
    if (tbody) tbody.innerHTML = "";
    if (beritaListElem) beritaListElem.innerHTML = "";
    if (insightGridElem) insightGridElem.hidden = true;
    setResultsVisibility(false);
  }

  function renderRichNewsItem(art) {
    const id = art.id || "art-ppn-cnn-01";
    const pub = art.publisher || art.media || "Media Daring";
    const title = art.title || art.judul || "Berita";
    const cat = art.category || art.kategori || "Nasional";
    const timeStr = formatRelativeTime(art.published_at || art.waktu);
    const imgUrl = art.image_url || art.foto || "";
    const url = art.url || "#";
    const snippet = cleanSnippetText(art.snippet, title, pub);

    return `
      <article class="item item-rich">
        <div class="ph">${buildPhotoMarkup(imgUrl, title)}</div>
        <div>
          <div class="item-meta-top">
            <span class="chip">${escapeHtml(cat)}</span>
            <small>${escapeHtml(pub)}</small>
            <span class="item-time">· ${escapeHtml(timeStr)}</span>
          </div>
          <h3><a href="detail.html?id=${encodeURIComponent(id)}">${escapeHtml(title)}</a></h3>
          ${snippet ? `<p class="item-snippet">${escapeHtml(snippet)}</p>` : ""}
          <div class="item-links">
            <a class="src" href="detail.html?id=${encodeURIComponent(id)}">Baca ringkasan &amp; analisis →</a>
            <a class="src secondary" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Sumber asli ↗</a>
          </div>
        </div>
      </article>
    `;
  }

  function renderSearchData(data, fromClientCache = false) {
    if (data.invalid_topic) {
      renderEmptyOrInvalidState(data.aiSummary || ABSURD_TOPIC_MESSAGE);
      return;
    }

    setResultsVisibility(true);
    const cachePill = fromClientCache || data.from_cache
      ? `<span class="chip" style="background:#d4edda;color:#155724;font-size:10px;margin-top:10px;display:inline-block;">⚡ Dimuat dari Cache</span>`
      : "";

    const rawSummary = data.aiSummary || "Ringkasan komparatif berhasil dianalisis.";
    const summaryHtml = rawSummary
      .split(/\n+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => `<p>${escapeHtml(s)}</p>`)
      .join("");

    aiSummaryElem.innerHTML = `${summaryHtml}${cachePill}`;

    const matrix = data.comparisonMatrix;
    if (matrix && matrix.rows && matrix.rows.length > 0) {
      const thead = document.getElementById("compareHead");
      const tbody = document.getElementById("compareBody");

      if (thead && matrix.columns && matrix.columns.length > 0) {
        thead.innerHTML = `<tr>${matrix.columns.map((col) => `<th>${escapeHtml(col)}</th>`).join("")}</tr>`;
      }

      if (tbody) {
        tbody.innerHTML = matrix.rows.map((row) => `
          <tr>
            <td>${escapeHtml(row.aspek || "-")}</td>
            <td>${escapeHtml(row.cnn || "-")}</td>
            <td>${escapeHtml(row.cnbc || "-")}</td>
            <td>${escapeHtml(row.tempo || "-")}</td>
          </tr>
        `).join("");
      }
    }

    const consensus = Array.isArray(data.consensus) ? data.consensus : [];
    const divergence = Array.isArray(data.divergence) ? data.divergence : [];
    if (insightGridElem && consensusListElem && divergenceListElem && (consensus.length > 0 || divergence.length > 0)) {
      consensusListElem.innerHTML = consensus.map((c) => `<li>${escapeHtml(c)}</li>`).join("");
      divergenceListElem.innerHTML = divergence.map((d) => `<li>${escapeHtml(d)}</li>`).join("");
      insightGridElem.hidden = false;
    } else if (insightGridElem) {
      insightGridElem.hidden = true;
    }

    if (beritaListElem) {
      if (data.articles && data.articles.length > 0) {
        if (beritaCountElem) {
          beritaCountElem.textContent = `${data.articles.length} sumber berita ditemukan`;
        }
        beritaListElem.innerHTML = data.articles.map(renderRichNewsItem).join("");
        attachImageLoaders(beritaListElem);
      } else {
        if (beritaSectionElem) beritaSectionElem.hidden = true;
      }
    }
  }

  async function loadSearchResults() {
    if (!currentQuery) {
      document.title = "Pencarian Berita — Behind The Headline";
      renderEmptyOrInvalidState("Silakan masukkan kata kunci atau topik berita pada kolom pencarian di atas untuk melihat ringkasan AI dan perbandingan antarmedia.");
      return;
    }

    document.title = `${currentQuery} — Behind The Headline`;

    if (isAbsurdTopicClient(currentQuery)) {
      renderEmptyOrInvalidState(ABSURD_TOPIC_MESSAGE);
      return;
    }

    const cacheKey = `search_v3_${currentQuery.toLowerCase()}`;
    const cachedData = BTHCache.load(cacheKey);

    if (cachedData) {
      renderSearchData(cachedData, true);
      return;
    }

    renderSearchSkeleton();

    const data = await apiGet(`/api/v1/search?q=${encodeURIComponent(currentQuery)}&limit=6`);

    if (data && data.status === "success") {
      BTHCache.save(cacheKey, data, 86400 * 7);
      renderSearchData(data, false);
      return;
    }

    const qLow = currentQuery.toLowerCase();
    const matchedFallback = FALLBACK_NEWS.filter((item) =>
      `${item.judul} ${item.kategori} ${item.full_text || ""}`.toLowerCase().includes(qLow)
    );

    if (matchedFallback.length === 0) {
      renderEmptyOrInvalidState(ABSURD_TOPIC_MESSAGE);
      return;
    }

    setResultsVisibility(true);
    aiSummaryElem.innerHTML = `<p>Topik '${escapeHtml(currentQuery)}' membahas rencana penyesuaian tarif Pajak Pertambahan Nilai (PPN) dari 11% menjadi 12% sesuai amanat UU HPP mulai 2025. Pemerintah menargetkan tambahan penerimaan Rp 70–80 triliun untuk perlindungan sosial dengan mengecualikan kebutuhan pokok, sementara pelaku ritel mengkhawatirkan penurunan konsumsi dan ekonom menyoroti beban kelas menengah.</p>`;
    const tbody = document.getElementById("compareBody");
    if (tbody) {
      tbody.innerHTML = `
        <tr><td>Data angka</td><td>Tarif PPN 12%; proyeksi Rp 70-80 triliun</td><td>Koreksi penjualan 1,2%; inflasi 0,3-0,5%</td><td>Biaya hidup urban 2,8-3,5%</td></tr>
        <tr><td>Narasumber</td><td>Menteri Keuangan Sri Mulyani</td><td>Ketua Aprindo Roy Nicholas Mandey</td><td>Direktur Celios Bhima Yudhistira</td></tr>
        <tr><td>Fokus berita</td><td>Amanat regulasi UU HPP</td><td>Sentimen ritel &amp; pasar modal</td><td>Daya beli kelas menengah</td></tr>
      `;
    }
    if (beritaListElem) {
      beritaListElem.innerHTML = matchedFallback.slice(0, 3).map(renderRichNewsItem).join("");
      attachImageLoaders(beritaListElem);
    }
  }

  loadSearchResults();
}

// =========================================================================
// 3. DETAIL BERITA (detail.html): SKELETON, PHOTO SPINNER & RINGKASAN TOPIK
// =========================================================================
const detailJudul = document.getElementById("judul");
if (detailJudul) {
  function renderDetailSkeleton() {
    detailJudul.innerHTML = `
      <span class="skeleton sk-line xl sk-w-100"></span>
      <span class="skeleton sk-line xl sk-w-80"></span>
    `;
    const penulisElem = document.getElementById("penulisDate");
    if (penulisElem) {
      penulisElem.innerHTML = `<span class="skeleton sk-line sm sk-w-45"></span>`;
    }
    const fotoContainer = document.getElementById("foto");
    if (fotoContainer) {
      fotoContainer.innerHTML = `<div class="photo-loader"><span class="spinner" aria-label="Memuat foto berita"></span></div>`;
    }
    const isiContainer = document.getElementById("isiBerita");
    if (isiContainer) {
      isiContainer.innerHTML = `
        <span class="skeleton sk-line sk-w-100"></span>
        <span class="skeleton sk-line sk-w-90"></span>
        <span class="skeleton sk-line sk-w-100"></span>
        <span class="skeleton sk-line sk-w-80"></span>
        <span class="skeleton sk-line sk-w-100" style="margin-top:16px"></span>
        <span class="skeleton sk-line sk-w-90"></span>
        <span class="skeleton sk-line sk-w-65"></span>
      `;
    }
    const aiDetail = document.getElementById("aiSummaryDetail");
    if (aiDetail) {
      aiDetail.innerHTML = `
        <span class="skeleton on-dark sk-line sk-w-100"></span>
        <span class="skeleton on-dark sk-line sk-w-90"></span>
        <span class="skeleton on-dark sk-line sk-w-65"></span>
      `;
    }
  }

  function renderArticleDetail(article, relatedArticles) {
    const titleText = article.title || article.judul || "Detail Berita";
    detailJudul.textContent = titleText;
    document.title = `${titleText} — Behind The Headline`;

    const categoryName = article.category || article.kategori || "Berita";
    const katElem = document.getElementById("kategori");
    if (katElem) katElem.textContent = categoryName;

    const pubElem = document.getElementById("metaPublisher");
    if (pubElem) {
      const pubName = article.publisher || article.media || "Media Indonesia";
      const timeStr = formatRelativeTime(article.published_at || article.waktu);
      pubElem.textContent = `${pubName} · ${timeStr}`;
    }

    const penulisElem = document.getElementById("penulisDate");
    if (penulisElem) {
      const author = article.author || "Tim Redaksi";
      const pubDate = article.published_at ? new Date(article.published_at).toLocaleDateString("id-ID", { day: "numeric", month: "long", year: "numeric" }) : "Terbaru";
      penulisElem.textContent = `Oleh ${author} · ${pubDate}`;
    }

    const fotoContainer = document.getElementById("foto");
    const imgUrl = article.image_url || article.foto;
    if (fotoContainer) {
      fotoContainer.innerHTML = buildPhotoMarkup(imgUrl, titleText, true);
      attachImageLoaders(fotoContainer.parentElement);
    }

    const isiContainer = document.getElementById("isiBerita");
    if (isiContainer) {
      let paragraphs = [];
      if (article.paragraphs && Array.isArray(article.paragraphs) && article.paragraphs.length > 0) {
        paragraphs = article.paragraphs;
      } else if (article.full_text) {
        paragraphs = article.full_text.split(/\n\s*\n/).map((p) => p.trim()).filter((p) => p.length > 20);
      }

      if (paragraphs.length > 4) {
        paragraphs = paragraphs.slice(0, 4);
      } else if (paragraphs.length === 0) {
        paragraphs = [article.snippet || "Paragraf artikel sedang disiapkan oleh sistem."];
      }

      isiContainer.innerHTML = paragraphs.map((p) => `<p>${escapeHtml(p)}</p>`).join("");
    }

    const srcLink = document.getElementById("linkSumberAsli");
    if (srcLink && (article.url || article.link)) {
      srcLink.href = article.url || article.link;
    }

    const compareTopicBtn = document.getElementById("compareTopicBtn");
    if (compareTopicBtn) {
      const topicQuery = categoryName !== "Berita" ? categoryName : titleText.split(" ").slice(0, 3).join(" ");
      compareTopicBtn.href = `hasil.html?q=${encodeURIComponent(topicQuery)}`;
    }

    const shareBtn = document.getElementById("shareBtn");
    if (shareBtn) {
      shareBtn.onclick = async () => {
        try {
          await navigator.clipboard.writeText(window.location.href);
          shareBtn.textContent = "✓ Tautan tersalin";
          setTimeout(() => { shareBtn.textContent = "Salin tautan"; }, 2200);
        } catch (e) {
          shareBtn.textContent = "Gagal menyalin";
        }
      };
    }

    const aiDetail = document.getElementById("aiSummaryDetail");
    if (aiDetail) {
      const topicText = article.topic_summary || article.ai_summary || (
        `Topik: ${categoryName}. Berita ini diklasifikasikan ke dalam ranah ${categoryName} berdasarkan fokus pembahasan isu dalam laporan ${article.publisher || article.media}.`
      );
      aiDetail.innerHTML = `<p style="margin-top:0">${escapeHtml(topicText)}</p>`;
    }

    const relatedContainer = document.getElementById("relatedNews");
    if (relatedContainer && relatedArticles && relatedArticles.length > 0) {
      relatedContainer.innerHTML = relatedArticles.map((rel) => `
        <article class="item">
          <div class="item-meta-top">
            <span class="chip">${escapeHtml(rel.category || rel.kategori || categoryName)}</span>
            <small>${escapeHtml(rel.publisher || rel.media || "Media Lain")}</small>
          </div>
          <h3><a href="detail.html?id=${encodeURIComponent(rel.id)}">${escapeHtml(rel.title || rel.judul)}</a></h3>
          <div class="item-links">
            <a class="src" href="detail.html?id=${encodeURIComponent(rel.id)}">Baca ringkasan →</a>
            <a class="src secondary" href="${escapeHtml(rel.url)}" target="_blank" rel="noopener noreferrer">Sumber asli ↗</a>
          </div>
        </article>
      `).join("");
    } else if (relatedContainer) {
      relatedContainer.innerHTML = `<p style="color:var(--muted);font-size:13px;">Belum ada liputan pembanding tambahan untuk artikel ini.</p>`;
    }
  }

  async function loadArticleDetail() {
    const artId = currentId || "art-ppn-cnn-01";
    const cacheKey = `article_v4_${artId}`;

    const cachedArticleData = BTHCache.load(cacheKey);
    if (
      cachedArticleData &&
      cachedArticleData.article &&
      cachedArticleData.article.topic_summary
    ) {
      renderArticleDetail(cachedArticleData.article, cachedArticleData.related || []);
      return;
    }

    renderDetailSkeleton();

    const data = await apiGet(`/api/v1/article/${encodeURIComponent(artId)}`);
    if (data && data.status === "success" && data.article) {
      BTHCache.save(cacheKey, { article: data.article, related: data.article.related_articles || [] }, 86400 * 7);
      renderArticleDetail(data.article, data.article.related_articles || []);
    } else {
      const fallbackArt = FALLBACK_NEWS.find((a) => a.id === artId) || FALLBACK_NEWS[0];
      const fallbackRel = FALLBACK_NEWS.filter((a) => a.id !== fallbackArt.id).slice(0, 2);
      renderArticleDetail(fallbackArt, fallbackRel);
    }
  }

  loadArticleDetail();
}
