"""Base classes for scanner adapters (unused by `goat scan` today)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ScanResult:
    """Result of scanning a single skill entry."""

    scanner: str
    entry_id: str
    status: str
    score: Optional[float] = None
    severity: Optional[str] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: str = ""
    scan_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainScanResult:
    """Result of scanning a compound chain."""

    scanner: str
    chain_id: str
    chain_name: str
    graph_verdict: str
    nodes: List[ScanResult]
    graph_result: Optional[ScanResult] = None
    scan_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScannerAdapter(ABC):
    """Abstract base class for scanner adapters."""

    name: str = "base"
    supported_modes: List[str] = ["atomic"]
    requires_api_key: bool = False

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        pass

    @abstractmethod
    def scan_chain(self, chain_dir: Path, mode: str = "composite", **kwargs) -> ChainScanResult:
        pass

    def get_version(self) -> str:
        return "unknown"

    def get_supported_modes(self) -> List[str]:
        return self.supported_modes

    def validate_config(self) -> List[str]:
        issues = []
        if not self.is_available():
            issues.append(f"{self.name}: not installed or not in PATH")
        return issues


_SCANNER_REGISTRY: Dict[str, type] = {}


def register_scanner(adapter_class: type) -> None:
    if not issubclass(adapter_class, ScannerAdapter):
        raise TypeError(f"{adapter_class} must inherit from ScannerAdapter")
    instance = adapter_class()
    _SCANNER_REGISTRY[instance.name] = adapter_class


def get_scanner(name: str) -> Optional[type]:
    return _SCANNER_REGISTRY.get(name)


def list_scanners() -> List[str]:
    return list(_SCANNER_REGISTRY.keys())


def create_scanner(name: str, **kwargs) -> ScannerAdapter:
    adapter_class = _SCANNER_REGISTRY.get(name)
    if not adapter_class:
        raise ValueError(f"Unknown scanner: {name}. Available: {list(_SCANNER_REGISTRY.keys())}")
    return adapter_class(**kwargs)


def list_available_scanners() -> List[Dict[str, Any]]:
    result = []
    for name, adapter_class in _SCANNER_REGISTRY.items():
        adapter = adapter_class()
        result.append({
            "name": name,
            "available": adapter.is_available(),
            "version": adapter.get_version(),
            "modes": adapter.get_supported_modes(),
            "requires_api_key": adapter.requires_api_key,
            "issues": adapter.validate_config(),
        })
    return result
