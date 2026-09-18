"""Target queue for feeding normalized reconnaissance results into a planner."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from core.target_engine import Target, target_engine
from core.tool_adapter import NormalizedResult


@dataclass(frozen=True)
class QueuedTarget:
    target: Target
    source_tool: str | None = None
    source_target: str | None = None


class ReconTargetQueue:
    """FIFO queue that accepts only valid, unique targets."""

    def __init__(self, initial_targets: Iterable[str] = ()):
        self._pending: deque[QueuedTarget] = deque()
        self._seen: set[tuple[str, str]] = set()
        for value in initial_targets:
            self.add(value)

    def add(
        self,
        value: str,
        source_tool: str | None = None,
        source_target: str | None = None,
    ) -> Target | None:
        target = target_engine.parse(value)
        if not target.is_valid:
            return None

        key = (target.target_type.value, target.normalized_value)
        if key in self._seen:
            return target

        self._seen.add(key)
        self._pending.append(QueuedTarget(target, source_tool, source_target))
        return target

    def add_result(self, result: NormalizedResult) -> list[Target]:
        """Create targets from records that have a direct Target Engine value."""
        added = []
        for record in result.records:
            value = self._record_value(record)
            if value is None:
                continue
            candidate = target_engine.parse(value)
            if not candidate.is_valid:
                continue
            key = (candidate.target_type.value, candidate.normalized_value)
            if key in self._seen:
                continue
            target = self.add(value, result.tool, result.target)
            if target is not None:
                added.append(target)
        return added

    @staticmethod
    def _record_value(record: dict) -> str | None:
        record_type = record.get("type")
        if record_type == "domain":
            return record.get("value")
        if record_type == "account":
            return record.get("url")
        if record_type == "host":
            return record.get("ip") or record.get("host")
        return None

    def pop(self) -> QueuedTarget | None:
        return self._pending.popleft() if self._pending else None

    def drain(self) -> list[QueuedTarget]:
        items = list(self._pending)
        self._pending.clear()
        return items

    def __len__(self) -> int:
        return len(self._pending)

    def __contains__(self, value: str) -> bool:
        target = target_engine.parse(value)
        return target.is_valid and (
            target.target_type.value, target.normalized_value
        ) in self._seen