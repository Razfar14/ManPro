"""
Sumber 4: Ekstraksi Langsung via RSS Feed Resmi Media Indonesia (Tanpa API Key)
Mengambil berita langsung dari feed sindikasi resmi penerbit:
- CNN Indonesia (Nasional, Ekonomi, Teknologi)
- CNBC Indonesia (News, Market)
- Antara News Terkini
"""

import hashlib
import logging
import re
from typing import List, Dict
import xml.etree.ElementTree as ET
import requests

from backend.ingestion.base import BaseIngestionSource, ArticleItem
from backend.scraper.user_agents import get_request_headers
from backend.config import OFFICIAL_RSS_FEEDS, DEFAULT_TIMEOUT

logger = logging.getLogger("MediaRSSSource")

class MediaRSSSource(BaseIngestionSource):
    name = "Official Media RSS Feeds (CNN, CNBC, Antara, Tempo)"

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def _generate_id(self, url: str) -> str:
        return "rss-" + hashlib.md5(url.encode("utf-8")).hexdigest()[:10]

    def _parse_feed(self, publisher: str, feed_url: str, limit: int = 5) -> List[ArticleItem]:
        articles: List[ArticleItem] = []
        try:
            headers = get_request_headers(referer="https://google.com/")
            res = self.session.get(feed_url, headers=headers, timeout=self.timeout)
            if res.status_code != 200:
                logger.debug(f"Feed {publisher} ({feed_url}) HTTP status {res.status_code}")
                return articles

            root = ET.fromstring(res.content)
            items = root.findall(".//channel/item")

            for it in items:
                if len(articles) >= limit:
                    break

                title = it.findtext("title", "").strip()
                link = it.findtext("link", "").strip()
                pub_date = it.findtext("pubDate", "").strip()
                desc = it.findtext("description", "").strip()

                if not link or not title:
                    continue

                # Filter klip video murni (seperti /tv/ tanpa teks panjang) agar pembaca mendapatkan artikel teks lengkap
                if "/tv/" in link or title.upper().startswith("VIDEO:"):
                    continue

                image_url = ""
                enclosure = it.find("enclosure")
                if enclosure is not None and "url" in enclosure.attrib:
                    image_url = enclosure.attrib["url"]
                else:
                    img_match = re.search(r'src=["\'](https?://[^"\']+)["\']', desc)
                    if img_match:
                        image_url = img_match.group(1)

                clean_snippet = re.sub(r"<[^>]+>", "", desc).strip()
                clean_snippet = re.sub(r"&nbsp;|&quot;|&amp;", " ", clean_snippet).strip()

                category = "Nasional"
                if "cnbc" in feed_url.lower():
                    category = "Ekonomi"
                elif any(k in title.lower() for k in ["ekonomi", "ihsg", "rupiah", "pajak", "ppn", "ojk"]):
                    category = "Ekonomi"
                elif any(k in title.lower() for k in ["hukum", "kpk", "polisi", "kejaksaan", "tersangka"]):
                    category = "Hukum"
                elif any(k in title.lower() for k in ["teknologi", "ai", "gadget", "siber"]):
                    category = "Teknologi"
                elif any(k in title.lower() for k in ["banjir", "gempa", "cuaca", "lingkungan", "hujan"]):
                    category = "Lingkungan"

                articles.append(ArticleItem(
                    id=self._generate_id(link),
                    title=title,
                    url=link,
                    publisher=publisher,
                    category=category,
                    published_at=pub_date,
                    snippet=clean_snippet[:250] + ("..." if len(clean_snippet) > 250 else ""),
                    image_url=image_url,
                    source_type="official_rss"
                ))
        except Exception as e:
            logger.debug(f"Gagal mem-parse RSS {publisher} ({feed_url}): {e}")

        return articles

    def fetch_latest(self, category: str = "all", limit: int = 15) -> List[ArticleItem]:
        all_articles: List[ArticleItem] = []
        active_feeds = [
            ("CNN Indonesia", "https://www.cnnindonesia.com/nasional/rss"),
            ("CNN Indonesia", "https://www.cnnindonesia.com/ekonomi/rss"),
            ("CNBC Indonesia", "https://www.cnbcindonesia.com/news/rss"),
            ("Antara", "https://www.antaranews.com/rss/terkini.xml")
        ]

        per_media = max(3, limit // len(active_feeds))
        for publisher, url in active_feeds:
            arts = self._parse_feed(publisher, url, limit=per_media)
            all_articles.extend(arts)

        return all_articles[:limit]

    def search(self, query: str, limit: int = 10) -> List[ArticleItem]:
        all_articles = self.fetch_latest(limit=30)
        q_low = query.lower()
        matched = [a for a in all_articles if q_low in a.title.lower() or q_low in a.snippet.lower()]
        return matched[:limit]
