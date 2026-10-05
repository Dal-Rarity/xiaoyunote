"""
MySQL -> JSONL 语料导出脚本
表：article（drafted=1 为正式发布）
输出：data/corpus/articles.jsonl，每行一个 JSON 对象（含 user_id）
"""
import json
import os
import sys
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

import pymysql
from ai_app.config import get_settings

OUT_PATH = os.path.join(BASE_DIR, "data", "corpus", "articles.jsonl")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)


def _dsn_to_kwargs(dsn):
    u = urlparse(dsn)
    charset = "utf8mb4"
    if "charset=" in (u.query or ""):
        charset = dict(p.split("=", 1) for p in u.query.split("&")).get("charset", charset)
    return dict(
        host=u.hostname,
        port=u.port or 3306,
        user=u.username,
        password=u.password or "",
        database=u.path.lstrip("/"),
        charset=charset,
    )


conn = pymysql.connect(**_dsn_to_kwargs(get_settings().MYSQL_DSN))

cur = conn.cursor()
cur.execute("""
    SELECT article_id, user_id, title, article_content,
           label_name, article_tag, create_time
    FROM article
    WHERE drafted = 1
""")

n = 0
skipped = 0
with open(OUT_PATH, "w", encoding="utf-8") as f:
    for aid, uid, title, body, cat, tags, created in cur.fetchall():
        body = (body or "").strip()
        if len(body) < 30 or "<script" in body.lower():
            skipped += 1
            continue
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        row = {
            "article_id": aid,
            "user_id": uid,
            "title": title,
            "content": body,
            "category": cat or "未分类",
            "tags": tag_list,
            "created_at": str(created),
        }
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += 1

conn.close()
print(f"exported {n} articles, skipped {skipped}")