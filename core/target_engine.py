"""Target classification and normalization for RED Kali reconnaissance flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


class TargetType(str, Enum):
    IP = "ip"
    CIDR = "cidr"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    USERNAME = "username"
    SOCIAL_USERNAME = "social_username"
    FILE = "file"
    DIRECTORY = "directory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IdentityTarget:
    raw_value: str
    normalized_value: str
    platform: str | None = None
    identifiers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Target:
    raw_value: str
    normalized_value: str
    target_type: TargetType
    identity: IdentityTarget | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return self.target_type != TargetType.UNKNOWN and not self.errors


_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\.?$",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()-]{6,24}$")


class TargetEngine:
    """Classifies a user supplied target without accessing the network."""

    def parse(self, raw_value: str) -> Target:
        raw = (raw_value or "").strip()
        if not raw:
            return Target(raw, "", TargetType.UNKNOWN, errors=("Введите цель.",))

        if raw.startswith("@"):
            username = raw[1:]
            if _USERNAME_RE.fullmatch(username):
                normalized = username.lower()
                return Target(raw, normalized, TargetType.SOCIAL_USERNAME,
                              IdentityTarget(raw, normalized, identifiers=(normalized,)))
            return Target(raw, raw, TargetType.UNKNOWN, errors=("Некорректный social username.",))

        if _EMAIL_RE.fullmatch(raw):
            return Target(raw, raw.lower(), TargetType.EMAIL)

        if _PHONE_RE.fullmatch(raw):
            normalized = "+" + re.sub(r"\D", "", raw)
            return Target(raw, normalized, TargetType.PHONE)

        ip_target = self._parse_ip(raw)
        if ip_target:
            return ip_target
        if re.fullmatch(r"[0-9.]+(?:/[0-9]{1,3})?", raw):
            return Target(raw, raw, TargetType.UNKNOWN, errors=("Некорректный IP-адрес или CIDR.",))

        if raw.startswith(("http://", "https://")):
            return self._parse_url(raw)

        if _DOMAIN_RE.fullmatch(raw):
            return Target(raw, raw.rstrip(".").lower(), TargetType.DOMAIN)

        if raw.startswith("/") or raw.startswith("./") or raw.startswith("../"):
            target_type = TargetType.DIRECTORY if raw.endswith("/") else TargetType.FILE
            return Target(raw, raw, target_type)

        if _USERNAME_RE.fullmatch(raw):
            normalized = raw.lower()
            return Target(raw, normalized, TargetType.USERNAME,
                          IdentityTarget(raw, normalized, identifiers=(normalized,)))

        return Target(raw, raw, TargetType.UNKNOWN, errors=("Не удалось определить тип цели.",))

    @staticmethod
    def _parse_ip(raw: str) -> Target | None:
        try:
            if "/" in raw:
                network = ipaddress.ip_network(raw, strict=False)
                return Target(raw, str(network), TargetType.CIDR)
            address = ipaddress.ip_address(raw)
            return Target(raw, str(address), TargetType.IP)
        except ValueError:
            return None

    @staticmethod
    def _parse_url(raw: str) -> Target:
        parsed = urlsplit(raw)
        if not parsed.hostname:
            return Target(raw, raw, TargetType.UNKNOWN, errors=("URL не содержит домен.",))
        host = parsed.hostname.lower()
        netloc = host if parsed.port is None else f"{host}:{parsed.port}"
        normalized = urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, ""))
        return Target(raw, normalized, TargetType.URL)


target_engine = TargetEngine()
