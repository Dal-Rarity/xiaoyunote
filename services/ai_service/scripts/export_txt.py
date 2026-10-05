import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(BASE_DIR, "data", "corpus")
TXT_DIR = os.path.join(CORPUS_DIR, "txt")

os.makedirs(TXT_DIR, exist_ok=True)

jsonl_path = os.path.join(CORPUS_DIR, "articles.jsonl")
rows = [json.loads(l) for l in open(jsonl_path, encoding="utf-8")]

def clean_text(text: str) -> str:
    """清洗 HTML 标签和多余空白"""
    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 移除多余空行（连续 3 个以上换行变成 2 个）
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 移除行首行尾多余空格
    lines = [line.strip() for line in text.split("\n")]
    # 过滤空行
    lines = [line for line in lines if line]
    return "\n\n".join(lines)

for r in rows:
    fname = os.path.join(TXT_DIR, f"{r['article_id']:03d}.txt")
    content = clean_text(r["content"])
    # 如果清洗后内容太短，跳过
    if len(content) < 30:
        continue
    with open(fname, "w", encoding="utf-8") as f:
        f.write(f"标题: {r['title']}\n")
        f.write(f"分类: {r['category']}\n")
        f.write(f"标签: {', '.join(r['tags'])}\n")
        f.write(f"日期: {r['created_at']}\n\n")
        f.write(content)

print(f"生成 {len(rows)} 个 TXT 文件（已清洗 HTML），目录：{TXT_DIR}")