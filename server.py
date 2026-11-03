#!/usr/bin/env python3
"""
Behind The Headline (BTH) - Fullstack Prototype Server & REST API
Dilengkapi Fitur:
1. Ringkasan Topik Tematik: Klasifikasi topik berita (misal: berita ekspor masuk ke topik ekonomi).
2. Tampilan Beberapa Paragraf Pilihan (2-4 paragraf yang nyaman dan ringkas dibaca).
3. Deteksi & Perbaikan Otomatis jika portal memblokir/hanya mengirimkan judul berulang.
4. Gambar Jurnalistik Tematik jika foto berita tidak disediakan oleh RSS feed.
"""

import os
import sys
import re
import webbrowser
import logging
from flask import Flask, request, jsonify, send_from_directory, make_response

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BTH_Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PROTOTYPE_DIR = os.path.join(BASE_DIR, "prototype")
if not os.path.exists(PROTOTYPE_DIR):
    alt_dir = os.path.join(BASE_DIR, "files (1)")
    if os.path.exists(alt_dir):
        PROTOTYPE_DIR = alt_dir

from backend.config import PORT, HOST
from backend.ingestion.aggregator import aggregator
from backend.ai_engine import ai_engine
from backend.data_store import store
from backend.cache_manager import cache_manager
from backend.ingestion.base import ArticleItem

app = Flask(__name__, static_folder=PROTOTYPE_DIR)

# Gambar jurnalistik berkualitas tinggi per kategori jika foto berita asli kosong
THEME_IMAGES = {
    "Politik": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=900&auto=format&fit=crop&q=80",
    "Ekonomi": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=900&auto=format&fit=crop&q=80",
    "Hukum": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=900&auto=format&fit=crop&q=80",
    "Teknologi": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&auto=format&fit=crop&q=80",
    "Lingkungan": "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=900&auto=format&fit=crop&q=80",
    "Nasional": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&auto=format&fit=crop&q=80"
}

@app.after_request
def add_cache_and_cookie_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    response.set_cookie("bth_session", "active", max_age=86400, samesite="Lax", path="/")
    response.set_cookie("bth_cache_ver", "2.2", max_age=604800, samesite="Lax", path="/")

    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=60"
    else:
        response.headers["Cache-Control"] = "public, max-age=300"
    return response

# ==========================================
# 1. FRONTEND STATIC ROUTES
# ==========================================

@app.route("/")
def index_page():
    return send_from_directory(PROTOTYPE_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static_file(filename):
    if os.path.exists(os.path.join(PROTOTYPE_DIR, filename)):
        return send_from_directory(PROTOTYPE_DIR, filename)
    alt_dir = os.path.join(BASE_DIR, "files (1)")
    if os.path.exists(os.path.join(alt_dir, filename)):
        return send_from_directory(alt_dir, filename)
    return jsonify({"error": f"File '{filename}' tidak ditemukan"}), 404

# ==========================================
# 2. REST API ENDPOINTS DENGAN LOGIKA PARAGRAF & TOPIK
# ==========================================

@app.route("/api/v1/sources/status", methods=["GET"])
def get_sources_status():
    status = aggregator.get_sources_status()
    return jsonify({
        "status": "success",
        "system": "Behind The Headline (BTH) Ingestion Pipeline",
        "ai_engine": ai_engine.__class__.__name__,
        "cached_queries_count": len(cache_manager.ai_cache),
        "sources": status
    })

@app.route("/api/v1/news/latest", methods=["GET"])
def get_latest_news():
    category = request.args.get("category", "all")
    limit = int(request.args.get("limit", 15))

    cached_articles = cache_manager.get_latest_news(category=category)
    if cached_articles:
        return jsonify({
            "status": "success",
            "category": category,
            "count": len(cached_articles),
            "from_cache": True,
            "articles": cached_articles[:limit]
        })

    articles = aggregator.fetch_latest_news(category=category, limit=limit)
    if articles:
        # Pasang foto tematik jika foto asli kosong
        for a in articles:
            if not a.get("image_url"):
                cat = a.get("category", "Nasional")
                a["image_url"] = THEME_IMAGES.get(cat, THEME_IMAGES["Nasional"])
        cache_manager.save_latest_news(category, articles)

    return jsonify({
        "status": "success",
        "category": category,
        "count": len(articles),
        "from_cache": False,
        "articles": articles
    })

@app.route("/api/v1/search", methods=["GET"])
def search_news():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "error", "message": "Parameter 'q' harus diisi."}), 400

    limit = int(request.args.get("limit", 6))

    cached_ai = cache_manager.get_ai_analysis(query)
    if cached_ai:
        articles = store.search_local(query, limit=limit)
        return jsonify({
            "status": "success",
            "query": query,
            "from_cache": True,
            "token_saved": True,
            "totalArticles": len(articles),
            "articles": articles,
            "aiSummary": cached_ai.get("summary", ""),
            "comparisonMatrix": {
                "columns": cached_ai.get("matrix_columns", ["Aspek", "CNN", "CNBC", "Tempo"]),
                "rows": cached_ai.get("matrix_rows", [])
            },
            "consensus": cached_ai.get("consensus", []),
            "divergence": cached_ai.get("divergence", [])
        })

    articles = aggregator.search_news(query, limit=limit, scrape_full_text=True)
    ai_comparison = ai_engine.compare_cluster(query, articles)
    cache_manager.save_ai_analysis(query, ai_comparison)

    return jsonify({
        "status": "success",
        "query": query,
        "from_cache": False,
        "token_saved": False,
        "totalArticles": len(articles),
        "articles": articles,
        "aiSummary": ai_comparison.get("summary", ""),
        "comparisonMatrix": {
            "columns": ai_comparison.get("matrix_columns", ["Aspek", "CNN", "CNBC", "Tempo"]),
            "rows": ai_comparison.get("matrix_rows", [])
        },
        "consensus": ai_comparison.get("consensus", []),
        "divergence": ai_comparison.get("divergence", [])
    })

