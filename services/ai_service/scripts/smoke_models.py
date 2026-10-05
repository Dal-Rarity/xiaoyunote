import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1) Embedding: 本地 Ollama
r = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama").embeddings.create(
    model="bge-m3", input=["昆明理工大学的天"]
)
print("embed dim =", len(r.data[0].embedding))  # 期望 1024

# 2) Rerank: 硅基流动
r = httpx.post(
    "https://api.siliconflow.cn/v1/rerank",
    headers={"Authorization": f"Bearer {os.environ['RERANK_API_KEY']}"},
    json={
        "model": "BAAI/bge-reranker-v2-m3",
        "query": "我最喜欢的科幻电影",
        "documents": ["《流浪地球》观后感", "今天食堂吃什么"],
        "top_n": 2,
    },
    timeout=10,
)
print("rerank =", [(i["index"], round(i["relevance_score"], 3)) for i in r.json()["results"]])

# 3) LLM: 通义
r = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
print(r.chat.completions.create(
    model="qwen-plus",
    max_tokens=32,
    messages=[{"role": "user", "content": "用一句话自我介绍"}],
).choices[0].message.content)