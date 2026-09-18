"""Reconnaissance intensity profiles shared by every tool adapter."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ReconLevel(str, Enum):
    QUICK = "quick"
    EXTENDED = "extended"
    DEEP = "deep"

    @property
    def display_name(self) -> str:
        return {
            ReconLevel.QUICK: "Quick — быстрый",
            ReconLevel.EXTENDED: "Extended — расширенный",
            ReconLevel.DEEP: "Deep — глубокий",
        }[self]


def coerce_level(value: ReconLevel | str) -> ReconLevel:
    return value if isinstance(value, ReconLevel) else ReconLevel(value)


def build_profiled_command(
    tool_key: str,
    target: str,
    options: dict[str, Any],
    sudo_active: bool,
    fallback_builder,
    level: ReconLevel | str,
) -> list[str]:
    """Build commands whose safety, depth and time cost follow ``level``.

    Unsupported tools keep their explicit card options; this gives every
    adapter a level-aware API while dedicated profiles are added incrementally.
    """
    level = coerce_level(level)

    if tool_key == "nmap":
        if level == ReconLevel.QUICK:
            scan_mode = "-sS" if sudo_active else "-sT"
            return ["nmap", scan_mode, "-T4", "--top-ports", "100", target]
        if level == ReconLevel.EXTENDED:
            scan_mode = "-sS" if sudo_active else "-sT"
            command = ["nmap", scan_mode, "-sV", "-T4", "--top-ports", "1000"]
            if sudo_active:
                command.append("-O")
            return command + [target]
        if level == ReconLevel.DEEP:
            scan_mode = "-sS" if sudo_active else "-sT"
            command = ["nmap", scan_mode, "-sV", "-T4", "-p-", "--script", "default,safe"]
            if sudo_active:
                command.append("-O")
            return command + [target]

    if tool_key == "amass":
        if level == ReconLevel.QUICK:
            return ["amass", "enum", "-passive", "-d", target]
        if level == ReconLevel.EXTENDED:
            return ["amass", "enum", "-active", "-d", target]
        if level == ReconLevel.DEEP:
            return ["amass", "enum", "-active", "-ip", "-d", target]

    if tool_key == "sherlock":
        tuned = dict(options)
        if level == ReconLevel.QUICK:
            tuned.update({"--timeout": 5, "--print-found": True})
        elif level == ReconLevel.EXTENDED:
            tuned.update({"--timeout": 10, "--print-found": True})
        elif level == ReconLevel.DEEP:
            tuned.update({"--timeout": 20, "--print-found": False})
        return fallback_builder(target, tuned, sudo_active)

    if tool_key == "maigret":
        tuned = dict(options)
        if level == ReconLevel.QUICK:
            tuned.update({"--timeout": 8, "--html": False, "--txt": False})
        elif level == ReconLevel.EXTENDED:
            tuned.update({"--timeout": 15, "--html": True, "--txt": True})
        elif level == ReconLevel.DEEP:
            tuned.update({"--timeout": 30, "--html": True, "--txt": True})
        return fallback_builder(target, tuned, sudo_active)

    return fallback_builder(target, options, sudo_active)
