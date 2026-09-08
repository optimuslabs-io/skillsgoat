"""Cisco skill-scanner adapter."""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base import ScanResult, ChainScanResult, ScannerAdapter, register_scanner


def _get_cisco_scanner_path() -> str:
    python_bin = Path(sys.executable).parent
    candidate = Path(sys.executable).parent / "skill-scanner"
    if candidate.exists():
        return str(candidate)
    return "skill-scanner"


class CiscoScannerAdapter(ScannerAdapter):
    name = "cisco"
    supported_modes = ["atomic", "node", "composite", "both"]
    requires_api_key = False
    
    def __init__(self, timeout: int = 180, no_llm: bool = True, policy: str = "strict", **kwargs):
        self.timeout = timeout
        self.no_llm = no_llm
        self.policy = policy
        self._scanner_path = self._get_cisco_scanner_path()
    
    def _get_cisco_scanner_path(self) -> str:
        python_bin = Path(sys.executable).parent
        candidate = Path(sys.executable).parent / "skill-scanner"
        if candidate.exists():
            return str(candidate)
        return "skill-scanner"
    
    @property
    def name(self) -> str:
        return "cisco"
    
    @property
    def supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    def is_available(self) -> bool:
        return Path(self._scanner_path).exists() or shutil.which("skill-scanner") is not None
    
    def get_version(self) -> str:
        try:
            result = subprocess.run(
                [self._scanner_path, "--version"],
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
            issues.append("skill-scanner not found in PATH. Install with: pip install cisco-ai-skill-scanner")
        return issues
    
    def get_supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    def _run_scan(self, target: Path, use_llm: bool = False) -> tuple[str, str]:
        cmd = [
            self._scanner_path, "scan", str(target),
            "--format", "json",
            "--policy", self.policy
        ]
        if not self.no_llm:
            pass
        
        try:
            result = subprocess.run(
                [self._scanner_path, "scan", str(target), "--format", "json", "--policy", self.policy],
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
        
        max_severity = data.get("max_severity", "NONE").upper()
        findings_count = data.get("findings_count", 0)
        findings = data.get("findings", [])
        is_safe = data.get("is_safe", True)
        
        if max_severity in ("HIGH", "CRITICAL"):
            status = "caught"
        elif findings_count > 0:
            status = "weak"
        else:
            status = "missed"
        
        findings = []
        for finding in findings:
            findings.append({
                "id": finding.get("id", ""),
                "category": finding.get("category", ""),
                "severity": finding.get("severity", ""),
                "title": finding.get("title", ""),
                "file_path": finding.get("file_path", ""),
                "line_number": finding.get("line_number", 0),
            })
        
        return ScanResult(
            scanner=self.name,
            entry_id="unknown",
            status=status,
            severity=max_severity.lower() if max_severity != "NONE" else "none",
            findings=findings,
            raw_output="",
            metadata={
                "findings_count": findings_count,
                "max_severity": max_severity,
                "is_safe": data.get("is_safe", True),
            }
        )
    
    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        start = time.time()
        status, stdout = self._run_scan(Path(skill_dir))
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
        for node_name, node_info in chain_data.get("nodes", {}).items():
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
            metadata={"mode": "composite"}
        )


from .base import register_scanner
register_scanner(CiscoScannerAdapter)
