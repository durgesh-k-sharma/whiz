"""OpenRouter model backend (uses OpenAI-compatible API)."""
from __future__ import annotations

import os
from typing import Any

from whiz.models.openai import OpenAIModel


class OpenRouterModel(OpenAIModel):
    """OpenRouter backend -- routes to multiple models through OpenAI-compatible API."""

    def __init__(
        self,
        model: str = "openrouter/auto",
        api_key: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            model=model.replace("openrouter/", ""),
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1",
            **kwargs,
        )
