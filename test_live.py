from backend.ingestion.aggregator import aggregator
from backend.ai_engine import ai_engine

def test_live():
    print("--- Testing Live News Aggregation ---")
    news = aggregator.fetch_latest_news(limit=6)
    print(f"Total live news fetched: {len(news)}")
    for i, n in enumerate(news):
        print(f"{i+1}. [{n.get('publisher')}] {n.get('title')} ({n.get('published_at')})")

    print("\n--- Testing DeepSeek Engine Initialization ---")
    print("AI Engine class:", ai_engine.__class__.__name__)
    sample_article = {
        "title": "Kenaikan Pajak dan APBN",
        "publisher": "CNN Indonesia",
        "full_text": "Pemerintah merencanakan penyesuaian tarif PPN untuk memperkuat fiskal."
    }
    summary = ai_engine.summarize_article(sample_article)
    print("AI Summary output:", summary)

if __name__ == "__main__":
    test_live()
