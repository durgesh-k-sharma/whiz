"""Ollama model backend."""
from __future__ import annotations

import os
from typing import Any

import httpx

from whiz.models.base import BaseModel, LLMResponse


class OllamaModel(BaseModel):
    """Ollama local model backend."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str | None = None,
        **kwargs: Any,
    ):
        self.model = model
        self._base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._extra_kwargs = kwargs

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        effective_model = model or self.model

        response = httpx.post(
            f"{self._base_url}/api/chat",
            json={
                "model": effective_model,
                "messages": messages,
                "stream": False,
                **{**self._extra_kwargs, **kwargs},
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "")
        return LLMResponse(
            content=content,
            model=effective_model,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
        )
