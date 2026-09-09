"""Nova Hunting skill scanner adapter."""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ScanResult, ChainScanResult, ScannerAdapter, register_scanner


def _get_nova_path() -> str:
    """Get the path to novarun executable."""
    python_bin = Path(sys.executable).parent
    candidate = Path(sys.executable).parent / "novarun"
    if candidate.exists():
        return str(candidate)
    return "novarun"


class NovaAdapter(ScannerAdapter):
    """Adapter for Nova Hunting skill scanner (novarun)."""
    
    name = "nova"
    supported_modes = ["atomic", "node", "composite", "both"]
    requires_api_key = False  # Depends on rules used
    
    def __init__(self, timeout: int = 180, no_llm: bool = True, rules_path: str = None, **kwargs):
        self.timeout = timeout
        self.no_llm = no_llm
        self.rules_path = rules_path
        self._nova_path = self._get_nova_path()
    
    def _get_nova_path(self) -> str:
        python_bin = Path(sys.executable).parent
        candidate = Path(sys.executable).parent / "novarun"
        if candidate.exists():
            return str(candidate)
        return "novarun"
    
    @property
    def name(self) -> str:
        return "nova"
    
    @property
    def supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    @property
    def requires_api_key(self) -> bool:
        return False  # Depends on rules used
    
    def is_available(self) -> bool:
        return Path(self._nova_path).exists() or shutil.which("novarun") is not None
    
    def get_version(self) -> str:
        try:
            result = subprocess.run(
                [self._nova_path, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[-1]
        except Exception:
            pass
        return "unknown"
    
    def validate_config(self) -> List[str]:
        issues = []
        if not self.is_available():
            issues.append("novarun not found in PATH. Install with: pip install nova-hunting")
        return issues
    
    def get_supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    def _run_scan(self, target: Path, rules_path: str = None) -> tuple[str, str]:
        cmd = [self._nova_path, "scan", str(target), "--format", "json"]
        if self.rules_path:
            cmd.extend(["--rule", self.rules_path])
        if rules_path:
            cmd.extend(["--rule", rules_path])
        
        try:
            result = subprocess.run(
                [self._nova_path, "scan", str(target), "--format", "json"] + (["--rule", self.rules_path] if self.rules_path else []) + (["--rule", rules_path] if rules_path else []),
                capture_output=True, text=True, timeout=self.timeout
            )
            return "success", result.stdout
        except subprocess.TimeoutExpired:
            return "timeout", ""
        except Exception as e:
            return "error", str(e)
    
    def _parse_result(self, stdout: str) -> ScanResult:
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return ScanResult(
                scanner=self.name,
                entry_id="unknown",
                status="error",
                raw_output=stdout[:1000]
            )
        
        # Nova output format - adapt based on actual output structure
        findings_list = data.get("findings", data.get("matches", []))
        max_severity = "NONE"
        for finding in findings_list:
            sev = finding.get("severity", "").upper()
            if sev == "CRITICAL":
                max_severity = "CRITICAL"
            elif sev == "HIGH" and max_severity != "CRITICAL":
                max_severity = "HIGH"
            elif sev == "MEDIUM" and max_severity not in ("CRITICAL", "HIGH"):
                max_severity = "MEDIUM"
            elif sev == "LOW" and max_severity == "NONE":
                max_severity = "LOW"
        
        if max_severity in ("CRITICAL", "HIGH"):
            status = "caught"
        elif max_severity in ("MEDIUM", "LOW"):
            status = "weak"
        else:
            status = "missed"
        
        findings = []
        for finding in findings_list:
            findings.append({
                "id": finding.get("rule_id", finding.get("id", "")),
                "category": finding.get("category", finding.get("type", "")),
                "severity": finding.get("severity", ""),
                "title": finding.get("description", finding.get("message", "")),
                "file_path": finding.get("file", finding.get("location", "")),
                "line_number": finding.get("line", finding.get("line_number", 0)),
            }),
        
        if max_severity in ("CRITICAL", "HIGH"):
            status = "caught"
        elif max_severity in ("MEDIUM", "LOW"):
            status = "weak"
        else:
            status = "missed"
        
        return ScanResult(
            scanner=self.name,
            entry_id="unknown",
            status=status,
            severity=max_severity.lower() if max_severity != "NONE" else "none",
            findings=findings,
            raw_output="",
            metadata={
                "findings_count": len(findings),
                "max_severity": max_severity,
            }
        )
    
    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        start = time.time()
        status, stdout = self._run_scan(skill_dir)
        scan_time = time.time() - start
        
        result = self._parse_result(stdout)
        result.scanner = self.name
        result.scan_time_seconds = scan_time
        result.metadata["mode"] = mode
        return result
    
    def scan_chain(self, chain_dir: Path, mode: str = "composite", **kwargs):
        from .base import ChainScanResult
        
        chain_yaml = Path(chain_dir) / "chain.yaml"
        if not chain_yaml.exists():
            return ChainScanResult(
                scanner=self.name,
                chain_id=chain_dir.name,
                chain_name=chain_dir.name,
                graph_verdict="unknown",
                nodes=[],
                scan_time_seconds=0,
                metadata={"error": "chain.yaml not found"}
            )
        
        import yaml
        chain_data = yaml.safe_load(chain_yaml.read_text())
        chain_id = chain_data.get("id", chain_dir.name)
        chain_name = chain_data.get("name", chain_dir.name)
        graph_verdict = chain_data.get("graph_verdict", "unknown")
        nodes_data = chain_data.get("nodes", {})
        
        nodes_results = []
        for node_name, node_info in nodes_data.items():
            node_dir = Path(chain_dir) / "nodes" / node_name / "skill"
            if node_dir.exists():
                node_result = self.scan_skill(node_dir, mode="atomic")
                node_result.entry_id = node_name
                nodes_results.append(node_result)
        
        composite_result = self.scan_skill(Path(chain_dir), mode="composite")
        composite_result.entry_id = f"{chain_dir.name}__composite"
        
        return ChainScanResult(
            scanner=self.name,
            chain_id=chain_id,
            chain_name=chain_data.get("name", chain_dir.name),
            graph_verdict=graph_verdict,
            nodes=nodes_results,
            graph_result=composite_result,
            metadata={"mode": mode}
        )


# Register
from .base import register_scanner
register_scanner(NovaAdapter)
