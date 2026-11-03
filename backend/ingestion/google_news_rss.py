"""
Sumber 2: Google News RSS Feed (Gratis, Bebas API Key, & Real-Time)
URL Format Top Headlines: https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id
URL Format Search: https://news.google.com/rss/search?q={KATA_KUNCI}&hl=id&gl=ID&ceid=ID:id
Mencakup seluruh portal berita daring di Indonesia (Detik, Kompas, CNN, CNBC, Tempo, Antara, Kumparan).
Dilengkapi resolusi URL redirect Google ke portal asli penerbit.
"""

import base64
import hashlib
import logging
import re
import urllib.parse
from typing import List, Optional
import xml.etree.ElementTree as ET
import requests

from backend.ingestion.base import BaseIngestionSource, ArticleItem
from backend.scraper.user_agents import get_request_headers
from backend.config import GOOGLE_NEWS_RSS_BASE, GOOGLE_NEWS_TOP_RSS, DEFAULT_TIMEOUT

logger = logging.getLogger("GoogleNewsRSSSource")

class GoogleNewsRSSSource(BaseIngestionSource):
    name = "Google News RSS"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def _generate_id(self, url: str) -> str:
        return "gn-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:10]

    def _resolve_google_url(self, google_url: str) -> str:
        """
        Mengekstrak URL portal penerbit asli dari Google News redirect link.
        """
        # Coba decode cepat dari payload base64 token CBMi...
        try:
            match = re.search(r"articles/([A-Za-z0-9_-]+)", google_url)
            if match:
                token = match.group(1)
                token += "=" * ((4 - len(token) % 4) % 4)
                decoded_bytes = base64.urlsafe_b64decode(token.encode("ascii"))
                url_match = re.search(rb"https?://[^\x00-\x1f\x7f-\xff\s\"'<>\\]+", decoded_bytes)
                if url_match:
                    extracted = url_match.group(0).decode("utf-8", errors="ignore")
                    if "http" in extracted and len(extracted) > 10 and "google" not in extracted:
                        return extracted
        except Exception:
            pass

        # Fallback coba resolve via HTTP HEAD singkat
        try:
            res = self.session.head(
                google_url,
                headers=get_request_headers(),
                allow_redirects=True,
                timeout=2.5
            )
            if res.url and "news.google.com" not in res.url:
                return res.url
        except Exception:
            pass

        return google_url

    def _parse_xml_items(self, xml_content: bytes, default_category: str = "Nasional", limit: int = 15) -> List[ArticleItem]:
        articles: List[ArticleItem] = []
        try:
            root = ET.fromstring(xml_content)
            items = root.findall(".//channel/item")

            for item in items[:limit]:
                raw_title = item.findtext("title", "").strip()
                google_link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()
                description = item.findtext("description", "").strip()

                if not raw_title or not google_link:
                    continue

                # Ekstraksi Publisher dari judul Google News ("Judul Berita - Nama Media")
                publisher = "Media Berita"
                title = raw_title
                source_elem = item.find("source")
                if source_elem is not None and source_elem.text:
                    publisher = source_elem.text.strip()
                    if f" - {publisher}" in title:
                        title = title.replace(f" - {publisher}", "").strip()
                elif " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    publisher = parts[1].strip()

                clean_snippet = re.sub(r"<[^>]+>", "", description).strip()
                clean_snippet = re.sub(r"&nbsp;|&quot;|&amp;", " ", clean_snippet).strip()

                real_url = self._resolve_google_url(google_link)

                # Heuristik Kategori
                category = default_category
                t_lower = title.lower()
                if any(k in t_lower for k in ["ekonomi", "ihsg", "rupiah", "pajak", "ppn", "bank", "bisnis", "saham"]):
                    category = "Ekonomi"
                elif any(k in t_lower for k in ["hukum", "polisi", "kpk", "sidang", "tersangka", "kasus", "kejaksaan"]):
                    category = "Hukum"
                elif any(k in t_lower for k in ["ai", "teknologi", "gadget", "siber", "robot", "aplikasi", "kominfo"]):
                    category = "Teknologi"
                elif any(k in t_lower for k in ["banjir", "cuaca", "gempa", "iklim", "lingkungan", "hujan", "polusi"]):
                    category = "Lingkungan"
                elif any(k in t_lower for k in ["politik", "dpr", "kpu", "pilkada", "presiden", "partai", "gerindra", "wapres"]):
                    category = "Politik"

                articles.append(ArticleItem(
                    id=self._generate_id(real_url),
                    title=title,
                    url=real_url,
                    publisher=publisher,
                    category=category,
                    published_at=pub_date,
                    snippet=clean_snippet[:280] + ("..." if len(clean_snippet) > 280 else ""),
                    image_url="",
                    source_type="google_news_rss"
                ))
        except Exception as e:
            logger.error(f"Gagal mem-parse XML Google News: {e}")

        return articles

    def fetch_top_headlines(self, limit: int = 15) -> List[ArticleItem]:
        """
        Mengambil berita TERKINI UTAMA (Breaking News Hari Ini) langsung dari Google News Indonesia.
        """
        try:
            headers = get_request_headers()
            res = self.session.get(GOOGLE_NEWS_TOP_RSS, headers=headers, timeout=self.timeout)
            if res.status_code == 200:
                return self._parse_xml_items(res.content, default_category="Nasional", limit=limit)
        except Exception as e:
            logger.warning(f"Gagal mengambil top headlines Google News: {e}")
        return []

    def fetch_latest(self, category: str = "all", limit: int = 15) -> List[ArticleItem]:
        """
        Mengambil berita terkini berdasarkan kategori atau headline nasional.
        """
        if category == "all" or not category:
            return self.fetch_top_headlines(limit=limit)

        query_map = {
            "Politik": "politik Indonesia",
            "Ekonomi": "ekonomi bisnis Indonesia",
            "Hukum": "hukum Indonesia",
            "Teknologi": "teknologi kecerdasan buatan Indonesia",
            "Lingkungan": "lingkungan cuaca Indonesia"
        }
        q = query_map.get(category, f"{category} Indonesia")
        return self.search(q, limit=limit)

    def search(self, query: str, limit: int = 10) -> List[ArticleItem]:
        """
        Mencari berita real-time di Google News berdasarkan kata kunci spesifik.
        """
        encoded_query = urllib.parse.quote_plus(query)
        rss_url = f"{GOOGLE_NEWS_RSS_BASE}?q={encoded_query}&hl=id&gl=ID&ceid=ID:id"

        try:
            headers = get_request_headers()
            res = self.session.get(rss_url, headers=headers, timeout=self.timeout)
            if res.status_code == 200:
                return self._parse_xml_items(res.content, default_category="Nasional", limit=limit)
        except Exception as e:
            logger.error(f"Gagal mencari di Google News RSS: {e}")

        return []
