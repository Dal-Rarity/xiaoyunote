"""手动测试 chat_pipeline.stream_answer"""
import asyncio
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from ai_app.services.chat_pipeline import stream_answer


async def run_question(q: str, user_id: int = 1):
    print(f"\n=== {q} ===")
    t0 = time.time()
    async for ev in stream_answer(q, user_id=user_id):
        if ev["type"] == "sources":
            ids = [i["article_id"] for i in ev["items"]]
            print(f"[sources] {ids}")
        elif ev["type"] == "delta":
            print(ev["text"], end="", flush=True)
        elif ev["type"] == "refused":
            print(f"[refused] {ev['text']}")
        elif ev["type"] == "error":
            print(f"[error] {ev.get('message')}")
    print(f"\n耗时: {(time.time() - t0) * 1000:.0f} ms")


async def main():
    await run_question("我关于《三体》写了什么？")
    await run_question("今天昆明天气怎么样？")


if __name__ == "__main__":
    asyncio.run(main())