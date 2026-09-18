"""Process management for stopping reconnaissance jobs and descendants."""

from __future__ import annotations

import os
import signal
import subprocess
from collections import defaultdict
from typing import Iterable


class ProcessManager:
    """Track active processes and terminate their process groups on cancel."""

    def __init__(self):
        self._tracks: dict[int, set[int]] = defaultdict(set)
        self.active_pids: set[int] = set()

    def register(self, pid: int, children: Iterable[int] | None = None):
        self.active_pids.add(pid)
        self._tracks[pid] = set(children or ())

    def add_child(self, parent_pid: int, child_pid: int):
        self._tracks.setdefault(parent_pid, set()).add(child_pid)
        self.active_pids.add(child_pid)

    def cancel(self, pid: int) -> None:
        if pid not in self.active_pids:
            return

        for candidate in self._collect_descendants(pid):
            try:
                os.killpg(candidate, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

        self._tracks.pop(pid, None)

    def _collect_descendants(self, pid: int) -> set[int]:
        collected: set[int] = {pid}
        stack = [pid]
        while stack:
            current = stack.pop()
            for child in self._tracks.get(current, set()):
                if child not in collected:
                    collected.add(child)
                    stack.append(child)
        return collected

    def clear(self):
        for pid in list(self.active_pids):
            self.cancel(pid)
