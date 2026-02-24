"""LLM configuration settings extracted from DeepSeek client."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class LLMConfig:
    """LLM provider configuration."""

    api_key: str
    model: str
    base_url: str = "https://api.deepseek.com"
    temperature: float = 0.7
    max_tokens: int = 1024
    system_prompt: Optional[str] = None


def get_config() -> LLMConfig:
    """Load LLM configuration from environment variables.

    Returns:
        LLMConfig: Configuration instance with loaded values.

    Raises:
        ValueError: If required environment variables are missing.
    """
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not found in environment")

    return LLMConfig(
        api_key=api_key,
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
        system_prompt=os.getenv("LLM_SYSTEM_PROMPT"),
    )
