import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_app.config import get_settings
from ai_app.models.dto import Chunk

s = get_settings()

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=s.CHUNK_SIZE,          # 800
    chunk_overlap=s.CHUNK_OVERLAP,    # 50
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    length_function=len,
)


def clean_text(text: str) -> str:
    """清洗 HTML 与多余空白"""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines)


def chunk_article(a: dict) -> list[Chunk]:
    """
    a: {article_id, user_id, title, content, category, tags, created_at}
    每块 text = 元数据头 + 正文片段
    """
    body = clean_text(a.get("content") or "")
    if len(body) < 30:
        return []

    header = (
        f"标题: {a['title']}\n"
        f"分类: {a['category']}\n"
        f"标签: {', '.join(a.get('tags') or [])}\n"
        f"日期: {a['created_at'][:10]}\n"
    )

    chunks = []
    for idx, piece in enumerate(_splitter.split_text(body)):
        chunks.append(
            Chunk(
                point_id="",
                user_id=a["user_id"],
                data_type="article",
                article_id=a["article_id"],
                title=a["title"],
                chunk_index=idx,
                text=header + piece,
                category=a["category"],
                tags=a.get("tags") or [],
                created_at=a["created_at"],
            )
        )
    return chunks


def chunk_behavior(row: dict, data_type: str) -> list[Chunk]:
    """收藏 / 喜欢 / 点赞 / 评论 → 单块"""
    title = row.get("title", "")
    category = row.get("category", "")
    extra = row.get("extra", "")

    if data_type == "collection":
        text = f"用户收藏了文章《{title}》，分类：{category}"
    elif data_type == "favorite":
        text = f"用户喜欢文章《{title}》，分类：{category}"
    elif data_type == "praise":
        text = f"用户点赞了文章《{title}》，分类：{category}"
    elif data_type == "comment":
        text = f"用户在《{title}》下评论：{extra}"
    else:
        text = str(row)

    return [
        Chunk(
            point_id="",
            user_id=row["user_id"],
            data_type=data_type,
            article_id=row["article_id"],
            title=title,
            chunk_index=0,
            text=text,
            category=category,
            tags=[],
            created_at=str(row.get("created_at", "")),
            source_id=row.get("source_id", 0),  # ← 新增
        )
    ]