"""
Scanner Adapter Framework for SkillsGoat

This module provides a plugin architecture for security scanners.
Each scanner implements the ScannerAdapter interface.
"""

# Import base classes first
from .base import (
    ScanResult,
    ChainScanResult,
    ScannerAdapter,
    register_scanner,
    get_scanner,
    list_scanners,
    create_scanner,
    list_available_scanners,
)

# Import scanner implementations to register them
from . import skillspector
from . import cisco
from . import snyk
from . import nova

# Re-export public API
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
