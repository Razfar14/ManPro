"""
Sumber 3: Provider API Berita Global (Freemium / Pendaftaran API Key)
Mendukung:
- NewsAPI.org (https://newsapi.org/v2/everything?q={query}&language=id)
- Currents API (https://api.currentsapi.services/v1/search?keywords={query}&language=id)
- MediaStack API (http://api.mediastack.com/v1/news?access_key={key}&countries=id&keywords={query})

Jika API Key belum diatur di sistem, modul ini memberikan log status informatif tanpa menyebabkan crash.
"""

import hashlib
import logging
from typing import List
import requests

from backend.ingestion.base import BaseIngestionSource, ArticleItem
from backend.config import NEWSAPI_KEY, CURRENTS_API_KEY, MEDIASTACK_KEY, DEFAULT_TIMEOUT

logger = logging.getLogger("GlobalNewsAPISource")

class GlobalNewsAPISource(BaseIngestionSource):
    name = "Global News APIs (NewsAPI, Currents, MediaStack)"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def _generate_id(self, url: str) -> str:
        return "glb-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:10]

    def has_active_keys(self) -> bool:
        return bool(NEWSAPI_KEY or CURRENTS_API_KEY or MEDIASTACK_KEY)

    def search(self, query: str, limit: int = 10) -> List[ArticleItem]:
        articles: List[ArticleItem] = []

        # 1. Coba NewsAPI.org jika API Key tersedia
        if NEWSAPI_KEY:
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query,
                    "language": "id",
                    "pageSize": limit,
                    "apiKey": NEWSAPI_KEY
                }
                res = self.session.get(url, params=params, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("articles", []):
                        art_url = item.get("url", "")
                        if not art_url:
                            continue
                        articles.append(ArticleItem(
                            id=self._generate_id(art_url),
                            title=item.get("title", ""),
                            url=art_url,
                            publisher=item.get("source", {}).get("name", "Media Global"),
                            category="Berita",
                            published_at=item.get("publishedAt", ""),
                            snippet=item.get("description", "") or "",
                            image_url=item.get("urlToImage", "") or "",
                            source_type="global_api",
                            author=item.get("author", "Redaksi")
                        ))
                    if articles:
                        return articles[:limit]
            except Exception as e:
                logger.warning(f"Error memanggil NewsAPI: {e}")

        # 2. Coba Currents API jika API Key tersedia
        if CURRENTS_API_KEY and len(articles) < limit:
            try:
                url = "https://api.currentsapi.services/v1/search"
                params = {
                    "keywords": query,
                    "language": "id",
                    "apiKey": CURRENTS_API_KEY
                }
                res = self.session.get(url, params=params, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("news", []):
                        art_url = item.get("url", "")
                        if not art_url:
                            continue
                        articles.append(ArticleItem(
                            id=self._generate_id(art_url),
                            title=item.get("title", ""),
                            url=art_url,
                            publisher=item.get("author", "Media Online"),
                            category=item.get("category", ["Umum"])[0] if item.get("category") else "Umum",
                            published_at=item.get("published", ""),
                            snippet=item.get("description", "") or "",
                            image_url=item.get("image", "") or "",
                            source_type="global_api",
                            author=item.get("author", "Redaksi")
                        ))
            except Exception as e:
                logger.warning(f"Error memanggil Currents API: {e}")

        # 3. Coba MediaStack API jika API Key tersedia
        if MEDIASTACK_KEY and len(articles) < limit:
            try:
                url = "http://api.mediastack.com/v1/news"
                params = {
                    "access_key": MEDIASTACK_KEY,
                    "countries": "id",
                    "keywords": query,
                    "limit": limit
                }
                res = self.session.get(url, params=params, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("data", []):
                        art_url = item.get("url", "")
                        if not art_url:
                            continue
                        articles.append(ArticleItem(
                            id=self._generate_id(art_url),
                            title=item.get("title", ""),
                            url=art_url,
                            publisher=item.get("source", "Media Indonesia"),
                            category=item.get("category", "General"),
                            published_at=item.get("published_at", ""),
                            snippet=item.get("description", "") or "",
                            image_url=item.get("image", "") or "",
                            source_type="global_api",
                            author=item.get("author", "Redaksi")
                        ))
            except Exception as e:
                logger.warning(f"Error memanggil MediaStack API: {e}")

        return articles[:limit]

    def fetch_latest(self, category: str = "all", limit: int = 10) -> List[ArticleItem]:
        return self.search("Indonesia", limit=limit)
