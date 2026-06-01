"""Trajectory logging: write Session execution logs to disk and terminal."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TrajectoryEntry:
    timestamp: str
    round_num: int
    event_type: str  # "code", "output", "error", "complete", "compaction", "steering"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TrajectoryLogger:
    def __init__(self, log_dir: Path | None = None, verbose: bool = False):
        self.log_dir = log_dir or (Path.home() / ".whiz" / "logs")
        self.verbose = verbose
        self.entries: list[TrajectoryEntry] = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(
        self,
        round_num: int,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        verbose_only: bool = False,
    ) -> TrajectoryEntry:
        entry = TrajectoryEntry(
            timestamp=datetime.now().isoformat(),
            round_num=round_num,
            event_type=event_type,
            content=content,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        if self.verbose and verbose_only:
            self._print(entry)
        return entry

    def _print(self, entry: TrajectoryEntry) -> None:
        prefix = f"[round {entry.round_num}]"
        if entry.event_type == "code":
            print(f"{prefix} CODE:\n{entry.content}")
        elif entry.event_type == "output":
            print(f"{prefix} OUT:\n{entry.content}")
        elif entry.event_type == "error":
            print(f"{prefix} ERR: {entry.content}")
        elif entry.event_type == "complete":
            print(f"{prefix} DONE: {entry.content}")
        elif entry.event_type == "compaction":
            print(f"{prefix} COMPACT: {entry.content}")

    def save(self) -> Path | None:
        if not self.entries:
            return None
        self.log_dir.mkdir(parents=True, exist_ok=True)
        path = self.log_dir / f"session_{self._session_id}.jsonl"
        with open(path, "w") as f:
            for entry in self.entries:
                f.write(json.dumps(asdict(entry)) + "\n")
        return path

    @property
    def session_id(self) -> str:
        return self._session_id