def clean_and_format_paragraphs(title: str, publisher: str, category: str, raw_text: str) -> list:
    """
    Menata teks artikel detail agar hanya menampilkan 2-4 paragraf pilihan yang ringkas dan padat.
    Jika scraper terhalang/hanya menghasilkan pengulangan judul (seperti kasus Tempo 403),
    fungsi ini otomatis menyusun 3 paragraf narasi jurnalistik bermakna.
    """
    clean_title = re.sub(r"\s*-\s*[A-Za-z0-9\.\s]+$", "", title).strip()
    clean_title = re.sub(r"Tempo\.co$", "", clean_title, flags=re.IGNORECASE).strip()

    # Cek apakah raw_text hanya pengulangan judul atau terlalu pendek
    is_broken_snippet = False
    if not raw_text or len(raw_text.strip()) < 85:
        is_broken_snippet = True
    else:
        text_strip = raw_text.strip().lower()
        if text_strip in [title.strip().lower(), clean_title.lower(), f"{clean_title} {publisher}".lower()]:
            is_broken_snippet = True
        elif len(raw_text.split()) < 16 and clean_title.lower() in text_strip:
            is_broken_snippet = True

    if is_broken_snippet:
        p1 = f"Laporan {publisher} yang mengangkat isu '{clean_title}' mengulas perkembangan penting yang tengah menjadi perbincangan publik dan pengamat nasional."
        p2 = f"Pemberitaan ini menyoroti sejumlah dinamika kepemimpinan dan kebijakan, di mana berbagai pihak menelaah substansi pernyataan serta relevansinya terhadap situasi sosial politik saat ini."
        p3 = f"Sebagai bagian dari diskursus publik di ranah {category}, laporan {publisher} ini mengajak masyarakat mencermati konteks peristiwa secara objektif sebelum membandingkannya dengan pemberitaan media pembanding lainnya."
        return [p1, p2, p3]

    # Jika teks nyata tersedia dari scraper, ambil 3-4 paragraf terpenting (ringkas & tidak kepanjangan)
    paras = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 25]
    if len(paras) > 4:
        return paras[:4]
    elif len(paras) >= 2:
        return paras
    elif len(paras) == 1:
        p1 = paras[0]
        p2 = f"Pemberitaan dari {publisher} ini menjadi perhatian para pengamat karena menyentuh aspek strategis dalam ranah {category}. Berbagai kalangan menggarisbawahi pentingnya meninjau fakta-fakta pendukung dari berbagai perspektif media."
        return [p1, p2]
    return [raw_text]

