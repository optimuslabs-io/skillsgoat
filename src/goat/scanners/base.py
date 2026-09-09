"""Base classes for scanner adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import time


@dataclass
class ScanResult:
    """Result of scanning a single skill entry."""
    scanner: str
    entry_id: str
    status: str  # "caught" | "weak" | "missed" | "error" | "timeout" | "scan_failed" | "stale"
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
    graph_verdict: str  # "critical" | "high" | "medium" | "low"
    nodes: List[ScanResult]  # Per-node results
    graph_result: Optional[ScanResult] = None  # Composite scan result
    scan_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScannerAdapter(ABC):
    """Abstract base class for scanner adapters."""
    
    name: str = "base"
    supported_modes: List[str] = ["atomic"]  # atomic, node, composite, both
    requires_api_key: bool = False
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is installed and configured."""
        pass
    
    @abstractmethod
    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        """Scan a single skill directory."""
        pass
    
    @abstractmethod
    def scan_chain(self, chain_dir: Path, mode: str = "composite", **kwargs) -> "ChainScanResult":
        """Scan a compound chain (node + composite modes)."""
        pass
    
    def get_version(self) -> str:
        """Return scanner version string."""
        return "unknown"
    
    def get_supported_modes(self) -> List[str]:
        return self.supported_modes
    
    def validate_config(self) -> List[str]:
        """Return list of configuration issues, empty if OK."""
        issues = []
        if not self.is_available():
            issues.append(f"{self.name}: not installed or not in PATH")
        if self.requires_api_key:
            # Subclasses should check their specific env vars
            pass
        return issues


# Scanner registry
_SCANNER_REGISTRY: Dict[str, type] = {}


def register_scanner(adapter_class: type) -> None:
    """Register a scanner adapter class."""
    if not issubclass(adapter_class, ScannerAdapter):
        raise TypeError(f"{adapter_class} must inherit from ScannerAdapter")
    instance = adapter_class()
    _SCANNER_REGISTRY[instance.name] = adapter_class


def get_scanner(name: str) -> Optional[type]:
    """Get scanner adapter class by name."""
    return _SCANNER_REGISTRY.get(name)


def list_scanners() -> List[str]:
    """List all registered scanner names."""
    return list(_SCANNER_REGISTRY.keys())


def create_scanner(name: str, **kwargs) -> "ScannerAdapter":
    """Create scanner instance by name."""
    adapter_class = _SCANNER_REGISTRY.get(name)
    if not adapter_class:
        raise ValueError(f"Unknown scanner: {name}. Available: {list(_SCANNER_REGISTRY.keys())}")
    return adapter_class(**kwargs)


def list_scanners() -> List[str]:
    """List all registered scanner names."""
    return list(_SCANNER_REGISTRY.keys())


def list_available_scanners() -> List[Dict[str, Any]]:
    """List all registered scanners with their availability and config status."""
    result = []
    for name, adapter_class in _SCANNER_REGISTRY.items():
        adapter = adapter_class()
        available = adapter.is_available()
        issues = adapter.validate_config()
        result.append({
            "name": name,
            "available": available,
            "version": adapter.get_version(),
            "modes": adapter.get_supported_modes(),
            "requires_api_key": adapter.requires_api_key,
            "issues": issues,
        })
    return result


# Internal registry
_SCANNER_REGISTRY: Dict[str, type] = {}

# Import scanner implementations to register them. A broken adapter must not
# prevent the rest of the goat package from loading.
import importlib

for _mod in ("skillspector", "cisco", "snyk", "nova"):
    try:
        importlib.import_module(f".{_mod}", __package__)
    except Exception as _exc:  # pragma: no cover
        import sys as _sys
        print(f"warning: scanner {_mod!r} failed to load: {_exc}", file=_sys.stderr)

# Re-export public API
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

__all__ = [
    "ScanResult",
    "ChainScanResult",
    "ScannerAdapter",
    "register_scanner",
    "get_scanner",
    "list_scanners",
    "create_scanner",
    "list_available_scanners",
    "list_scanners",
]
