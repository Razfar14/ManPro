import sys
import time
import server

def run_tests():
    client = server.app.test_client()

    print("--- 1. Testing Cookie & Static Routing ---")
    r = client.get('/')
    assert r.status_code == 200
    cookies = r.headers.get_all('Set-Cookie')
    print(f"   [OK] Set-Cookie headers received: {len(cookies)} cookies")
    assert any("bth_session=active" in c for c in cookies), "Cookie bth_session missing"
    assert any("bth_cache_ver=2.2" in c for c in cookies), "Cookie bth_cache_ver missing"

    print("\n--- 2. Testing Detail Page: 2-4 Concise Paragraphs & Topic Summary ---")
    r_art = client.get('/api/v1/article/art-ppn-cnn-01')
    assert r_art.status_code == 200
    art = r_art.get_json()['article']
    paragraphs = art.get('paragraphs', [])
    topic_summary = art.get('topic_summary', '')

    print(f"   [OK] Article Title: '{art['title'][:40]}...'")
    print(f"   [OK] Paragraph count: {len(paragraphs)} (Expect 2-4 paragraphs)")
    assert 2 <= len(paragraphs) <= 4, f"Paragraphs should be 2 to 4, got {len(paragraphs)}"
    print(f"   [OK] Topic Summary: {topic_summary}")
    assert "Topik:" in topic_summary, "Topic summary must contain 'Topik:'"
    assert "Ekonomi" in topic_summary, "PPN article must be classified into Ekonomi topic"

    print("\n--- 3. Testing Broken Snippet Recovery (Tempo.co Screenshot Case) ---")
    # Simulate the exact Tempo article from user's screenshot
    from backend.data_store import store
    from backend.ingestion.base import ArticleItem
    test_broken_item = ArticleItem(
        id="test-tempo-prabowo",
        title="Pidato Prabowo dalam 2 Tahun: Bertabur Makian dan Ancaman",
        url="https://www.tempo.co/nasional/pidato-prabowo",
        publisher="Tempo.co",
        category="Nasional",
        published_at="2026-11-01T08:00:00Z",
        snippet="Pidato Prabowo dalam 2 Tahun: Bertabur Makian dan Ancaman Tempo.co",
        image_url="",
        source_type="test"
    )
    store.save_article(test_broken_item)

    r_broken = client.get('/api/v1/article/test-tempo-prabowo')
    assert r_broken.status_code == 200
    broken_art = r_broken.get_json()['article']
    broken_paras = broken_art.get('paragraphs', [])
    broken_topic = broken_art.get('topic_summary', '')

    print(f"   [OK] Title: '{broken_art['title']}'")
    print(f"   [OK] Recovered paragraph count: {len(broken_paras)} paragraphs!")
    assert len(broken_paras) == 3, "Broken single snippet must be enriched into 3 structured paragraphs"
    assert "Pidato Prabowo dalam 2 Tahun: Bertabur Makian dan Ancaman Tempo.co" not in broken_paras[0], "Must not display the broken single title string"
    print(f"        * P1: {broken_paras[0][:75]}...")
    print(f"        * P2: {broken_paras[1][:75]}...")
    print(f"        * P3: {broken_paras[2][:75]}...")
    print(f"   [OK] Topic Summary: {broken_topic}")
    assert "Politik" in broken_topic, "Prabowo speech article must be classified into Politik topic"

    print("\n--- 4. Testing Export News Topic Classification Example ---")
    test_export_item = ArticleItem(
        id="test-ekspor-nikel",
        title="Kinerja Ekspor Nikel dan Bauksit Indonesia Naik 18 Persen",
        url="https://www.cnbcindonesia.com/market/ekspor-nikel",
        publisher="CNBC Indonesia",
        category="Ekonomi",
        published_at="2026-11-01T10:00:00Z",
        snippet="Aktivitas ekspor komoditas nikel mencatat lonjakan nilai devisa.",
        image_url="",
        source_type="test"
    )
    store.save_article(test_export_item)
    r_export = client.get('/api/v1/article/test-ekspor-nikel')
    assert r_export.status_code == 200
    export_topic = r_export.get_json()['article'].get('topic_summary', '')
    print(f"   [OK] Export Article Topic: {export_topic}")
    assert "Ekonomi" in export_topic and "Perdagangan" in export_topic, "Export news must classify into Ekonomi & Perdagangan"

    print("\n=======================================================")
    print(" >>> SEMUA TEST PARAGRAF & RINGKASAN TOPIK 100% SUKSES! <<<")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
