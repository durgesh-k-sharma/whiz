"""Mock LLM for testing without calling real model APIs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from whiz.models.base import LLMResponse


@dataclass
class MockLLM:
    """An LLM that returns scripted responses in sequence.

    Usage:
        mock = MockLLM(responses=["hello", "world"])
        mock.chat_completion([{"role": "user", "content": "hi"}])
        # -> LLMResponse(content="hello", ...)
    """

    responses: list[str]
    _call_count: int = field(default=0, init=False, repr=False)
    _calls: list[list[dict[str, str]]] = field(default_factory=list, init=False, repr=False)

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        self._calls.append(list(messages))
        if self._call_count >= len(self.responses):
            raise IndexError(
                f"MockLLM exhausted: call {self._call_count + 1} but only "
                f"{len(self.responses)} responses scripted"
            )
        response = self.responses[self._call_count]
        self._call_count += 1
        return LLMResponse(
            content=response,
            model=model or "mock",
            prompt_tokens=10,
            completion_tokens=len(response.split()),
            total_tokens=10 + len(response.split()),
        )

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def calls(self) -> list[list[dict[str, str]]]:
        return self._calls

    def assert_called_with(self, messages: list[dict[str, str]]) -> None:
        assert self._calls[-1] == messages, (
            f"Last call mismatch.\nExpected: {messages}\nActual: {self._calls[-1]}"
        )
