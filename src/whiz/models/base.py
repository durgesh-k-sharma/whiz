"""Base model interface and response types."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class BaseModel:
    """Abstract base for all LLM backends.

    Subclasses must implement chat_completion().
    """

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        **kwargs,
    ) -> LLMResponse:
        raise NotImplementedError

    @staticmethod
    def _extract_text(raw: object) -> str:
        """Extract text content from a raw API response, handling various formats."""
        if isinstance(raw, str):
            return raw
        # Try common response shapes
        if hasattr(raw, "content"):
            content = raw.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Anthropic-style content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        parts.append(block)
                return "\n".join(parts)
        if isinstance(raw, dict):
            if "text" in raw:
                return raw["text"]
            if "content" in raw:
                return str(raw["content"])
        return str(raw)
