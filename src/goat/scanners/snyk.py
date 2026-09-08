"""Snyk Agent Scan adapter (snyk-agent-scan CLI)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from .base import ChainScanResult, ScanResult, ScannerAdapter, register_scanner

# Agent Scan scores each risk 0–1000. Treat the top two printer bands as block.
_BLOCK_SCORE = 600


def _snyk_exe() -> str:
    candidate = Path(sys.executable).parent / "snyk-agent-scan"
    if candidate.exists():
        return str(candidate)
    return shutil.which("snyk-agent-scan") or "snyk-agent-scan"


def _iter_risks(report: dict) -> list[dict]:
    findings: list[dict] = []
    for path in report.get("scan_path_responses") or []:
        for skill in path.get("skill_risks") or []:
            indexes = skill.get("risk_indexes") or {}
            for name, risk in indexes.items():
                if not isinstance(risk, dict):
                    continue
                findings.append({
                    "id": name,
                    "score": int(risk.get("score") or 0),
                    "evidence": risk.get("evidence") or "",
                    "skill": skill.get("name") or "",
                })
    return findings


def _analysis_errors(report: dict) -> list[str]:
    msgs: list[str] = []
    for path in report.get("scan_path_responses") or []:
        err = path.get("error") or {}
        if err.get("message"):
            msgs.append(str(err["message"]))
        for skill in path.get("skill_risks") or []:
            serr = skill.get("error") or {}
            if serr.get("message"):
                msgs.append(str(serr["message"]))
    return msgs


class SnykAgentScanAdapter(ScannerAdapter):
    """Adapter for Snyk Agent Scan (`snyk-agent-scan`)."""

    name = "snyk"
    supported_modes = ["atomic"]
    requires_api_key = True

    def __init__(self, timeout: int = 180, **kwargs):
        self.timeout = timeout
        self._scanner_path = _snyk_exe()

    def is_available(self) -> bool:
        return Path(self._scanner_path).exists() or shutil.which("snyk-agent-scan") is not None

    def get_version(self) -> str:
        try:
            import importlib.metadata as metadata
            return metadata.version("snyk-agent-scan")
        except Exception:
            return "unknown"

    def validate_config(self) -> List[str]:
        issues = []
        if not self.is_available():
            issues.append(
                "snyk-agent-scan not found. Install with: pip install snyk-agent-scan"
            )
        if not os.environ.get("SNYK_TOKEN"):
            issues.append(
                "SNYK_TOKEN is not set. Create an API token at https://app.snyk.io/account"
            )
        return issues

    def get_supported_modes(self) -> List[str]:
        return ["atomic"]

    def scan_skill(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        start = time.time()
        if not os.environ.get("SNYK_TOKEN"):
            return ScanResult(
                scanner=self.name,
                entry_id=skill_dir.name,
                status="error",
                raw_output="SNYK_TOKEN is not set",
                scan_time_seconds=time.time() - start,
            )

        cmd = [self._scanner_path, "scan", str(skill_dir), "--json"]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired:
            return ScanResult(
                scanner=self.name,
                entry_id=skill_dir.name,
                status="timeout",
                scan_time_seconds=time.time() - start,
                metadata={"error": "timeout"},
            )
        except Exception as exc:
            return ScanResult(
                scanner=self.name,
                entry_id=skill_dir.name,
                status="error",
                raw_output=str(exc),
                scan_time_seconds=time.time() - start,
            )

        raw = proc.stdout.strip() or proc.stderr.strip()
        i = raw.find("{")
        if i == -1:
            return ScanResult(
                scanner=self.name,
                entry_id=skill_dir.name,
                status="error",
                raw_output=raw[:1000],
                scan_time_seconds=time.time() - start,
            )
        try:
            data = json.loads(raw[i:])
        except json.JSONDecodeError:
            return ScanResult(
                scanner=self.name,
                entry_id=skill_dir.name,
                status="error",
                raw_output=raw[:1000],
                scan_time_seconds=time.time() - start,
            )

        findings = _iter_risks(data)
        errors = _analysis_errors(data)
        max_score = max((f["score"] for f in findings), default=0)
        if errors and not findings:
            status = "error"
            severity = "none"
        elif max_score >= _BLOCK_SCORE:
            status = "caught"
            severity = "critical" if max_score >= 900 else "high"
        elif findings:
            status = "weak"
            severity = "medium" if max_score >= 300 else "low"
        else:
            status = "missed"
            severity = "none"

        return ScanResult(
            scanner=self.name,
            entry_id=skill_dir.name,
            status=status,
            score=float(max_score),
            severity=severity,
            findings=findings,
            raw_output=raw[:2000],
            scan_time_seconds=time.time() - start,
            metadata={"mode": mode, "errors": errors},
        )

    def scan_chain(self, chain_dir: Path, mode: str = "composite", **kwargs) -> ChainScanResult:
        return ChainScanResult(
            scanner=self.name,
            chain_id=chain_dir.name,
            chain_name=chain_dir.name,
            graph_verdict="unknown",
            nodes=[],
            scan_time_seconds=0,
            metadata={"error": "Chain scanning is not supported for Snyk Agent Scan"},
        )


register_scanner(SnykAgentScanAdapter)
