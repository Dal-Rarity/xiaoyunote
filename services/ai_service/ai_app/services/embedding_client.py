from ai_app.config import get_settings
from ai_app.deps import ollama

s = get_settings()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化，长度与输入一一对应"""
    out: list[list[float]] = []
    for i in range(0, len(texts), s.EMBED_BATCH):
        batch = texts[i : i + s.EMBED_BATCH]
        r = await ollama.embeddings.create(model=s.EMBED_MODEL, input=batch)
        out.extend([d.embedding for d in r.data])
    return out