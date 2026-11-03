/**
 * Behind The Headline (BTH) - Client Controller & Cache Manager
 * Pembaruan:
 * 1. Halaman Detail: Menampilkan hanya 2-4 paragraf pilihan yang padat dan nyaman dibaca.
 * 2. Ringkasan Topik Tematik: Menjelaskan klasifikasi topik (misal ekspor masuk ke topik ekonomi).
 * 3. Caching 2 Lapis (Cookie & LocalStorage) untuk load instan.
 */

// =========================================================================
// 0. MODUL CLIENT CACHE & COOKIE MANAGER
// =========================================================================
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
    topic_summary: "Topik: Ekonomi & Fiskal. Berita ini diklasifikasikan ke dalam ranah Ekonomi & Fiskal karena membahas penyesuaian tarif PPN yang memengaruhi penerimaan APBN dan dunia usaha.",
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
    topic_summary: "Topik: Ekonomi & Pasar Ritel. Berita ini diklasifikasikan ke dalam topik Ekonomi & Pasar Ritel karena menyoroti kekhawatiran asosiasi pengusaha terhadap pelemahan konsumsi domestik.",
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
    topic_summary: "Topik: Ekonomi & Kesejahteraan Buruh. Berita ini diklasifikasikan ke dalam ranah Ekonomi & Kesejahteraan Buruh karena mengulas beban hidup kelas menengah dan penolakan serikat pekerja.",
    full_text: "Jakarta, Tempo.co -- Kenaikan tarif PPN 12% mendapatkan sorotan tajam dari kalangan ekonom independen dan organisasi serikat buruh. Celios menilai kebijakan ini tidak tepat waktu di tengah penurunan jumlah penduduk kelas menengah.\n\nMenurut kajian Celios, kenaikan PPN 12% dapat meningkatkan biaya hidup rata-rata keluarga urban sebesar 2,8% hingga 3,5%."
  }
];

const params = new URLSearchParams(window.location.search);
const currentQuery = params.get("q") || "";
const currentId = params.get("id") || "";
const isFileProtocol = window.location.protocol === "file:";

