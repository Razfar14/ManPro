"""
Konfigurasi Sistem Behind The Headline (BTH)
Mengatur endpoint API, User-Agent, timeout, dan kunci API untuk modul Ingestion & AI.
"""

import os

# DeepSeek AI API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# Base URL Ingestion Provider
BERITA_INDO_API_BASE = "https://berita-indo-api-two.vercel.app/v1"
API_BERITA_INDONESIA_BASE = "https://api-berita-indonesia.vercel.app"

# Google News RSS Search & Top Feeds
GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"
GOOGLE_NEWS_TOP_RSS = "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"

# RSS Feed Resmi Media Indonesia yang Aktif & Terbuka
OFFICIAL_RSS_FEEDS = {
    "CNN Indonesia": "https://www.cnnindonesia.com/rss",
    "CNBC Indonesia": "https://www.cnbcindonesia.com/news/rss",
    "Antara": "https://www.antaranews.com/rss/terkini.xml",
    "Tempo": "https://www.tempo.co/rss/nasional",
    "Republika": "https://www.republika.co.id/rss"
}

# Provider Global (Freemium - opsional melalui Environment Variable)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY", "")
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY", "")

# HTTP Client Config
DEFAULT_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "6"))
MAX_RETRIES = 2
MAX_ARTICLES_PER_QUERY = 15

# Server Config
HOST = "0.0.0.0"
PORT = 8000
DEBUG = True
