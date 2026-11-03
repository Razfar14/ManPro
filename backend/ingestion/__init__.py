from backend.ingestion.base import ArticleItem, BaseIngestionSource
from backend.ingestion.indo_news_api import IndoNewsAPISource
from backend.ingestion.google_news_rss import GoogleNewsRSSSource
from backend.ingestion.media_rss import MediaRSSSource
from backend.ingestion.global_news_api import GlobalNewsAPISource
from backend.ingestion.aggregator import NewsAggregator, aggregator

__all__ = [
    "ArticleItem",
    "BaseIngestionSource",
    "IndoNewsAPISource",
    "GoogleNewsRSSSource",
    "MediaRSSSource",
    "GlobalNewsAPISource",
    "NewsAggregator",
    "aggregator"
]
