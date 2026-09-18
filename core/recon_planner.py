"""Build executable reconnaissance plans from queued targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.recon_profile import ReconLevel
from core.recon_queue import QueuedTarget
from core.tool_adapter import ToolAdapter, ToolRegistry, tool_registry


@dataclass(frozen=True)
class ReconPlanItem:
    target: QueuedTarget
    adapter: ToolAdapter
    level: ReconLevel

    @property
    def tool_key(self) -> str:
        return self.adapter.key

    def build_command(self, options: dict | None = None, sudo_active: bool = False) -> list[str]:
        return self.adapter.build_command(
            self.target.target.normalized_value,
            options or {},
            sudo_active,
            self.level,
        )


class ReconPlanner:
    """Select compatible adapters while leaving execution to the controller."""

    def __init__(self, registry: ToolRegistry = tool_registry):
        self.registry = registry

    def plan_target(
        self,
        target: QueuedTarget,
        level: ReconLevel = ReconLevel.QUICK,
        tool_keys: Iterable[str] | None = None,
    ) -> list[ReconPlanItem]:
        adapters = (
            (self.registry.get(key) for key in tool_keys)
            if tool_keys is not None
            else self.registry.all()
        )
        return [
            ReconPlanItem(target, adapter, level)
            for adapter in adapters
            if adapter.supports(target.target)
        ]

    def plan_queue(
        self,
        queued_targets: Iterable[QueuedTarget],
        level: ReconLevel = ReconLevel.QUICK,
        tool_keys: Iterable[str] | None = None,
    ) -> list[ReconPlanItem]:
        plan = []
        for target in queued_targets:
            plan.extend(self.plan_target(target, level, tool_keys))
        return plan