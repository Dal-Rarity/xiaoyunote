from loguru import logger

from ai_app.config import get_settings
from ai_app.deps import llm

s = get_settings()


async def stream_chat(messages: list[dict]):
    """
    异步生成器，逐块 yield LLM 输出的文本。
    主模型失败自动切备选模型。
    """
    try:
        resp = await llm.chat.completions.create(
            model=s.LLM_MODEL,
            messages=messages,
            stream=True,
            temperature=s.LLM_TEMPERATURE,
            max_tokens=s.LLM_MAX_TOKEN,
            extra_body={"enable_thinking": False},  # ← 关闭思考
        )
    except Exception as e:
        logger.warning(f"LLM {s.LLM_MODEL} failed: {e}, fallback to {s.LLM_FALLBACK_MODEL}")
        resp = await llm.chat.completions.create(
            model=s.LLM_FALLBACK_MODEL,
            messages=messages,
            stream=True,
            temperature=s.LLM_TEMPERATURE,
            max_tokens=s.LLM_MAX_TOKEN,
        )

    async for chunk in resp:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content