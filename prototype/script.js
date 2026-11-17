/**
 * Behind The Headline (BTH) - Client Controller & Cache Manager
 * Pembaruan:
 * 1. Navigasi Burger Menu responsif & optimal di layar mobile.
 * 2. Filter pencarian kosong (mencegah submit bila input belum diisi).
 * 3. Loading circle (spinner) pada foto hingga gambar selesai dimuat.
 * 4. Skeleton shimmer placeholder untuk teks & kartu saat memuat data.
 * 5. Penanganan topik berita nyeleneh (balasan penolakan & halaman kosong).
 * 6. Halaman Detail: 2-4 paragraf pilihan & Ringkasan Topik Tematik yang informatif.
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
  }
};

BTHCache.setCookie("bth_last_visit", new Date().toISOString(), 7);

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
    void input.offsetWidth; // trigger reflow agar animasi shake dapat berulang
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
    topic_summary: "Topik: Ekonomi & Kesejahteraan Buruh. Berita ini diklasifikasikan ke dalam ranah Ekonomi & Kesejahteraan Buruh karena mengulas meningkatnya beban biaya hidup kelas menengah sebesar 2,8-3,5% serta tuntutan serikat pekerja.",
    full_text: "Jakarta, Tempo.co -- Kenaikan tarif PPN 12% mendapatkan sorotan tajam dari kalangan ekonom independen dan organisasi serikat buruh. Celios menilai kebijakan ini tidak tepat waktu di tengah penurunan jumlah penduduk kelas menengah.\n\nMenurut kajian Celios, kenaikan PPN 12% dapat meningkatkan biaya hidup rata-rata keluarga urban sebesar 2,8% hingga 3,5%."
  }
];

const params = new URLSearchParams(window.location.search);
const currentQuery = (params.get("q") || "").trim();
const currentId = (params.get("id") || "").trim();
const isFileProtocol = window.location.protocol === "file:";

async function apiGet(endpoint) {
  if (isFileProtocol) return null;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);
    const res = await fetch(endpoint, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[BTH API] Endpoint ${endpoint} tidak terjangkau (${err.message}). Beralih ke data lokal.`);
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

// =========================================================================
// 1. BERANDA (index.html): SKELETON HOLDER + PHOTO LOADER + INSTANT CACHE
// =========================================================================
const grid = document.getElementById("grid");
if (grid) {
  function renderGridSkeleton(count = 5) {
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

  function renderGridArticles(articles) {
    grid.innerHTML = articles.map((item) => {
      const artId = item.id || "art-ppn-cnn-01";
      const kategori = item.category || item.kategori || "Nasional";
      const judul = item.title || item.judul || "Judul Berita";
      const publisher = item.publisher || item.media || "Media Indonesia";
      const timeStr = formatRelativeTime(item.published_at || item.waktu);
      const imageUrl = item.image_url || item.foto;

      return `
        <article class="card">
          <div class="ph">${buildPhotoMarkup(imageUrl, judul)}</div>
          <div class="info">
            <span class="chip">${escapeHtml(kategori)}</span>
            <h3><a href="detail.html?id=${encodeURIComponent(artId)}">${escapeHtml(judul)}</a></h3>
            <div class="meta">${escapeHtml(publisher)} · ${escapeHtml(timeStr)}</div>
          </div>
        </article>
      `;
    }).join("");
    attachImageLoaders(grid);
  }

  async function loadHomepageNews() {
    const cachedArticles = BTHCache.load("homepage_articles");
    if (cachedArticles && cachedArticles.length > 0) {
      renderGridArticles(cachedArticles);
    } else {
      renderGridSkeleton(5);
    }

    const data = await apiGet("/api/v1/news/latest?limit=15");
    if (data && data.articles && data.articles.length > 0) {
      BTHCache.save("homepage_articles", data.articles, 600);
      renderGridArticles(data.articles);
    } else if (!cachedArticles) {
      renderGridArticles(FALLBACK_NEWS);
    }
  }

  loadHomepageNews();
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
const compareSectionElem = document.getElementById("compareSection");
const beritaSectionElem = document.getElementById("beritaSection");
const aiNoteElem = document.getElementById("aiNote");

if (compareTable && aiSummaryElem) {
  function setResultsVisibility(visible) {
    if (compareSectionElem) compareSectionElem.hidden = !visible;
    if (beritaSectionElem) beritaSectionElem.hidden = !visible;
    if (aiNoteElem) aiNoteElem.hidden = !visible;
  }

  function renderSearchSkeleton() {
    setResultsVisibility(true);
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
    setResultsVisibility(false);
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

    if (beritaListElem) {
      if (data.articles && data.articles.length > 0) {
        beritaListElem.innerHTML = data.articles.map((art) => `
          <article class="item">
            <small>${escapeHtml(art.publisher || "Media Daring")}</small>
            <h3><a href="detail.html?id=${encodeURIComponent(art.id)}">${escapeHtml(art.title)}</a></h3>
            <a class="src" href="${escapeHtml(art.url)}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
          </article>
        `).join("");
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

    // Cek cepat di sisi klien untuk topik nyeleneh
    if (isAbsurdTopicClient(currentQuery)) {
      renderEmptyOrInvalidState(ABSURD_TOPIC_MESSAGE);
      return;
    }

    const cacheKey = `search_v2_${currentQuery.toLowerCase()}`;
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

    // Fallback offline jika server tidak terjangkau
    const qLow = currentQuery.toLowerCase();
    const matchedFallback = FALLBACK_NEWS.filter((item) =>
      `${item.judul} ${item.kategori} ${item.full_text}`.toLowerCase().includes(qLow)
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
      beritaListElem.innerHTML = matchedFallback.slice(0, 3).map((art) => `
        <article class="item">
          <small>${escapeHtml(art.media)}</small>
          <h3><a href="detail.html?id=${encodeURIComponent(art.id)}">${escapeHtml(art.judul)}</a></h3>
          <a class="src" href="${escapeHtml(art.url)}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
        </article>
      `).join("");
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

    const katElem = document.getElementById("kategori");
    if (katElem) katElem.textContent = article.category || article.kategori || "Berita";

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

    // Menampilkan HANYA 2-4 paragraf pilihan (ringkas, padat, dan nyaman dibaca)
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

    // Menampilkan RINGKASAN TOPIK TEMATIK
    const aiDetail = document.getElementById("aiSummaryDetail");
    if (aiDetail) {
      const topicText = article.topic_summary || article.ai_summary || (
        `Topik: ${article.category || "Umum"}. Berita ini diklasifikasikan ke dalam ranah ${article.category || "Umum"} berdasarkan fokus pembahasan isu dalam laporan ${article.publisher || article.media}.`
      );
      aiDetail.innerHTML = `<p style="margin-top:0">${escapeHtml(topicText)}</p>`;
    }

    const relatedContainer = document.getElementById("relatedNews");
    if (relatedContainer && relatedArticles && relatedArticles.length > 0) {
      relatedContainer.innerHTML = relatedArticles.map((rel) => `
        <article class="item">
          <small>${escapeHtml(rel.publisher || rel.media || "Media Lain")}</small>
          <h3><a href="detail.html?id=${encodeURIComponent(rel.id)}">${escapeHtml(rel.title || rel.judul)}</a></h3>
          <a class="src" href="${escapeHtml(rel.url)}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
        </article>
      `).join("");
    } else if (relatedContainer) {
      relatedContainer.innerHTML = `<p style="color:var(--muted);font-size:13px;">Belum ada liputan pembanding tambahan untuk artikel ini.</p>`;
    }
  }

  async function loadArticleDetail() {
    const artId = currentId || "art-ppn-cnn-01";
    const cacheKey = `article_v3_${artId}`;

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
