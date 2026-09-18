"""Sequential orchestration of reconnaissance plan items and discovered targets."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from core.recon_planner import ReconPlanItem, ReconPlanner
from core.recon_profile import ReconLevel
from core.recon_queue import QueuedTarget, ReconTargetQueue
from core.tool_adapter import NormalizedResult


class ReconController:
    """Coordinate planning without owning process or UI concerns."""

    def __init__(
        self,
        planner: ReconPlanner | None = None,
        level: ReconLevel = ReconLevel.QUICK,
        tool_keys: Iterable[str] | None = None,
    ):
        self.planner = planner or ReconPlanner()
        self.level = level
        self.tool_keys = tuple(tool_keys) if tool_keys is not None else None
        self.target_queue = ReconTargetQueue()
        self._pending: deque[ReconPlanItem] = deque()
        self._scheduled: set[tuple[str, str]] = set()
        self._active: ReconPlanItem | None = None

    def enqueue(self, targets: Iterable[QueuedTarget]) -> int:
        """Plan queued targets and return the number of newly scheduled tasks."""
        added = 0
        for item in targets:
            for plan_item in self.planner.plan_target(item, self.level, self.tool_keys):
                if self._schedule(plan_item):
                    added += 1
        return added

    def seed(self, values: Iterable[str]) -> int:
        """Add initial raw targets and schedule compatible tools for them."""
        for value in values:
            self.target_queue.add(value)
        return self.enqueue(self.target_queue.drain())

    def next_item(self) -> ReconPlanItem | None:
        if self._active is not None:
            return self._active
        if not self._pending:
            return None
        self._active = self._pending.popleft()
        return self._active

    def complete(self, result: NormalizedResult) -> int:
        """Finish the active task and schedule targets discovered by its result."""
        if self._active is None:
            raise RuntimeError("Нет активной задачи разведки.")

        self._active = None
        discovered = self.target_queue.add_result(result)
        return self.enqueue(self.target_queue.drain()) if discovered else 0

    def cancel(self) -> None:
        self._pending.clear()
        self._active = None

    def _schedule(self, item: ReconPlanItem) -> bool:
        key = (item.tool_key, item.target.target.normalized_value)
        if key in self._scheduled:
            return False
        self._scheduled.add(key)
        self._pending.append(item)
        return True

    def __len__(self) -> int:
        return len(self._pending) + (1 if self._active else 0)