# 参数冻结表（params-frozen-v1）

## 冻结时间
2026-10-03

## 实验记录

| 实验 | 变量 | 平均分 | 决策 |
|---|---|---|---|
| A | 基线（阈值0.4，TopK5） | 2.88 | 对照 |
| B | 阈值 0.4→0.2 | 3.42 | ✅ 保留 |
| C | TopK 5→15 | 3.83 | ✅ 保留 |
| D | 提示词分点 | 3.25 | ❌ 回滚 |
| E | 换模型 | — | 取消（保留 flash） |

## 冻结参数

| 参数 | 冻结值 | 来源 |
|---|---|---|
| 检索模式 | 向量检索 + Rerank | T6-T7 实测 |
| Score 阈值 | **0.2** | 实验 B |
| Top K | **15** | 实验 C |
| Rerank Top N | 5 | 默认 |
| 温度 | 0.3 | 稳定性优先 |
| 系统提示词 | prompt-system-v1（身份修正后，无分点） | T8 + 实验 D 回滚 |
| LLM | qwen3.8-flash | 性价比 + 长上下文 |
| Embedding | bge-m3 | T2 |
| Rerank | bge-reranker-v2-m3 | T2 |

## 多用户隔离说明
- Dify 验证阶段：全量语料，参数可迁移；
- 工程化阶段（T12/T13/T17）：Qdrant payload 按 user_id 过滤；
- 收藏/喜欢/评论：作为额外 data_type 入库，支持行为查询。

## 备注
- 最终平均分：3.83（实验 C 配置）
- 拒答题（Q13-15）全部正确
- 待优化项：Q4/6/8/10 仍部分失败，工程化阶段用多用户隔离 + 行为数据补充


## T13 检索评测结果（2026-10-04）

### 精确题 Recall@5
- 8/8 = 1.0（目标 ≥ 0.8，达标）

### 开放题命中率
- 3/3 = 1.0

### 多用户隔离验证
- user_id=1 召回 [75, 70, 77, 87, 76]
- user_id=2 召回 [11, 21, 4, 29]（无 75）
- user_id=4 召回 [30, 16, 26, 9, 29]（无 75）
- 结论：隔离生效

### 行为数据检索
- data_type=collection / comment：可过滤
- data_type=favorite / praise：待补测

### 安全题（Q12-Q15）
- 检索层未拒答（阈值 0.2 拦不住语义相似问题）
- 预期行为：最终拒答由 LLM 层判断（T8 已验证）
- T14 复现 LLM 层拒答逻辑后复测

### 备注
- Q6/Q7/Q10 为聚合/开放题，不适用精确 ID 匹配
- 评测脚本已区分精确题/开放题/安全题


## T14 流式生成实测（2026-10-04）

| 环节 | 耗时 |
|---|---|
| embedding | 334 ms |
| qdrant search | 23 ms |
| rerank | 724 ms |
| full retrieve | 429 ms |
| LLM TTFT | 782 ms |
| LLM total | 4372 ms |

### 优化记录
- 问题：qwen3.8-flash 默认开启 thinking 模式，TTFT 3.8s
- 解决：API 传 enable_thinking: False
- 效果：TTFT 从 3791 ms → 782 ms（↓79%）

### 防幻觉核对
- 对照 75 原文逐句核对，回答无编造
- 引用编号 [1] [2] 正确区分来源

## T16 Redis 降级验证（2026-10-04）

### 场景
虚拟机 `docker stop redis-stack`，观察服务行为。

### 实测日志
- 14:17-14:18：`cache_hit` 正常命中
- 14:20:37：`cache get failed (fail-open): Timeout connecting to server`
- 14:20:44：`cache set failed (fail-open): Timeout connecting to server`
- 所有请求仍返回 HTTP 200 OK

### 结论
- ✅ fail-open 降级生效，Redis 挂不影响主链路
- ✅ 日志 warning 明确，便于排障
- ✅ 恢复后自动重连