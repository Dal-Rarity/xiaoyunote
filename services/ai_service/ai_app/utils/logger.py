"""
结构化日志：一行一条 JSON
- 控制台输出 JSON（便于 grep/jq）
- 文件滚动归档，保留 14 天
"""
import sys
from loguru import logger

# 移除默认 handler
logger.remove()

# 控制台：JSON 一行一条
logger.add(
    sys.stdout,
    serialize=True,
    level="INFO",
    enqueue=True,
)

# 文件：滚动归档
logger.add(
    "logs/ai_{time:YYYY-MM-DD}.log",
    rotation="50MB",
    retention="14 days",
    serialize=True,
    level="INFO",
    enqueue=True,
)

__all__ = ["logger"]