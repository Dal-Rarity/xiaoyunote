# 语料说明（articles.jsonl）

## 来源
- 数据库：MySQL `xiaoyushouji`（127.0.0.1:3307）
- 表：`article`
- 过滤条件：`drafted=1`（正式发布）
- 导出脚本：`scripts/export_corpus.py`

## 字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `article_id` | int | 文章 ID，主键 |
| `title` | string | 标题 |
| `content` | string | 正文（已过滤空文/脏数据） |
| `category` | string | 分类，来自 `label_name` |
| `tags` | list[str] | 标签列表，由 `article_tag` 逗号拆分 |
| `created_at` | string | 创建时间 |

## 类别分布（截至 2026-09-30）

| 类别 | 篇数 |
|---|---|
| 日记 | 24 |
| 阅读笔记 | 17 |
| 周记 | 16 |
| 备忘录 | 16 |
| 影后观感 | 15 |
| **合计** | **88** |

## 更新方式

1. 主站写/改文章后，确保 `drafted=1`；
2. 重跑导出脚本：

```powershell
cd services/ai_service
python scripts/export_corpus.py