"""SkillSpector scanner adapter."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base import ScanResult, ChainScanResult, ScannerAdapter, register_scanner


def _get_skillspector_path() -> str:
    """Get the path to skillspector executable."""
    python_bin = Path(sys.executable).parent
    candidate = Path(sys.executable).parent / "skillspector"
    if candidate.exists():
        return str(candidate)
    return "skillspector"


class SkillSpectorAdapter(ScannerAdapter):
    """Adapter for NVIDIA SkillSpector scanner."""
    
    name = "skillspector"
    supported_modes = ["atomic", "node", "composite", "both"]
    requires_api_key = False
    
    def __init__(self, timeout: int = 120, no_llm: bool = True, model: str = None, provider: str = None, **kwargs):
        self.timeout = timeout
        self.no_llm = no_llm
        self.model = model
        self.provider = provider
        self._skillspector_path = _get_skillspector_path()
    
    def _get_skillspector_path(self) -> str:
        python_bin = Path(sys.executable).parent
        candidate = Path(sys.executable).parent / "skillspector"
        if candidate.exists():
            return str(candidate)
        return "skillspector"
    
    @property
    def name(self) -> str:
        return "skillspector"
    
    @property
    def supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    @property
    def requires_api_key(self) -> bool:
        if self.provider and self.provider not in ("claude_cli", "codex_cli", "gemini_cli", "ollama"):
            return True
        return False
    
    def is_available(self) -> bool:
        return Path(self._skillspector_path).exists() or shutil.which("skillspector") is not None
    
    def get_version(self) -> str:
        try:
            result = subprocess.run(
                [self._skillspector_path, "--version"],
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
            issues.append("skillspector not found. Install with: pip install -e '.[scanners]' (pinned SHA in pyproject.toml)")
        if self.requires_api_key:
            provider = self.provider or "nv_inference"
            if provider in ("openai", "openai_compatible") and not os.environ.get("OPENAI_API_KEY"):
                issues.append("OPENAI_API_KEY required for openai/openai_compatible provider")
            elif provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
                issues.append("ANTHROPIC_API_KEY required for anthropic provider")
            elif provider == "anthropic_proxy":
                if not os.environ.get("ANTHROPIC_PROXY_API_KEY") or not os.environ.get("ANTHROPIC_PROXY_ENDPOINT_URL"):
                    issues.append("ANTHROPIC_PROXY_API_KEY and ANTHROPIC_PROXY_ENDPOINT_URL required for anthropic_proxy")
            elif provider == "bedrock" and not os.environ.get("AWS_PROFILE") and not os.environ.get("AWS_ACCESS_KEY_ID"):
                issues.append("AWS credentials required for bedrock provider")
            elif provider == "azure_openai" and not os.environ.get("AZURE_OPENAI_API_KEY"):
                issues.append("AZURE_OPENAI_API_KEY required for azure_openai provider")
            elif provider == "openai_compatible" and not os.environ.get("OPENAI_API_KEY"):
                issues.append("OPENAI_API_KEY required for openai_compatible provider (set OPENAI_BASE_URL for custom endpoints)")
        return issues
    
    def get_supported_modes(self) -> List[str]:
        return ["atomic", "node", "composite", "both"]
    
    def _run_scan(self, target: Path, mode: str = "atomic", no_llm: bool = True) -> tuple[str, str]:
        cmd = [self._skillspector_path, "scan", str(target), "--format", "json"]
        if self.no_llm or no_llm:
            cmd.append("--no-llm")
        if self.provider:
            cmd.extend(["--provider", self.provider])
        if self.model:
            cmd.extend(["--model", self.model])

        try:
            result = subprocess.run(
                cmd,
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
        
        ra = data.get("risk_assessment", {})
        issues = data.get("issues", [])
        score = ra.get("score", 0)
        severity = ra.get("severity", "").upper()
        recommendation = ra.get("recommendation", "")
        
        if recommendation.upper().startswith("DO_NOT_INSTALL"):
            status = "caught"
        elif severity in ("HIGH", "CRITICAL"):
            status = "weak"
        else:
            status = "missed"
        
        findings = []
        for issue in issues:
            findings.append({
                "id": issue.get("id", ""),
                "category": issue.get("category", ""),
                "severity": issue.get("severity", ""),
                "title": issue.get("title", ""),
                "location": issue.get("location", {}),
            })
        
        score_val = float(score) if isinstance(score, (int, float)) else 0.0
        
        return ScanResult(
            scanner=self.name,
            entry_id="unknown",
            status=status,
            score=score_val,
            severity=severity,
            findings=findings,
            raw_output=stdout[:2000],
            metadata={
                "recommendation": recommendation,
                "component_count": len(data.get("components", [])),
            }
        )
    
    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        start = time.time()
        status, stdout = self._run_scan(Path(skill_dir), mode)
        scan_time = time.time() - start
        
        result = self._parse_result(stdout)
        result.scanner = self.name
        result.scan_time_seconds = scan_time
        result.metadata["mode"] = mode
        return result
    
    def scan_chain(self, chain_dir: Path, mode: str = "composite", **kwargs):
        from .base import ChainScanResult
        import yaml
        
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
register_scanner(SkillSpectorAdapter)
