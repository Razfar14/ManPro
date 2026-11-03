"""
Panduan Integrasi Model AI Sebenarnya (Untuk Raja Zhafar - AI Modeling)
========================================================================

File ini berisi template kode siap pakai untuk menghubungkan model AI pencarian/komparasi
yang akan disediakan oleh Raja Zhafar (misalnya Google Gemini API, IndoBERT, atau LLM lokal).

Langkah Integrasi:
-------------------
1. Instal SDK yang dipilih:
   pip install google-genai   # atau google-generativeai / transformers

2. Buat class turunan dari BaseAIEngine seperti contoh GeminiAIEngine di bawah.
3. Di file `backend/ai_engine/__init__.py`, ubah:
      from backend.ai_engine.prototype_nlp import ai_engine
   menjadi:
      from backend.ai_engine.adapter_guide import GeminiAIEngine
      ai_engine = GeminiAIEngine(api_key="YOUR_GEMINI_API_KEY")
"""

import json
import logging
from typing import List, Dict, Any
from backend.ai_engine.base import BaseAIEngine

logger = logging.getLogger("AIEngineAdapter")

class GeminiAIEngine(BaseAIEngine):
    """
    Adapter integrasi Google Gemini API untuk analisis semantik Behind The Headline.
    Mengirimkan teks lengkap hasil scraping ke LLM dengan prompt terstruktur (Structured JSON Output).
    """

    def __init__(self, api_key: str = "", model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if api_key:
            try:
                # Menggunakan google-genai atau google.generativeai
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model_name)
                logger.info(f"Gemini AI Engine aktif dengan model {model_name}")
            except Exception as e:
                logger.warning(f"Belum dapat menginisialisasi Google Gemini SDK: {e}")

    def summarize_article(self, article: Dict[str, Any]) -> str:
        if not self.client:
            from backend.ai_engine.prototype_nlp import ai_engine as proto
            return proto.summarize_article(article)

        prompt = f"""
        Kamu adalah sistem AI Behind The Headline.
        Rangkum artikel berita berikut dalam 2-3 kalimat objektif Bahasa Indonesia:
        Judul: {article.get('title')}
        Media: {article.get('publisher')}
        Isi:
        {article.get('full_text', '')[:3000]}
        """
        try:
            response = self.client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error inference Gemini: {e}")
            from backend.ai_engine.prototype_nlp import ai_engine as proto
            return proto.summarize_article(article)

    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.client:
            from backend.ai_engine.prototype_nlp import ai_engine as proto
            return proto.compare_cluster(query, articles)

        # Siapkan payload artikel
        articles_payload = []
        for a in articles[:4]:
            articles_payload.append({
                "publisher": a.get("publisher"),
                "title": a.get("title"),
                "text": a.get("full_text", "")[:2500] or a.get("snippet", "")
            })

        prompt = f"""
        Kamu adalah AI analis komparasi media 'Behind The Headline'.
        Tugasmu adalah menganalisis dan membandingkan sudut pandang antarmedia mengenai topik: '{query}'.

        Data Artikel yang Diberikan:
        {json.dumps(articles_payload, ensure_ascii=False, indent=2)}

        Wajib kembalikan HANYA format JSON valid tanpa tanda backtick markdown dengan skema berikut:
        {{
          "summary": "Ringkasan 3-4 kalimat sintesis komparatif antarmedia",
          "matrix_columns": ["Aspek", "CNN", "CNBC", "Tempo"],
          "matrix_rows": [
            {{
              "aspek": "Data angka",
              "cnn": "angka/statistik yang disorot CNN",
              "cnbc": "angka/statistik yang disorot CNBC",
              "tempo": "angka/statistik yang disorot Tempo"
            }},
            {{
              "aspek": "Narasumber",
              "cnn": "nama narasumber dan jabatan yang dikutip CNN",
              "cnbc": "nama narasumber dan jabatan yang dikutip CNBC",
              "tempo": "nama narasumber dan jabatan yang dikutip Tempo"
            }},
            {{
              "aspek": "Fokus berita",
              "cnn": "sudut pandang/framing CNN",
              "cnbc": "sudut pandang/framing CNBC",
              "tempo": "sudut pandang/framing Tempo"
            }}
          ],
          "consensus": ["fakta yang disepakati bersama"],
          "divergence": ["titik perbedaan sudut pandang"]
        }}
        """

        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text.strip()
            # Bersihkan markdown formatting jika model menyertakan ```json
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Error parsing Gemini response, fallback ke prototype: {e}")
            from backend.ai_engine.prototype_nlp import ai_engine as proto
            return proto.compare_cluster(query, articles)
