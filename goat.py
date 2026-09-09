#!/usr/bin/env python3
"""Shim. The CLI lives in src/goat/main.py (`pip install -e .` → `goat`)."""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent / "src")
sys.path.insert(0, _SRC)

if __name__ != "__main__":
    import importlib

    sys.modules.pop("goat", None)
    sys.modules[__name__] = importlib.import_module("goat")
else:
    from goat.main import main  # noqa: E402

    raise SystemExit(main())
