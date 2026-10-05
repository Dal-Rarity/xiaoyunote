"""逐段打点：embedding / qdrant / rerank / llm"""
import asyncio
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai_app.services.embedding_client import embed_texts
from ai_app.services.rerank_client import rerank
from ai_app.services.retriever import retrieve
from ai_app.services.prompts import build_messages
from ai_app.services.llm_client import stream_chat
from ai_app.deps import qdrant
from ai_app.config import get_settings

s = get_settings()


async def main():
    q = "我关于《三体》写了什么？"
    user_id = 1

    t0 = time.time()
    vecs = await embed_texts([q])
    print(f"1. embedding: {(time.time()-t0)*1000:.0f} ms")

    t0 = time.time()
    hits = qdrant.search(
        collection_name=s.QDRANT_COLLECTION,
        query_vector=vecs[0],
        limit=s.RECALL_TOP_K,
        with_payload=True,
    )
    print(f"2. qdrant ({len(hits)} hits): {(time.time()-t0)*1000:.0f} ms")

    docs = [h.payload["text"] for h in hits]
    t0 = time.time()
    try:
        await rerank(q, docs, s.RERANK_TOP_N)
        print(f"3. rerank ({len(docs)} docs): {(time.time()-t0)*1000:.0f} ms")
    except Exception as e:
        print(f"3. rerank failed: {e}")

    t0 = time.time()
    r = await retrieve(q, user_id=user_id)
    print(f"4. full retrieve: {(time.time()-t0)*1000:.0f} ms")

    messages = build_messages(q, r.chunks)
    t0 = time.time()
    ttft = None
    chars = 0
    async for delta in stream_chat(messages):
        if ttft is None:
            ttft = (time.time() - t0) * 1000
        chars += len(delta)
    print(f"5. llm: TTFT={ttft:.0f} ms, total={(time.time()-t0)*1000:.0f} ms, chars={chars}")


if __name__ == "__main__":
    asyncio.run(main())