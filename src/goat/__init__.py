"""SkillsGoat — vulnerable-by-design AI agent skill collection."""

from __future__ import annotations

from typing import Any

__all__ = ["main", "discover_entries", "discover_chains"]

# Lazily forwarded from goat.main so tools/link_skills.py (the --index-only /
# --goat linker) and other callers can use the package-level API.
_FORWARDED = {"main", "discover_entries", "discover_chains"}


def __getattr__(name: str) -> Any:
    if name in _FORWARDED:
        import importlib
        _main_mod = importlib.import_module("goat.main")
        return getattr(_main_mod, name)
    raise AttributeError(name)
