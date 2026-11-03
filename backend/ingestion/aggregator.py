"""
Modul Ingestion Aggregator Terpadu (Behind The Headline)
Mengorkestrasikan penarikan berita dari 4 sumber utama:
1. Google News RSS Feed (Real-Time Breaking News Seluruh Media Indonesia)
2. RSS Feed Resmi Media Indonesia (CNN Indonesia, CNBC, Antara)
3. API Unofficial Berita Indonesia (Berita Indo API & api-berita-indonesia)
4. Provider API Global (NewsAPI, Currents, MediaStack)
Dilanjutkan dengan Full-Text Scraping dan penyimpanan ke Data Store.
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.ingestion.base import ArticleItem
from backend.ingestion.indo_news_api import IndoNewsAPISource
from backend.ingestion.google_news_rss import GoogleNewsRSSSource
from backend.ingestion.media_rss import MediaRSSSource
from backend.ingestion.global_news_api import GlobalNewsAPISource
from backend.scraper.full_text_extractor import FullTextExtractor
from backend.data_store import store

logger = logging.getLogger("NewsAggregator")

class NewsAggregator:
    """Orkestrator Ingestion dan Scraping Berita Antarmedia."""

    def __init__(self):
        self.google_rss = GoogleNewsRSSSource()
        self.media_rss = MediaRSSSource()
        self.indo_api = IndoNewsAPISource()
        self.global_api = GlobalNewsAPISource()
        self.scraper = FullTextExtractor()

    def get_sources_status(self) -> Dict[str, Any]:
        """Memeriksa status konfigurasi keempat provider berita."""
        return {
            "source_1_unofficial_indo_api": {
                "name": "Berita Indo API & api-berita-indonesia",
                "status": "ready (upstream vercel free tier)",
                "requires_key": False
            },
            "source_2_google_news_rss": {
                "name": "Google News RSS Feed",
                "status": "active_realtime",
                "requires_key": False,
                "feature": "Cakupan seluruh media Indonesia + Breaking News Terkini + Redirect Resolver"
            },
            "source_3_global_apis": {
                "name": "NewsAPI, Currents, MediaStack",
                "status": "active" if self.global_api.has_active_keys() else "key_optional",
                "requires_key": True
            },
            "source_4_official_media_rss": {
                "name": "Official Media Feeds (CNN, CNBC, Antara)",
                "status": "active_realtime",
                "requires_key": False,
                "publishers": ["CNN Indonesia", "CNBC Indonesia", "Antara News"]
            }
        }

    def fetch_latest_news(self, category: str = "all", limit: int = 15) -> List[Dict[str, Any]]:
        """
        Mengambil berita TERKINI LIVE hari ini dari Google News RSS dan RSS resmi (CNN, CNBC, Antara).
        Jika offline atau jaringan terputus, sistem menggunakan dataset kurasi lokal sebagai fallback.
        """
        live_articles: List[ArticleItem] = []

        # Ambil secara paralel dari Google News RSS (Top Breaking News) dan Media RSS Resmi (CNN, CNBC, Antara)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.google_rss.fetch_latest, category, limit): "google_rss",
                executor.submit(self.media_rss.fetch_latest, category, limit // 2): "media_rss",
            }
            for fut in as_completed(futures):
                src_name = futures[fut]
                try:
                    res = fut.result()
                    if res:
                        live_articles.extend(res)
                except Exception as e:
                    logger.debug(f"Panggilan {src_name} gagal: {e}")

        # Jika berhasil mendapatkan berita live dari internet
        if live_articles:
            saved = []
            seen_titles = set()
            for item in live_articles:
                norm_title = item.title.strip().lower()
                if norm_title in seen_titles:
                    continue
                seen_titles.add(norm_title)

                # Simpan ke data store (memperbarui cache runtime)
                art_dict = store.save_article(item)
                saved.append(art_dict)

            logger.info(f"Berhasil menarik {len(saved)} berita terkini live dari Google News & Media RSS.")
            return saved[:limit]

        # Jika offline / sandbox / gagal koneksi, gunakan dataset kurasi lokal
        logger.info("Menggunakan dataset cache lokal untuk berita terbaru.")
        return store.get_latest(category=category, limit=limit)

    def search_news(self, query: str, limit: int = 10, scrape_full_text: bool = True) -> List[Dict[str, Any]]:
        """
        Alur Utama Pencarian:
        1. Ingestion metadata dari Google News RSS (spesifik query kata kunci)
        2. Fallback ke Unofficial API & Global API
        3. Full-Text Scraping artikel lengkap menggunakan User-Agent rotation
        4. Simpan artikel ke Data Store
        """
        found_items: List[ArticleItem] = []

        # 1. Jalankan pencarian ke Google News RSS (sumber terlengkap untuk query spesifik di Indonesia)
        try:
            google_results = self.google_rss.search(query, limit=limit)
            if google_results:
                found_items.extend(google_results)
        except Exception as e:
            logger.debug(f"Pencarian Google RSS gagal: {e}")

        if len(found_items) < 3:
            try:
                indo_results = self.indo_api.search(query, limit=limit)
                if indo_results:
                    found_items.extend(indo_results)
            except Exception as e:
                logger.debug(f"Pencarian Indo API gagal: {e}")

        if self.global_api.has_active_keys() and len(found_items) < 3:
            try:
                glb_results = self.global_api.search(query, limit=limit)
                if glb_results:
                    found_items.extend(glb_results)
            except Exception as e:
                logger.debug(f"Pencarian Global API gagal: {e}")

        # 2. Jika live search berhasil menemukan artikel
        if found_items:
            processed = []
            seen_urls = set()
            for item in found_items[:limit]:
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)

                full_text = ""
                # Langkah 2: Scraping teks penuh jika URL dapat diakses
                if scrape_full_text and item.url.startswith("http"):
                    try:
                        scrape_data = self.scraper.fetch_article(item.url)
                        if scrape_data.get("full_text"):
                            full_text = scrape_data["full_text"]
                            if scrape_data.get("author"):
                                item.author = scrape_data["author"]
                            if scrape_data.get("lead_image") and not item.image_url:
                                item.image_url = scrape_data["lead_image"]
                    except Exception as e:
                        logger.debug(f"Gagal scraping teks penuh {item.url}: {e}")

                art_dict = store.save_article(item, full_text=full_text)
                processed.append(art_dict)
            return processed

        # 3. Fallback: Cari di dataset lokal jika live request kosong atau offline
        logger.info(f"Menggunakan pencarian dataset lokal untuk kata kunci '{query}'")
        return store.search_local(query, limit=limit)

    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scraping langsung sebuah URL berita."""
        return self.scraper.fetch_article(url)

# Singleton aggregator instance
aggregator = NewsAggregator()
