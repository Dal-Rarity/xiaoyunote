import asyncio
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))
TOKEN = os.getenv("INTERNAL_TOKEN", "")
URL = "http://127.0.0.1:8100/api/ai/chat/stream"
HEADERS = {"Content-Type": "application/json", "X-User-Id": "1", "X-Internal-Token": TOKEN}


async def ask(q: str, sid: str):
    print(f"\n>>> Q: {q}")
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", URL, json={"question": q, "session_id": sid}, headers=HEADERS) as r:
            async for line in r.aiter_lines():
                if line.startswith("data:") and line != "data: [DONE]":
                    try:
                        obj = json.loads(line[5:].strip())
                        if obj["type"] == "delta":
                            print(obj["text"], end="", flush=True)
                    except Exception:
                        pass
    print()


async def main():
    sid = "sess-multi-001"
    await ask("我最近写了什么？", sid)
    await ask("那篇三体读后感讲了什么？", sid)


if __name__ == "__main__":
    asyncio.run(main())