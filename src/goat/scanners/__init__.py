"""Optional scanner adapters.

`goat scan` does **not** use this package; it shells out via SCANNER_CONFIGS
in goat.main. These modules are sketches. A broken adapter must not prevent
`import goat`.
"""

from __future__ import annotations

import importlib
import sys

from .base import (
    ChainScanResult,
    ScanResult,
    ScannerAdapter,
    create_scanner,
    get_scanner,
    list_available_scanners,
    list_scanners,
    register_scanner,
)

for _mod in ("skillspector", "cisco", "snyk", "nova"):
    try:
        importlib.import_module(f".{_mod}", __package__)
    except Exception as exc:  # pragma: no cover
        print(f"warning: scanner {_mod!r} failed to load: {exc}", file=sys.stderr)

__all__ = [
    "ScanResult",
    "ChainScanResult",
    "ScannerAdapter",
    "register_scanner",
    "get_scanner",
    "list_scanners",
    "create_scanner",
    "list_available_scanners",
]
