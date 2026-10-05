# 环境自检清单（T1）

- [x] 虚拟机 Qdrant 容器 Up，端口 0.0.0.0:6333
- [x] Windows 可访问 http://192.168.56.200:6333/collections
- [x] Redis 端口 6379 连通
- [x] Windows Ollama 运行，ollama list 含 bge-m3
- [x] OLLAMA_HOST=0.0.0.0 已设置并重启
- [x] Windows 防火墙放行 11434
- [x] 虚拟机可访问 http://192.168.56.1:11434/api/tags
- [ ] Dify 本地可登录
- [x] .env 中 VM_IP 与 WIN_IP 已填写



# 模型接线清单（T2）

| 供应商 | Base URL | 模型名 | Key 位置 | 用途 | 计费 |
|---|---|---|---|---|---|
| Ollama | http://host.docker.internal:11434 | bge-m3 | 无需 | Embedding | 免费本地 |
| 硅基流动 | https://api.siliconflow.cn/v1 | BAAI/bge-reranker-v2-m3 | .env / Dify | Rerank | 免费档 |
| 通义 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus | .env / Dify | LLM 主力 | 按量 |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat | 待填 | LLM 备选 | 按量 |

## 实测备注
- Rerank 对相关文档打分约 0.30（非 0.87），T13 阈值 0.35 需重新校准。
- Ollama 首次调用加载模型约 14s，之后 8-9ms。