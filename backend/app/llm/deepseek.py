"""DeepSeek LLM client.

DeepSeek exposes an OpenAI-compatible API, so we reuse `langchain_openai.ChatOpenAI`
with a custom base_url. The same client is shared by every agent.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings


@lru_cache(maxsize=4)
def get_llm(temperature: float = 0.1, model: str | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=temperature,
        max_retries=3,
        timeout=120,
    )