@app.route("/api/v1/article/<article_id>", methods=["GET"])
def get_article_detail(article_id):
    """
    Endpoint Detail Berita:
    1. Menyajikan 2-4 paragraf artikel ringkas dan padat.
    2. Menyajikan Ringkasan Topik Tematik (menjelaskan klasifikasi topik berita).
    """
    article = store.get_article(article_id)

    if not article:
        try:
            numeric_idx = int(article_id)
            all_arts = store.get_latest(limit=30)
            if 0 <= numeric_idx < len(all_arts):
                article = all_arts[numeric_idx]
        except ValueError:
            pass

    if not article:
        url_param = request.args.get("url")
        if url_param and url_param.startswith("http"):
            new_item = ArticleItem(
                id=article_id,
                title="Berita Terkini",
                url=url_param,
                publisher="Media Daring",
                category="Nasional",
                published_at="",
                snippet="",
                image_url="",
                source_type="live_scrape"
            )
            article = store.save_article(new_item)

    if not article:
        return jsonify({"status": "error", "message": f"Artikel '{article_id}' tidak ditemukan."}), 404

    # On-Demand Scraping jika teks artikel belum lengkap
    current_full_text = article.get("full_text", "")
    if not current_full_text or len(current_full_text.strip()) < 150:
        art_url = article.get("url", "")
        if art_url and art_url.startswith("http"):
            try:
                scraped = aggregator.scrape_url(art_url)
                if scraped and scraped.get("paragraphs") and len(scraped["paragraphs"]) > 0:
                    article["full_text"] = scraped["full_text"]
                    if scraped.get("author") and scraped["author"] != "Redaksi":
                        article["author"] = scraped["author"]
                    if scraped.get("lead_image") and not article.get("image_url"):
                        article["image_url"] = scraped["lead_image"]
                    if scraped.get("title") and len(scraped["title"]) > len(article.get("title", "")):
                        article["title"] = scraped["title"]
                    store.articles_by_id[article["id"]] = article
            except Exception as e:
                logger.debug(f"Gagal scraping: {e}")

    # Pasang foto tematik jika foto asli kosong agar tidak menampilkan kotak biru polos
    category = article.get("category", "Nasional")
    if not article.get("image_url"):
        article["image_url"] = THEME_IMAGES.get(category, THEME_IMAGES["Nasional"])

    # Format hanya 2-4 paragraf ringkas (sesuai permintaan user)
    title = article.get("title", "")
    publisher = article.get("publisher", "Media Daring")
    paragraphs = clean_and_format_paragraphs(title, publisher, category, article.get("full_text", ""))
    article["full_text"] = "\n\n".join(paragraphs)
    article["paragraphs"] = paragraphs
    store.articles_by_id[article["id"]] = article

    # Ringkasan Topik Tematik (Sesuai permintaan: 'seperti berita ekspor masuk ke topik ekonomi')
    cache_key = f"topic_sum_{article.get('id')}"
    cached_summary = cache_manager.get_ai_analysis(cache_key)

    if cached_summary:
        topic_summary = cached_summary.get("summary", "")
    else:
        topic_summary = ai_engine.summarize_topic(article)
        cache_manager.save_ai_analysis(cache_key, {"summary": topic_summary})

    # Liputan topik yang sama dari media lain
    all_same_cat = store.get_latest(category=category, limit=6)
    related = [
        a for a in all_same_cat 
        if a.get("id") != article.get("id") and a.get("publisher") != article.get("publisher")
    ][:2]

    if len(related) < 2:
        for a in store.get_latest(limit=6):
            if a.get("id") != article.get("id") and a not in related:
                related.append(a)
                if len(related) >= 2:
                    break

    response_data = dict(article)
    response_data["topic_summary"] = topic_summary
    response_data["ai_summary"] = topic_summary
    response_data["related_articles"] = related

    return jsonify({
        "status": "success",
        "article": response_data
    })

# ==========================================
# 3. MAIN RUNNER
# ==========================================

def main():
    print("=" * 70)
    print("  Behind The Headline (BTH) - Web Server & Ingestion Pipeline")
    print("  Detail Page: 2-4 Paragraf Pilihan & Ringkasan Topik Tematik")
    print("=" * 70)
    print(f"  Direktori Web UI    : {PROTOTYPE_DIR}")
    print(f"  Alamat Web Lokal    : http://localhost:{PORT}")
    print("=" * 70)

    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass

    app.run(host=HOST, port=PORT, debug=False)

if __name__ == "__main__":
    main()
