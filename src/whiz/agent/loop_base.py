"""Shared base classes for agent loops."""
from __future__ import annotations

from dataclasses import dataclass, field


class RecursionError(Exception):
    """Raised when max recursion depth is exceeded."""
    pass


@dataclass
class SubLLMManager:
    """Tracks recursion depth across parent-child session trees."""
    max_depth: int = 5
    _depth: int = field(default=0, init=False, repr=False)

    @property
    def current_depth(self) -> int:
        return self._depth

    def enter(self) -> None:
        if self._depth >= self.max_depth:
            raise RecursionError(
                f"Max recursion depth ({self.max_depth}) exceeded. "
                f"Current depth: {self._depth}"
            )
        self._depth += 1

    def exit(self) -> None:
        if self._depth > 0:
            self._depth -= 1
