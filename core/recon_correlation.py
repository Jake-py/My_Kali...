"""Correlation and evidence aggregation for queued reconnaissance results."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.tool_adapter import NormalizedResult


class ReconCorrelator:
    """Collect normalized tool outputs into a de-duplicated evidence tree."""

    def __init__(self):
        self.tree: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(dict))
        self._evidence: dict[tuple[str, str, str], int] = {}
        self._observations: list[tuple[str, str, str, int]] = []
        self._counts: dict[str, int] = defaultdict(int)

    def ingest(self, result: NormalizedResult) -> dict[str, Any]:
        by_type: dict[str, int] = defaultdict(int)
        seen_for_result: set[tuple[str, str]] = set()

        for record in result.records:
            record_type = str(record.get("type", "unknown")).strip()
            if not record_type:
                continue

            key = self._record_key(record)
            if key is None:
                continue

            evidence_identity = (record_type, key)
            if evidence_identity in seen_for_result:
                continue
            seen_for_result.add(evidence_identity)

            aggregate_key = (result.target, record_type, key)
            self._evidence[aggregate_key] = self._evidence.get(aggregate_key, 0) + 1
            self.tree[result.target][record_type][key] = self._evidence[aggregate_key]
            self._observations.append((result.target, record_type, key, self._evidence[aggregate_key]))
            by_type[record_type] += 1
            self._counts[record_type] += 1

        return {
            "target": result.target,
            "tool": result.tool,
            "by_type": dict(by_type),
            "total": sum(by_type.values()),
        }

    def all_evidence(self) -> list[tuple[str, str, str, int]]:
        return list(self._observations)

    def report(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_evidence": len(self.all_evidence()),
                "by_type": dict(self._counts),
            },
            "tree": {
                target: {
                    record_type: dict(values)
                    for record_type, values in nested.items()
                }
                for target, nested in self.tree.items()
            },
        }

    @staticmethod
    def _record_key(record: dict[str, Any]) -> str | None:
        if record.get("type") in {"domain", "host", "ip", "email", "phone", "username", "file", "directory"}:
            return str(record.get("value") or record.get("host") or record.get("ip") or "").strip() or None
        if record.get("type") == "account":
            return str(record.get("url") or "").strip() or None
        if record.get("type") == "service":
            port = record.get("port")
            protocol = record.get("protocol", "tcp")
            service = record.get("service", "unknown")
            return f"{protocol}:{port}:{service}"
        return None
