"""
Modul Full-Text Scraping & Ekstraksi Isi Berita
Mengambil artikel lengkap dari portal media Indonesia (CNN, CNBC, Tempo, Antara, Kumparan, dll.),
membersihkan elemen iklan/boilerplate ('Baca Juga', copyright), serta mengekstrak teks, narasumber, dan kutipan.
"""

import re
import logging
from typing import Dict, Any, List, Optional
import requests
from lxml import html

from backend.scraper.user_agents import get_request_headers
from backend.config import DEFAULT_TIMEOUT

logger = logging.getLogger("FullTextExtractor")

# Pola teks boilerplate yang harus dieliminasi dari artikel media Indonesia
BOILERPLATE_PATTERNS = [
    r"Baca juga:.*",
    r"Simak Video:.*",
    r"Simak juga Video.*",
    r"Pilihan Editor:.*",
    r"Pilihan Redaksi:.*",
    r"Tonton video.*",
    r"Follow berita .* di Google News.*",
    r"KLIK DI SINI.*",
    r"ADVERTISEMENT.*",
    r"SCROLL TO CONTINUE WITH CONTENT.*",
    r"Halaman selanjutnya.*",
    r"Dapatkan informasi terkini langsung dari gadget Anda.*",
    r"\(Gambas:Video .*\)"
]

# Pemetaan selektor CSS artikel untuk portal berita utama Indonesia
PORTAL_SELECTORS = {
    "cnnindonesia.com": [
        ".detail-text", ".detail__body-text", "#detikdetailtext"
    ],
    "cnbcindonesia.com": [
        ".detail_text", ".detail__body-text"
    ],
    "tempo.co": [
        ".detail-konten", ".read__content", ".content-detail", ".wrapper-content"
    ],
    "republika.co.id": [
        ".artikel", ".detail-berita", ".content-news"
    ],
    "antaranews.com": [
        ".post-content", ".post_content"
    ],
    "kompas.com": [
        ".read__content", ".kcm-read-text"
    ]
}

class FullTextExtractor:
    """Kelas untuk melakukan scraping dan pembersihan teks artikel berita."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_article(self, url: str) -> Dict[str, Any]:
        """
        Mengunduh HTML dan mengekstrak teks lengkap dari URL berita.
        """
        headers = get_request_headers(referer="https://news.google.com/")
        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            if response.status_code != 200:
                logger.warning(f"Gagal mengambil URL {url}: HTTP {response.status_code}")
                return self._fallback_error(url, f"HTTP Error {response.status_code}")

            return self.parse_html(response.text, url)
        except Exception as e:
            logger.error(f"Error scraping artikel {url}: {e}")
            return self._fallback_error(url, str(e))

    def parse_html(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Mem-parse struktur HTML dan mengekstrak judul, tanggal, penulis, gambar, dan paragraf bersih.
        """
        try:
            tree = html.fromstring(html_content)
        except Exception as e:
            logger.warning(f"Gagal memparsing HTML lxml: {e}")
            return self._fallback_regex(html_content, url)

        # 1. Judul Berita
        title = ""
        h1_nodes = tree.xpath("//h1")
        if h1_nodes and h1_nodes[0].text_content().strip():
            title = h1_nodes[0].text_content().strip()
        else:
            meta_title = tree.xpath("//meta[@property='og:title']/@content")
            if meta_title:
                title = meta_title[0].strip()

        # 2. Penulis
        author = "Redaksi"
        author_meta = tree.xpath("//meta[@name='author']/@content | //meta[@property='article:author']/@content")
        if author_meta:
            author = author_meta[0].strip()
        else:
            byline = tree.xpath("//*[contains(@class, 'author') or contains(@class, 'penulis') or contains(@class, 'byline')]")
            if byline:
                raw_author = byline[0].text_content().strip()
                if raw_author and len(raw_author) < 80:
                    author = raw_author

        # 3. Tanggal Terbit
        published_at = ""
        pub_meta = tree.xpath("//meta[@property='article:published_time']/@content | //meta[@name='pubdate']/@content")
        if pub_meta:
            published_at = pub_meta[0].strip()

        # 4. Gambar Utama
        lead_image = ""
        og_image = tree.xpath("//meta[@property='og:image']/@content")
        if og_image:
            lead_image = og_image[0].strip()

        # 5. Ekstraksi Tubuh Artikel Menggunakan Selektor Spesifik atau Heuristik
        raw_paragraphs = []
        matched_portal = None
        for domain, selectors in PORTAL_SELECTORS.items():
            if domain in url:
                matched_portal = domain
                for sel in selectors:
                    # Konversi CSS selector sederhana ke xpath
                    xpath_query = f"//*[contains(@class, '{sel.lstrip('.#')}')]//p"
                    nodes = tree.xpath(xpath_query)
                    if nodes:
                        raw_paragraphs = [n.text_content().strip() for n in nodes if n.text_content().strip()]
                        break
                if raw_paragraphs:
                    break

        # Jika selektor khusus belum menemukan konten, gunakan heuristik pencarian paragraf umum
        if not raw_paragraphs:
            article_nodes = tree.xpath("//article//p | //div[contains(@class, 'article') or contains(@class, 'detail') or contains(@class, 'content')]//p")
            if article_nodes:
                raw_paragraphs = [n.text_content().strip() for n in article_nodes if n.text_content().strip()]
            else:
                p_nodes = tree.xpath("//p")
                raw_paragraphs = [n.text_content().strip() for n in p_nodes if len(n.text_content().strip()) > 35]

        # 6. Pembersihan Teks dari Iklan dan Boilerplate
        cleaned_paragraphs = []
        for p in raw_paragraphs:
            p_clean = p.strip()
            # Cek terhadap pola boilerplate
            is_boilerplate = False
            for pat in BOILERPLATE_PATTERNS:
                if re.search(pat, p_clean, re.IGNORECASE):
                    is_boilerplate = True
                    break
            if not is_boilerplate and len(p_clean) > 20:
                cleaned_paragraphs.append(p_clean)

        full_text = "\n\n".join(cleaned_paragraphs)

        return {
            "status": "success",
            "url": url,
            "title": title,
            "author": author,
            "published_at": published_at,
            "lead_image": lead_image,
            "paragraphs": cleaned_paragraphs,
            "full_text": full_text,
            "word_count": len(full_text.split()) if full_text else 0
        }

    def _fallback_regex(self, html_content: str, url: str) -> Dict[str, Any]:
        """Fallback ekstraksi berbasis Regular Expression jika parser DOM gagal."""
        title_match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""
        p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html_content, re.IGNORECASE | re.DOTALL)
        paragraphs = []
        for p in p_matches:
            clean = re.sub(r"<[^>]+>", "", p).strip()
            if len(clean) > 30:
                paragraphs.append(clean)
        full_text = "\n\n".join(paragraphs)
        return {
            "status": "partial",
            "url": url,
            "title": title,
            "author": "Redaksi",
            "published_at": "",
            "lead_image": "",
            "paragraphs": paragraphs,
            "full_text": full_text,
            "word_count": len(full_text.split())
        }

    def _fallback_error(self, url: str, error_msg: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "url": url,
            "error": error_msg,
            "title": "",
            "author": "Redaksi",
            "published_at": "",
            "lead_image": "",
            "paragraphs": [],
            "full_text": "",
            "word_count": 0
        }
