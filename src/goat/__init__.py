"""SkillsGoat — vulnerable-by-design AI agent skill collection."""

from __future__ import annotations

from typing import Any

__all__ = ["main"]


def __getattr__(name: str) -> Any:
    if name == "main":
        from goat.main import main as _main
        return _main
    raise AttributeError(name)
