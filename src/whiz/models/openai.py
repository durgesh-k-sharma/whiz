"""OpenAI model backend."""
from __future__ import annotations

import os
from typing import Any

from whiz.models.base import BaseModel, LLMResponse


class OpenAIModel(BaseModel):
    """OpenAI chat completions backend."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        self.model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url
        self._extra_kwargs = kwargs

        try:
            from openai import OpenAI
            client_kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client = OpenAI(**client_kwargs)
        except ImportError:
            raise RuntimeError(
                "openai package not installed. Install with: pip install openai"
            )

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        effective_model = model or self.model
        response = self._client.chat.completions.create(
            model=effective_model,
            messages=messages,
            **{**self._extra_kwargs, **kwargs},
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=effective_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )
