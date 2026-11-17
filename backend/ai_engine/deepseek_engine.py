"""
DeepSeek AI Engine (Behind The Headline)
Menggunakan DeepSeek API (deepseek-chat) untuk:
1. Ringkasan Topik Tematik (klasifikasi topik & penjelasan mendalam substansinya)
2. Ringkasan Artikel
3. Matriks Komparasi Antarmedia & Penjelasan Topik yang Dicari
4. Deteksi Topik Nyeleneh / Tidak Valid
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
import requests

from backend.ai_engine.base import BaseAIEngine
from backend.ai_engine.prototype_nlp import ai_engine as prototype_engine
from backend.ai_engine.topic_validator import (
    ABSURD_TOPIC_MESSAGE,
    is_absurd_or_invalid_topic,
)
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL

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

    def _call_deepseek(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 1500) -> Optional[str]:
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
            "max_tokens": max_tokens
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
        except Exception:
            self.last_status = "connection_error"
            return None

    def is_query_absurd_with_llm(self, query: str) -> bool:
        """
        Memeriksa lewat DeepSeek apakah topik yang dicari nyeleneh, fiktif mustahil,
        acak/gibberish, atau di luar ranah berita nyata.
        """
        is_absurd, _ = is_absurd_or_invalid_topic(query)
        if is_absurd:
            return True

        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah filter kelayakan topik berita. Tentukan apakah query pengguna adalah "
                    "topik berita nyata/wajar (politik, ekonomi, hukum, teknologi, lingkungan, sosial, olahraga, budaya, dll) "
                    "ATAU query nyeleneh/absurd/mustahil/karakter fiksi/gibberish/obrolan non-berita "
                    "(misal: 'kucing terbang naik motor', 'alien jualan bakso', 'asdfg', 'resep nasi goreng'). "
                    'Jawab HANYA JSON valid: {"is_absurd": true} atau {"is_absurd": false}.'
                )
            },
            {"role": "user", "content": f"Query: {query}"}
        ]
        raw = self._call_deepseek(messages, temperature=0.0, max_tokens=60)
        if raw:
            try:
                cleaned = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", raw.strip())
                parsed = json.loads(cleaned)
                return bool(parsed.get("is_absurd", False))
            except Exception:
                pass
        return False

    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik berita yang informatif dan menjelaskan substansinya.
        """
        title = article.get("title", "")
        publisher = article.get("publisher", "Media")
        category = article.get("category", "Umum")
        text_snippet = (article.get("full_text", "") or article.get("snippet", ""))[:1800]

        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah analis jurnalisme 'Behind The Headline'. Tugasmu adalah mengklasifikasikan topik berita "
                    "dan menjelaskan isi topik tersebut secara informatif dalam 3-4 kalimat Bahasa Indonesia yang jelas.\n"
                    "Aturan wajib:\n"
                    "1. Awali persis dengan format 'Topik: <Nama Topik & Subtopik>.' (contoh: 'Topik: Ekonomi & Perdagangan.').\n"
                    "2. Kalimat pertama menjelaskan mengapa berita masuk ke topik itu.\n"
                    "3. Kalimat berikutnya menjelaskan inti persoalan, pihak/aktor atau kebijakan yang dibahas, angka penting jika ada, serta dampaknya bagi publik."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Penerbit: {publisher}\n"
                    f"Judul: {title}\n"
                    f"Kategori Awal: {category}\n"
                    f"Teks: {text_snippet}\n\n"
                    "Buat penjelasan topik 3-4 kalimat yang informatif:"
                )
            }
        ]

        result = self._call_deepseek(messages, temperature=0.2, max_tokens=500)
        if result and len(result.strip()) > 35:
            cleaned = result.strip()
            if not cleaned.startswith("Topik:"):
                cleaned = f"Topik: {category}. {cleaned}"
            return cleaned

        return prototype_engine.summarize_topic(article)

    def summarize_article(self, article: Dict[str, Any]) -> str:
        title = article.get("title", "")
        publisher = article.get("publisher", "Media Berita")
        full_text = article.get("full_text", "") or article.get("snippet", "")

        messages = [
            {
                "role": "system",
                "content": "Rangkum artikel berita berikut dalam 2-3 kalimat Bahasa Indonesia yang netral, padat, dan objektif."
            },
            {
                "role": "user",
                "content": f"Penerbit: {publisher}\nJudul: {title}\nIsi:\n{full_text[:3000]}\n\nRangkuman:"
            }
        ]

        result = self._call_deepseek(messages, temperature=0.2, max_tokens=400)
        if result and len(result.strip()) > 30:
            return result.strip()

        return prototype_engine.summarize_article(article)

    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        is_absurd, _ = is_absurd_or_invalid_topic(query)
        if is_absurd:
            return {
                "query": query,
                "invalid_topic": True,
                "summary": ABSURD_TOPIC_MESSAGE,
                "matrix_columns": [],
                "matrix_rows": [],
                "consensus": [],
                "divergence": [],
                "engine_used": "Topic Validator"
            }

        if not articles:
            if self.is_query_absurd_with_llm(query):
                return {
                    "query": query,
                    "invalid_topic": True,
                    "summary": ABSURD_TOPIC_MESSAGE,
                    "matrix_columns": [],
                    "matrix_rows": [],
                    "consensus": [],
                    "divergence": [],
                    "engine_used": "DeepSeek Topic Filter"
                }
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
                    "Kamu adalah AI analis dan komparasi berita 'Behind The Headline'.\n"
                    "Pertama, periksa apakah topik pencarian (query) pengguna adalah topik berita nyata atau topik nyeleneh/mustahil/absurd/gibberish "
                    "(misal: 'kucing terbang', 'alien jualan bakso', 'spongebob korupsi', 'asdfg', 'resep masak').\n"
                    "Jika topik nyeleneh/tidak masuk akal, kembalikan:\n"
                    '{"is_absurd": true, "summary": "' + ABSURD_TOPIC_MESSAGE + '", "matrix_columns": [], "matrix_rows": [], "consensus": [], "divergence": []}\n\n'
                    "Jika topik berita valid, buat penjelasan yang MENDALAM dan JELAS tentang topik yang dicari, mencakup:\n"
                    "1. Penjelasan apa topik yang dicari, latar belakang masalah/kebijakan/peristiwa, serta dampaknya bagi masyarakat.\n"
                    "2. Fakta kunci, angka/data penting, dan pihak/narasumber yang terlibat berdasarkan artikel.\n"
                    "3. Perbandingan penekanan atau sudut pandang masing-masing media.\n\n"
                    "Kembalikan HANYA JSON valid tanpa tanda backtick ``` dengan struktur:\n"
                    "{\n"
                    '  "is_absurd": false,\n'
                    '  "summary": "Ringkasan penjelasan topik 4-6 kalimat yang informatif, mendalam, dan membandingkan sudut pandang media",\n'
                    '  "matrix_columns": ["Aspek", "<Nama Media 1>", "<Nama Media 2>", "<Nama Media 3>"],\n'
                    '  "matrix_rows": [\n'
                    '    {"aspek": "Data angka", "cnn": "...", "cnbc": "...", "tempo": "..."},\n'
                    '    {"aspek": "Narasumber", "cnn": "...", "cnbc": "...", "tempo": "..."},\n'
                    '    {"aspek": "Fokus berita", "cnn": "...", "cnbc": "...", "tempo": "..."}\n'
                    '  ],\n'
                    '  "consensus": ["..."],\n'
                    '  "divergence": ["..."]\n'
                    "}\n"
                    "Catatan: tetap gunakan key 'cnn', 'cnbc', 'tempo' pada objek matrix_rows agar kompatibel dengan tabel frontend, dengan isi masing-masing sesuai urutan media pada matrix_columns."
                )
            },
            {
                "role": "user",
                "content": f"Topik yang dicari: '{query}'\nArtikel:\n{json.dumps(articles_payload, ensure_ascii=False)}"
            }
        ]

        raw_json_str = self._call_deepseek(messages, temperature=0.2, max_tokens=1500)
        if raw_json_str:
            try:
                cleaned = raw_json_str.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
                    cleaned = re.sub(r"\n?```$", "", cleaned)
                parsed = json.loads(cleaned)
                if parsed.get("is_absurd"):
                    return {
                        "query": query,
                        "invalid_topic": True,
                        "summary": ABSURD_TOPIC_MESSAGE,
                        "matrix_columns": [],
                        "matrix_rows": [],
                        "consensus": [],
                        "divergence": [],
                        "engine_used": "DeepSeek Topic Filter"
                    }
                if "summary" in parsed and "matrix_rows" in parsed:
                    parsed["query"] = query
                    parsed["invalid_topic"] = False
                    parsed["engine_used"] = "DeepSeek (deepseek-chat)"
                    return parsed
            except Exception as e:
                logger.warning(f"[DeepSeek AI] Gagal parse JSON: {e}")

        res = prototype_engine.compare_cluster(query, articles)
        res["engine_used"] = "Prototype NLP (DeepSeek fallback)"
        return res


deepseek_engine = DeepSeekAIEngine()