async function apiGet(endpoint) {
  if (isFileProtocol) return null;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
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
// 1. BERANDA (index.html): INSTANT CACHE + STALE-REVALIDATE
// =========================================================================
const grid = document.getElementById("grid");
if (grid) {
  function renderGridArticles(articles) {
    grid.innerHTML = articles.map(item => {
      const artId = item.id || "art-ppn-cnn-01";
      const kategori = item.category || item.kategori || "Nasional";
      const judul = item.title || item.judul || "Judul Berita";
      const publisher = item.publisher || item.media || "Media Indonesia";
      const timeStr = formatRelativeTime(item.published_at || item.waktu);
      const imageUrl = item.image_url || item.foto;

      const photoHtml = imageUrl 
        ? `<img src="${imageUrl}" alt="${judul}" loading="lazy" onerror="this.style.display='none'">`
        : `<span>Foto Berita</span>`;

      return `
        <article class="card">
          <div class="ph">${photoHtml}</div>
          <div class="info">
            <span class="chip">${kategori}</span>
            <h3><a href="detail.html?id=${encodeURIComponent(artId)}">${judul}</a></h3>
            <div class="meta">${publisher} · ${timeStr}</div>
          </div>
        </article>
      `;
    }).join("");
  }

  async function loadHomepageNews() {
    const cachedArticles = BTHCache.load("homepage_articles");
    if (cachedArticles && cachedArticles.length > 0) {
      renderGridArticles(cachedArticles);
    } else {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 30px; color: var(--muted);" class="loading-pulse">Mengambil berita terkini langsung dari Google News & Portal Berita...</div>`;
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
// 2. HASIL PENCARIAN (hasil.html): ZERO TOKEN COST PADA PENCARIAN BERULANG
// =========================================================================
const qInput = document.getElementById("q");
if (qInput && currentQuery) {
  qInput.value = currentQuery;
}

if (currentQuery) {
  document.querySelectorAll(".nav li a").forEach(link => {
    if (link.textContent.trim().toLowerCase() === currentQuery.trim().toLowerCase()) {
      link.classList.add("on");
    } else if (link.getAttribute("href") === "index.html" && currentQuery) {
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

if (compareTable && aiSummaryElem) {
  function renderSearchData(data, fromClientCache = false) {
    const cachePill = fromClientCache || data.from_cache 
      ? ` <span class="chip" style="background:#d4edda; color:#155724; font-size:10px; margin-left:8px;">⚡ Dimuat dari Cache (Hemat Token AI)</span>`
      : "";
    
    aiSummaryElem.innerHTML = `${data.aiSummary || "Ringkasan komparatif berhasil dianalisis."}${cachePill}`;

    const matrix = data.comparisonMatrix;
    if (matrix && matrix.rows) {
      const thead = document.getElementById("compareHead");
      const tbody = document.getElementById("compareBody");

      if (thead && matrix.columns) {
        thead.innerHTML = `<tr>${matrix.columns.map(col => `<th>${col}</th>`).join("")}</tr>`;
      }

      if (tbody) {
        tbody.innerHTML = matrix.rows.map(row => `
          <tr>
            <td>${row.aspek || "-"}</td>
            <td>${row.cnn || "-"}</td>
            <td>${row.cnbc || "-"}</td>
            <td>${row.tempo || "-"}</td>
          </tr>
        `).join("");
      }
    }

    if (beritaListElem && data.articles && data.articles.length > 0) {
      beritaListElem.innerHTML = data.articles.map(art => `
        <article class="item">
          <small>${art.publisher || "Media Daring"}</small>
          <h3><a href="detail.html?id=${encodeURIComponent(art.id)}">${art.title}</a></h3>
          <a class="src" href="${art.url}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
        </article>
      `).join("");
    }
  }

  async function loadSearchResults() {
    const query = currentQuery || "Kenaikan Tarif PPN";
    document.title = `${query} — Behind The Headline`;

    const cacheKey = `search_${query.toLowerCase()}`;
    const cachedData = BTHCache.load(cacheKey);

    if (cachedData) {
      renderSearchData(cachedData, true);
      return;
    }

    aiSummaryElem.innerHTML = `<span class="loading-pulse">AI sedang menganalisis berita '${query}' dari berbagai portal media...</span>`;

    const data = await apiGet(`/api/v1/search?q=${encodeURIComponent(query)}&limit=6`);

    if (data && data.status === "success") {
      BTHCache.save(cacheKey, data, 86400 * 7);
      renderSearchData(data, false);
    } else {
      aiSummaryElem.textContent = "Pemberitaan mengenai penyesuaian tarif PPN 12% menunjukkan perbedaan sudut pandang antarmedia. CNN Indonesia menitikberatkan pada kepatuhan regulasi UU HPP, CNBC Indonesia menyoroti kekhawatiran pengusaha ritel terhadap pelemahan daya beli, sementara Tempo menyoroti beban kelas menengah.";
      const tbody = document.getElementById("compareBody");
      if (tbody) {
        tbody.innerHTML = `
          <tr><td>Data angka</td><td>Tarif PPN 12%; proyeksi Rp 70-80 triliun</td><td>Koreksi penjualan 1,2%; inflasi 0,3-0,5%</td><td>Biaya hidup urban 2,8-3,5%</td></tr>
          <tr><td>Narasumber</td><td>Menteri Keuangan Sri Mulyani</td><td>Ketua Aprindo Roy Nicholas Mandey</td><td>Direktur Celios Bhima Yudhistira</td></tr>
          <tr><td>Fokus berita</td><td>Amanat regulasi UU HPP</td><td>Sentimen ritel & pasar modal</td><td>Daya beli kelas menengah</td></tr>
        `;
      }
      if (beritaListElem) {
        beritaListElem.innerHTML = FALLBACK_NEWS.slice(0, 3).map(art => `
          <article class="item">
            <small>${art.media}</small>
            <h3><a href="detail.html?id=${encodeURIComponent(art.id)}">${art.judul}</a></h3>
            <a class="src" href="${art.url}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
          </article>
        `).join("");
      }
    }
  }

  loadSearchResults();
}

// =========================================================================
// 3. DETAIL BERITA (detail.html): MENAMPILKAN BEBERAPA PARAGRAF & RINGKASAN TOPIK
// =========================================================================
const detailJudul = document.getElementById("judul");
if (detailJudul) {
  function renderArticleDetail(article, relatedArticles) {
    detailJudul.textContent = article.title || article.judul;
    document.title = `${article.title || article.judul} — Behind The Headline`;

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
    if (fotoContainer && imgUrl) {
      fotoContainer.innerHTML = `<img src="${imgUrl}" alt="${article.title || article.judul}" onerror="this.parentElement.innerHTML='Foto Berita'">`;
    }

    // Menampilkan HANYA 2-4 paragraf pilihan (ringkas, padat, dan nyaman dibaca)
    const isiContainer = document.getElementById("isiBerita");
    if (isiContainer) {
      let paragraphs = [];
      if (article.paragraphs && Array.isArray(article.paragraphs) && article.paragraphs.length > 0) {
        paragraphs = article.paragraphs;
      } else if (article.full_text) {
        paragraphs = article.full_text.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 20);
      }
      
      // Batasi maksimal 4 paragraf agar tidak kepanjangan
      if (paragraphs.length > 4) {
        paragraphs = paragraphs.slice(0, 4);
      } else if (paragraphs.length === 0) {
        paragraphs = [article.snippet || "Paragraf artikel sedang disiapkan oleh sistem."];
      }

      isiContainer.innerHTML = paragraphs.map(p => `<p>${p}</p>`).join("");
    }

    const srcLink = document.getElementById("linkSumberAsli");
    if (srcLink && (article.url || article.link)) {
      srcLink.href = article.url || article.link;
    }

    // Menampilkan RINGKASAN TOPIK TEMATIK (misal: berita ekspor masuk ke topik ekonomi)
    const aiDetail = document.getElementById("aiSummaryDetail");
    if (aiDetail) {
      const topicText = article.topic_summary || article.ai_summary || (
        `Topik: ${article.category || 'Umum'}. Berita ini diklasifikasikan ke dalam ranah ${article.category || 'Umum'} berdasarkan fokus pembahasan isu dalam laporan ${article.publisher || article.media}.`
      );
      aiDetail.innerHTML = topicText;
    }

    const relatedContainer = document.getElementById("relatedNews");
    if (relatedContainer && relatedArticles.length > 0) {
      relatedContainer.innerHTML = relatedArticles.map(rel => `
        <article class="item">
          <small>${rel.publisher || rel.media || "Media Lain"}</small>
          <h3><a href="detail.html?id=${encodeURIComponent(rel.id)}">${rel.title || rel.judul}</a></h3>
          <a class="src" href="${rel.url}" target="_blank" rel="noopener noreferrer">Baca di sumber asli →</a>
        </article>
      `).join("");
    }
  }

  async function loadArticleDetail() {
    const artId = currentId || "art-ppn-cnn-01";
    const cacheKey = `article_v2_${artId}`;

    const cachedArticleData = BTHCache.load(cacheKey);
    if (
      cachedArticleData &&
      cachedArticleData.article &&
      cachedArticleData.article.topic_summary
    ) {
      renderArticleDetail(cachedArticleData.article, cachedArticleData.related || []);
      return;
    }

    const isiContainer = document.getElementById("isiBerita");
    if (isiContainer) {
      isiContainer.innerHTML = `<p class="loading-pulse" style="color:var(--muted)">Menyiapkan paragraf pilihan dan ringkasan topik...</p>`;
    }

    const data = await apiGet(`/api/v1/article/${encodeURIComponent(artId)}`);
    if (data && data.status === "success" && data.article) {
      BTHCache.save(cacheKey, { article: data.article, related: data.article.related_articles || [] }, 86400 * 7);
      renderArticleDetail(data.article, data.article.related_articles || []);
    } else {
      const fallbackArt = FALLBACK_NEWS.find(a => a.id === artId) || FALLBACK_NEWS[0];
      const fallbackRel = FALLBACK_NEWS.filter(a => a.id !== fallbackArt.id).slice(0, 2);
      renderArticleDetail(fallbackArt, fallbackRel);
    }
  }

  loadArticleDetail();
}
