"""
Definisi Data Model dan Kelas Dasar (Base Interface) untuk Sumber Ingestion Berita.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ArticleItem:
    """Struktur data standar artikel berita hasil ingestion."""
    id: str
    title: str
    url: str
    publisher: str
    category: str
    published_at: str
    snippet: str
    image_url: str
    source_type: str  # 'unofficial_api', 'google_news_rss', 'official_rss', 'global_api', 'cache'
    author: Optional[str] = "Redaksi"
    full_text: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaseIngestionSource(ABC):
    """Interface abstrak untuk setiap penyedia sumber berita."""

    name: str = "Base Source"

    @abstractmethod
    def fetch_latest(self, category: str = "all", limit: int = 10) -> List[ArticleItem]:
        """Mengambil berita terkini."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[ArticleItem]:
        """Mencari berita berdasarkan kata kunci."""
        pass
