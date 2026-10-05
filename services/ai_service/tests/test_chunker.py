from ai_app.services.chunker import chunk_article, chunk_behavior, clean_text


def test_clean_html():
    assert "<p>" not in clean_text("<p>你好</p>")


def test_short_skipped():
    assert chunk_article({"article_id": 1, "user_id": 1, "title": "t",
                          "content": "太短", "category": "日记",
                          "tags": [], "created_at": ""}) == []


def test_header_and_user():
    a = {"article_id": 1, "user_id": 7, "title": "标题",
         "content": "正文" * 100, "category": "日记",
         "tags": ["x"], "created_at": "2026-01-01"}
    chunks = chunk_article(a)
    assert chunks and "标题: 标题" in chunks[0].text
    assert chunks[0].user_id == 7


def test_behavior_source_id():
    row = {"user_id": 7, "article_id": 5, "title": "影评",
           "category": "影后观感", "source_id": 100}
    chunks = chunk_behavior(row, "collection")
    assert chunks[0].data_type == "collection"
    assert chunks[0].source_id == 100
    assert "收藏" in chunks[0].text