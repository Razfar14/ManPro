"""
DeepSeek AI Engine (Behind The Headline)
Menggunakan DeepSeek API (deepseek-chat) untuk:
1. Ringkasan Topik Tematik (klasifikasi topik berita, misal ekspor masuk ke Ekonomi)
2. Ringkasan Artikel
3. Matriks Komparasi Antarmedia (Data angka, Narasumber, Fokus berita)
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
import requests

from backend.ai_engine.base import BaseAIEngine
from backend.ai_engine.prototype_nlp import ai_engine as prototype_engine
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, DEFAULT_TIMEOUT

logger = logging.getLogger("DeepSeekAIEngine")

class DeepSeekAIEngine(BaseAIEngine):
    """
    Engine AI Utama Behind The Headline bertenaga DeepSeek LLM (deepseek-chat).
    """

    def __init__(self, api_key: str = DEEPSEEK_API_KEY, model: str = DEEPSEEK_MODEL):
        self.api_key = api_key
        self.api_url = DEEPSEEK_API_URL
        self.model = model
        self.timeout = 25
        self.last_status = "initialized"
        logger.info(f"DeepSeek AI Engine diinisialisasi dengan model '{self.model}'.")

    def _call_deepseek(self, messages: List[Dict[str, str]], temperature: float = 0.3) -> Optional[str]:
        if not self.api_key or self.api_key.startswith("sk-placeholder"):
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1200
        }

        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                self.last_status = "active_deepseek"
                return content
            elif res.status_code == 402:
                self.last_status = "insufficient_balance"
                return None
            else:
                self.last_status = f"http_{res.status_code}"
                return None
        except Exception as e:
            self.last_status = "connection_error"
            return None

    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik dan alasan klasifikasi kategorinya menggunakan AI.
        """
        title = article.get("title", "")
        publisher = article.get("publisher", "Media")
        category = article.get("category", "Umum")
        text_snippet = (article.get("full_text", "") or article.get("snippet", ""))[:1200]

        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah asisten jurnalisme 'Behind The Headline'. Tugasmu adalah mengklasifikasikan topik berita "
                    "dan menjelaskan dalam 1-2 kalimat mengapa berita tersebut masuk ke dalam topik itu. "
                    "Contoh format yang harus diikuti:\n"
                    "'Topik: Ekonomi & Perdagangan. Berita ini diklasifikasikan ke dalam topik Ekonomi & Perdagangan karena "
                    "membahas kebijakan ekspor komoditas nikel yang berdampak pada penerimaan devisa negara berdasarkan laporan Tempo.'"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Penerbit: {publisher}\n"
                    f"Judul: {title}\n"
                    f"Kategori Awal: {category}\n"
                    f"Teks: {text_snippet}\n\n"
                    "Buat ringkasan topik dalam 1-2 kalimat sesuai format contoh di atas:"
                )
            }
        ]

        result = self._call_deepseek(messages, temperature=0.2)
        if result and len(result.strip()) > 25:
            return result.strip()

        # Fallback ke Prototype NLP Engine
        return prototype_engine.summarize_topic(article)

    def summarize_article(self, article: Dict[str, Any]) -> str:
        title = article.get("title", "")
        publisher = article.get("publisher", "Media Berita")
        full_text = article.get("full_text", "") or article.get("snippet", "")

        messages = [
            {
                "role": "system",
                "content": "Rangkum artikel berita berikut dalam 2-3 kalimat Bahasa Indonesia yang netral dan objektif."
            },
            {
                "role": "user",
                "content": f"Penerbit: {publisher}\nJudul: {title}\nIsi:\n{full_text[:3000]}\n\nRangkuman:"
            }
        ]

        result = self._call_deepseek(messages, temperature=0.2)
        if result and len(result.strip()) > 30:
            return result.strip()

        return prototype_engine.summarize_article(article)

    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not articles:
            return prototype_engine.compare_cluster(query, articles)

        articles_payload = []
        for art in articles[:4]:
            articles_payload.append({
                "publisher": art.get("publisher", "Media"),
                "title": art.get("title", ""),
                "content": (art.get("full_text", "") or art.get("snippet", ""))[:2200]
            })

        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah AI komparasi media 'Behind The Headline'. "
                    "Kembalikan HANYA format JSON valid tanpa tanda backtick ``` dengan struktur:\n"
                    "{\n"
                    '  "summary": "Ringkasan 3-4 kalimat sintesis komparatif antarmedia",\n'
                    '  "matrix_columns": ["Aspek", "CNN", "CNBC", "Tempo"],\n'
                    '  "matrix_rows": [\n'
                    '    {"aspek": "Data angka", "cnn": "...", "cnbc": "...", "tempo": "..."},\n'
                    '    {"aspek": "Narasumber", "cnn": "...", "cnbc": "...", "tempo": "..."},\n'
                    '    {"aspek": "Fokus berita", "cnn": "...", "cnbc": "...", "tempo": "..."}\n'
                    '  ],\n'
                    '  "consensus": ["..."],\n'
                    '  "divergence": ["..."]\n'
                    "}"
                )
            },
            {
                "role": "user",
                "content": f"Topik: '{query}'\nArtikel:\n{json.dumps(articles_payload, ensure_ascii=False)}"
            }
        ]

        raw_json_str = self._call_deepseek(messages, temperature=0.2)
        if raw_json_str:
            try:
                cleaned = raw_json_str.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
                    cleaned = re.sub(r"\n?```$", "", cleaned)
                parsed = json.loads(cleaned)
                if "summary" in parsed and "matrix_rows" in parsed:
                    parsed["query"] = query
                    parsed["engine_used"] = "DeepSeek (deepseek-chat)"
                    return parsed
            except Exception as e:
                logger.warning(f"[DeepSeek AI] Gagal parse JSON: {e}")

        res = prototype_engine.compare_cluster(query, articles)
        res["engine_used"] = "Prototype NLP (DeepSeek fallback)"
        return res

deepseek_engine = DeepSeekAIEngine()
