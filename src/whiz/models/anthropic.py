"""Anthropic model backend."""
from __future__ import annotations

import os
from typing import Any

from whiz.models.base import BaseModel, LLMResponse


class AnthropicModel(BaseModel):
    """Anthropic Claude chat completions backend."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
        **kwargs: Any,
    ):
        self.model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._extra_kwargs = kwargs

        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        effective_model = model or self.model

        # Anthropic expects system as a separate parameter
        system = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                anthropic_messages.append(msg)

        response = self._client.messages.create(
            model=effective_model,
            system=system,
            messages=anthropic_messages,
            max_tokens=4096,
            **{**self._extra_kwargs, **kwargs},
        )

        content = "".join(block.text for block in response.content if hasattr(block, "text"))
        usage = response.usage
        return LLMResponse(
            content=content,
            model=effective_model,
            prompt_tokens=usage.input_tokens if usage else 0,
            completion_tokens=usage.output_tokens if usage else 0,
            total_tokens=(usage.input_tokens + usage.output_tokens) if usage else 0,
        )
