"""Three-layer memory system for placeholder values: session, domain, global."""

import json
from pathlib import Path


class Memory:
    """Manages placeholder value storage across three layers.

    Layers (checked in order):
    - session: changes per session (domain + phase), not persisted
    - domain: changes per domain, persisted
    - global: never changes, persisted
    """

    def __init__(self, persist_path: Path):
        self._persist_path = persist_path
        self._session: dict[str, str] = {}
        self._domain: dict[str, dict[str, str]] = {}  # domain_key -> {name: value}
        self._global: dict[str, str] = {}
        self._current_domain_key: str = ""
        self._load()

    def _load(self):
        if self._persist_path.exists():
            try:
                data = json.loads(
                    self._persist_path.read_text(encoding="utf-8")
                )
                self._domain = data.get("domain", {})
                self._global = data.get("global", {})
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "domain": self._domain,
            "global": self._global,
        }
        self._persist_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_session_context(self, domain: str, phase: str):
        """Set the current session context. Clears session-level values."""
        self._current_domain_key = f"{domain}:{phase}"
        self._session = {}

    def get(self, name: str) -> str | None:
        """Look up a placeholder value: session -> domain -> global."""
        if name in self._session:
            return self._session[name]

        domain_values = self._domain.get(self._current_domain_key, {})
        if name in domain_values:
            return domain_values[name]

        if name in self._global:
            return self._global[name]

        return None

    def set_session(self, name: str, value: str):
        self._session[name] = value

    def set_domain(self, name: str, value: str):
        if self._current_domain_key not in self._domain:
            self._domain[self._current_domain_key] = {}
        self._domain[self._current_domain_key][name] = value

    def set_global(self, name: str, value: str):
        self._global[name] = value

    def get_all_sessions(self) -> list[str]:
        """Return all known domain:phase keys."""
        return list(self._domain.keys())
