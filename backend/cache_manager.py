"""
Modul Cache Manager Terpadu (Behind The Headline)
Menyimpan hasil inferensi AI, hasil pencarian, dan berita terkini ke disk & memori
untuk:
1. Menghemat Token AI (DeepSeek / LLM tidak dipanggil berulang kali untuk topik yang sama).
2. Mempercepat loading (respons seketika <10ms tanpa jeda).
3. Mendukung navigasi bolak-balik tanpa delay.
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("CacheManager")

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
AI_CACHE_FILE = os.path.join(CACHE_DIR, "ai_cache.json")
NEWS_CACHE_FILE = os.path.join(CACHE_DIR, "news_cache.json")

# TTL (Time To Live dalam detik)
AI_CACHE_TTL = 86400 * 7   # 7 Hari untuk analisis AI (Sangat hemat token!)
NEWS_CACHE_TTL = 600       # 10 Menit untuk berita breaking news terkini

class CacheManager:
    """Manajer Cache Dua Lapis (In-Memory + Disk Persistence)."""

    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.ai_cache: Dict[str, Dict[str, Any]] = self._load_file(AI_CACHE_FILE)
        self.news_cache: Dict[str, Dict[str, Any]] = self._load_file(NEWS_CACHE_FILE)
        logger.info(f"CacheManager siap. {len(self.ai_cache)} hasil AI & {len(self.news_cache)} berita tersimpan.")

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Gagal memuat cache {file_path}: {e}")
        return {}

    def _save_file(self, file_path: str, data: Dict[str, Any]):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Gagal menyimpan cache {file_path}: {e}")

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower()

    # ==========================================
    # 1. AI RESPONSE CACHE (HEMAT TOKEN DEEPSEEK)
    # ==========================================
    def get_ai_analysis(self, query: str) -> Optional[Dict[str, Any]]:
        """Mengambil analisis AI yang tersimpan agar tidak menghabiskan token LLM."""
        norm_key = self._normalize_key(query)
        entry = self.ai_cache.get(norm_key)
        if entry:
            timestamp = entry.get("_cached_at", 0)
            if time.time() - timestamp < AI_CACHE_TTL:
                logger.info(f"[CACHE HIT ⚡] Analisis AI untuk '{query}' diambil dari cache (Hemat Token DeepSeek!)")
                data = dict(entry.get("data", {}))
                data["from_cache"] = True
                data["cache_age_seconds"] = int(time.time() - timestamp)
                return data
        return None

    def save_ai_analysis(self, query: str, data: Dict[str, Any]):
        """Menyimpan hasil inferensi AI ke disk."""
        norm_key = self._normalize_key(query)
        self.ai_cache[norm_key] = {
            "_cached_at": time.time(),
            "data": data
        }
        self._save_file(AI_CACHE_FILE, self.ai_cache)
        logger.info(f"[CACHE SAVED 💾] Analisis AI untuk '{query}' disimpan ke cache permanen.")

    # ==========================================
    # 2. LATEST NEWS CACHE (INSTANT HOME LOAD)
    # ==========================================
    def get_latest_news(self, category: str = "all") -> Optional[List[Dict[str, Any]]]:
        """Mengambil berita beranda terkini dari cache jika masih fresh."""
        norm_key = f"latest_{self._normalize_key(category)}"
        entry = self.news_cache.get(norm_key)
        if entry:
            timestamp = entry.get("_cached_at", 0)
            if time.time() - timestamp < NEWS_CACHE_TTL:
                logger.info(f"[CACHE HIT ⚡] Berita beranda kategori '{category}' dimuat dari cache.")
                return entry.get("articles")
        return None

    def save_latest_news(self, category: str, articles: List[Dict[str, Any]]):
        """Menyimpan berita terkini ke cache."""
        norm_key = f"latest_{self._normalize_key(category)}"
        self.news_cache[norm_key] = {
            "_cached_at": time.time(),
            "articles": articles
        }
        self._save_file(NEWS_CACHE_FILE, self.news_cache)

# Singleton instance
cache_manager = CacheManager()
