"""Unified, side-effect-free interface for external reconnaissance tools.

Adapters isolate tool availability checks and command construction from the UI.
Command execution remains the responsibility of ``CommandWorker``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import shutil
import subprocess
import re
from typing import Any, Iterable

from core.tools_db import TOOLS_DATABASE
from core.target_engine import Target, TargetType
from core.recon_profile import ReconLevel, build_profiled_command


class ToolState(str, Enum):
    READY = "ready"
    MISSING = "missing"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


@dataclass(frozen=True)
class ToolHealth:
    state: ToolState
    path: str | None
    version: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class NormalizedResult:
    """A stable envelope for parsers added in subsequent reconnaissance stages."""

    tool: str
    target: str
    records: list[dict[str, Any]]
    raw_output: str = ""


DEFAULT_TARGETS = {
    "social": ("username", "social_username", "url"),
    "accounts": ("domain", "email", "username"),
    "network": ("ip", "cidr", "domain", "url"),
    "other": ("file", "directory", "domain", "ip", "email"),
}


class ToolAdapter:
    """Adapter for one entry in ``TOOLS_DATABASE``.

    Existing command builders are intentionally reused while the application is
    migrated incrementally. New adapters can override ``build_command`` and
    ``parse_output`` without requiring changes in the interface.
    """

    def __init__(self, key: str, config: dict[str, Any]):
        self.key = key
        self.config = config
        self.name = config["name"]
        self.binary = config["binary"]
        self.supported_targets = tuple(config.get(
            "supported_targets", DEFAULT_TARGETS.get(config.get("category"), ("unknown",))
        ))
        self.capabilities = tuple(config.get("capabilities", ()))

    def is_installed(self) -> bool:
        return shutil.which(self.binary) is not None

    def health_check(self, include_version: bool = False) -> ToolHealth:
        path = shutil.which(self.binary)
        if not path:
            return ToolHealth(ToolState.MISSING, None, detail="Бинарник не найден в PATH")

        if self.config.get("requires_api_key"):
            return ToolHealth(
                ToolState.NOT_CONFIGURED,
                path,
                detail=self.config.get("configuration_hint", "Требуется настройка API"),
            )

        version = self._get_version(path) if include_version else None
        return ToolHealth(ToolState.READY, path, version)

    def _get_version(self, path: str) -> str | None:
        for argument in ("--version", "-V", "-v"):
            try:
                result = subprocess.run(
                    [path, argument], text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=1.5, check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            output = (result.stdout or "").strip().splitlines()
            if output:
                return output[0][:100]
        return None

    def build_command(
        self, target: str, options: dict[str, Any], sudo_active: bool,
        level: ReconLevel = ReconLevel.QUICK,
    ) -> list[str]:
        return build_profiled_command(
            self.key, target, options, sudo_active, self.config["cmd_builder"], level,
        )

    def supports(self, target: Target) -> bool:
        """Whether this adapter can handle a classified target."""
        return target.target_type.value in self.supported_targets

    def parse_output(self, target: str, output: str) -> NormalizedResult:
        """Convert common text output into stable records without losing raw data."""
        parsers = {
            "nmap": self._parse_nmap,
            "amass": self._parse_amass,
            "sherlock": self._parse_account_urls,
            "maigret": self._parse_account_urls,
        }
        parser = parsers.get(self.key, self._parse_lines)
        return NormalizedResult(self.key, target, parser(output), output)

    @staticmethod
    def _parse_lines(output: str) -> list[dict[str, Any]]:
        return [
            {"type": "line", "value": line.strip()}
            for line in output.splitlines()
            if line.strip()
        ]

    @staticmethod
    def _parse_amass(output: str) -> list[dict[str, Any]]:
        records = []
        for line in output.splitlines():
            value = line.strip()
            if not value or value.startswith("["):
                continue
            if re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", value):
                records.append({"type": "domain", "value": value.lower()})
        return records

    @staticmethod
    def _parse_account_urls(output: str) -> list[dict[str, Any]]:
        records = []
        for line in output.splitlines():
            urls = re.findall(r"https?://[^\s)]+", line)
            for url in urls:
                records.append({"type": "account", "url": url.rstrip(".,")})
        return records

    @staticmethod
    def _parse_nmap(output: str) -> list[dict[str, Any]]:
        records = []
        host_pattern = re.compile(r"Nmap scan report for (.+?)(?: \(([^)]+)\))?$")
        port_pattern = re.compile(
            r"^(\d+)/(tcp|udp)\s+(\S+)\s+(\S+)(?:\s+(.*))?$"
        )
        for line in output.splitlines():
            value = line.strip()
            host_match = host_pattern.match(value)
            if host_match:
                record = {"type": "host", "host": host_match.group(1)}
                if host_match.group(2):
                    record["ip"] = host_match.group(2)
                records.append(record)
                continue
            port_match = port_pattern.match(value)
            if port_match:
                records.append({
                    "type": "service",
                    "port": int(port_match.group(1)),
                    "protocol": port_match.group(2),
                    "state": port_match.group(3),
                    "service": port_match.group(4),
                    "version": (port_match.group(5) or "").strip(),
                })
        return records

    def normalize(self, target: str, output: str) -> NormalizedResult:
        return self.parse_output(target, output)


class ToolRegistry:
    def __init__(self, tools: dict[str, dict[str, Any]] | None = None):
        source = tools or TOOLS_DATABASE
        self._adapters = {key: ToolAdapter(key, config) for key, config in source.items()}

    def get(self, key: str) -> ToolAdapter:
        return self._adapters[key]

    def all(self) -> Iterable[ToolAdapter]:
        return self._adapters.values()

    def audit(self, include_version: bool = False) -> list[tuple[ToolAdapter, ToolHealth]]:
        return [(adapter, adapter.health_check(include_version)) for adapter in self.all()]


tool_registry = ToolRegistry()
