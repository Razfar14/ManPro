"""
Sumber 1: API Unofficial Berita Indonesia (Open Source & Gratis)
Mengintegrasikan:
1. Berita Indo API (by satriaana) -> https://berita-indo-api-two.vercel.app/v1
2. Indonesia News API (by api-berita-indonesia) -> https://api-berita-indonesia.vercel.app
Mendukung portal: CNN Indonesia, CNBC Indonesia, Tempo, Republika, Antara, Kumparan.
"""

import hashlib
import logging
from typing import List
import requests

from backend.ingestion.base import BaseIngestionSource, ArticleItem
from backend.scraper.user_agents import get_request_headers
from backend.config import BERITA_INDO_API_BASE, API_BERITA_INDONESIA_BASE, DEFAULT_TIMEOUT

logger = logging.getLogger("IndoNewsAPISource")

class IndoNewsAPISource(BaseIngestionSource):
    name = "Unofficial Indonesian News API"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def _generate_id(self, url: str) -> str:
        return "art-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:10]

    def fetch_latest(self, category: str = "all", limit: int = 10) -> List[ArticleItem]:
        """
        Mengambil berita terkini dari portal CNN, CNBC, dan Tempo.
        """
        articles: List[ArticleItem] = []
        sources = [
            ("cnn", "CNN Indonesia", f"{API_BERITA_INDONESIA_BASE}/cnn/terbaru/"),
            ("cnbc", "CNBC Indonesia", f"{API_BERITA_INDONESIA_BASE}/cnbc/terbaru/"),
            ("tempo", "Tempo", f"{API_BERITA_INDONESIA_BASE}/tempo/nasional/")
        ]

        for code, publisher, url in sources:
            try:
                headers = get_request_headers()
                res = self.session.get(url, headers=headers, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    posts = data.get("data", {}).get("posts", [])
                    for p in posts[:limit // len(sources) + 1]:
                        link = p.get("link", "")
                        if not link:
                            continue
                        item = ArticleItem(
                            id=self._generate_id(link),
                            title=p.get("title", "").strip(),
                            url=link,
                            publisher=publisher,
                            category=p.get("category", category if category != "all" else "Umum"),
                            published_at=p.get("pubDate", ""),
                            snippet=p.get("description", "").strip(),
                            image_url=p.get("thumbnail", {}).get("large", "") if isinstance(p.get("thumbnail"), dict) else (p.get("thumbnail") or ""),
                            source_type="unofficial_api"
                        )
                        articles.append(item)
            except Exception as e:
                logger.warning(f"Gagal mengambil feed {publisher} dari {url}: {e}")

        # Fallback coba Berita Indo API (satriaana) jika belum cukup data
        if len(articles) < 3:
            alt_endpoints = [
                ("CNN Indonesia", f"{BERITA_INDO_API_BASE}/cnn-news"),
                ("CNBC Indonesia", f"{BERITA_INDO_API_BASE}/cnbc-news"),
                ("Tempo", f"{BERITA_INDO_API_BASE}/tempo-news")
            ]
            for pub, ep in alt_endpoints:
                try:
                    res = self.session.get(ep, headers=get_request_headers(), timeout=self.timeout)
                    if res.status_code == 200:
                        data = res.json().get("data", [])
                        for p in data[:3]:
                            link = p.get("link", "")
                            if link and not any(a.url == link for a in articles):
                                articles.append(ArticleItem(
                                    id=self._generate_id(link),
                                    title=p.get("title", ""),
                                    url=link,
                                    publisher=pub,
                                    category="Ekonomi" if "cnbc" in ep else "Nasional",
                                    published_at=p.get("isoDate", ""),
                                    snippet=p.get("contentSnippet", ""),
                                    image_url=p.get("image", {}).get("small", "") if isinstance(p.get("image"), dict) else "",
                                    source_type="unofficial_api"
                                ))
                except Exception as e:
                    logger.debug(f"Gagal endpoint cadangan {ep}: {e}")

        return articles[:limit]

    def search(self, query: str, limit: int = 10) -> List[ArticleItem]:
        """
        Pencarian berita: karena unofficial API umumnya berupa endpoint feed kategori,
        metode ini mengambil feed terbaru dan memfilter artikel berdasarkan kesesuaian kata kunci.
        """
        all_articles = self.fetch_latest(limit=30)
        query_lower = query.lower()
        matched = []
        for art in all_articles:
            if (query_lower in art.title.lower()) or (query_lower in art.snippet.lower()):
                matched.append(art)
        return matched[:limit]
