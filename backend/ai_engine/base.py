"""
Interface Dasar (Base Engine) untuk Komparasi dan Perangkuman AI.
Raja Zhafar (Divisi AI Modeling) dapat mengimplementasikan kelas turunan dari BaseAIEngine.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAIEngine(ABC):
    """Kontrak antarmuka untuk Modul AI Behind The Headline."""

    @abstractmethod
    def summarize_article(self, article: Dict[str, Any]) -> str:
        """Menghasilkan ringkasan intisari 2-3 kalimat untuk satu artikel tunggal."""
        pass

    @abstractmethod
    def summarize_topic(self, article: Dict[str, Any]) -> str:
        """
        Menghasilkan ringkasan topik berita secara tematik dan klasifikasi kategori.
        Contoh: Berita ekspor diklasifikasikan ke dalam topik Ekonomi & Perdagangan.
        """
        pass

    @abstractmethod
    def compare_cluster(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Menganalisis klaster berita antarmedia dan menghasilkan:
        1. Executive Summary (3-4 kalimat)
        2. Matriks Komparasi Aspek (Data angka, Narasumber, Fokus berita)
        3. Konsensus dan Titik Friksi (Divergensi)
        """
        pass
