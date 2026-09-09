# SkillsGoat Usability Review: Making It Trivial to Test with Any Scanner/Model

**Status:** Living document | **Date:** 2026-08-27 | **Reviewer:** Security Researcher

---

## Executive Summary

SkillsGoat is a **high-quality, comprehensive corpus** (70 atomic + 35 compound = 105 fixtures) with excellent ground truth. However, the **developer experience for scanner/model evaluation has significant friction points** that prevent "zero-to-results" in under 5 minutes.

**Bottom line:** The corpus is excellent. The tooling around it needs work to make it a "drop-in" benchmark for any scanner or model.

---

## Current State Assessment

### ✅ What Works Well
| Aspect | Status | Notes |
|--------|--------|-------|
| Corpus quality | ✅ Excellent | 70 atomic + 35 compound = 105 fixtures, rich ground truth |
| Ground truth format | ✅ Excellent | `expected.yaml` with AST10/SkillSpector/V-code mappings |
| Categories/taxonomy | ✅ Excellent | 35 categories, well-organized tiers (000-300) |
| Safety practices | ✅ Excellent | Canaries, inert payloads, SAFETY.md |
| Lint/selftest | ✅ Passing | CI-ready |

### ❌ Critical Usability Gaps

| Gap | Impact | Severity |
|-----|--------|----------|
| **No `requirements.txt` / `pyproject.toml`** | Can't `pip install` the tool | 🔴 Critical |
| **No Dockerfile / container support** | Can't run in CI/CD cleanly | 🔴 Critical |
| **Scanner adapters hardcoded** | Only SkillSpector/Cisco/Snyk; adding new = code change | 🟠 High |
| **No GitHub Actions CI workflow** | No automated regression testing | 🟠 High |
| **Scan output not machine-readable by default** | JSON only via flag; no SARIF/JUnit | 🟠 High |
| **No `make` / `just` / `taskfile`** | Common tasks require memorizing flags | 🟡 Medium |
| **No `requirements.txt` / `pyproject.toml`** | Manual `pip install pyyaml` required | 🟠 High |
| **No `scan --format sarif/junit/jsonl`** | Can't plug into SAST pipelines | 🟠 High |
| **No `scan --output-dir` with per-entry JSON** | Hard to diff results | 🟡 Medium |
| **No `--fail-on` threshold for CI gates** | Can't use as quality gate | 🟡 Medium |
| **No `goat.py doctor` / `goat.py check-env`** | Hard to debug scanner setup issues | 🟡 Medium |
| **No man pages / shell completions** | Discoverability suffers | 🟢 Low |

---

## Proposed Improvements (Prioritized)

### Phase 1: Zero-Friction Onboarding (Week 1)

#### 1.1 Add `pyproject.toml` with modern packaging
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "skillsgoat"
version = "0.2.0"
description = "Vulnerable-by-design AI agent skill corpus for scanner evaluation"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]
optional-dependencies = {
    "dev" = ["pytest", "ruff", "mypy"],
    "scanners" = ["skillspector @ git+https://github.com/NVIDIA/SkillSpector.git", "cisco-ai-skill-scanner"],
    "llm" = ["litellm", "anthropic", "openai"],
    "snyk" = ["snyk-agent-scan"]
}

[project.scripts]
goat = "goat:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

#### 1.2 Add `Dockerfile` for reproducible runs
```dockerfile
# syntax = docker/dockerfile:1.4
FROM python:3.12-slim AS base
WORKDIR /skillsgoat
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e ".[dev,scanners]"
COPY . .
ENTRYPOINT ["goat"]
```

#### 1.3 Add `Makefile` for common tasks
```makefile
.PHONY: install test lint scan-all clean

install:
	pip install -e ".[dev,scanners]"

lint:
	goat lint

test: lint
	goat selftest

scan-skillspector:
	goat scan --scanners skillspector --no-llm --format json --output evaluations/skillspector/latest.json

scan-cisco:
	goat scan --scanners cisco --no-llm --format json --output evaluations/cisco/latest.json

scan-snyk:
	goat scan --scanners snyk --format json --output evaluations/snyk/latest.json

scan-all: scan-skillspector scan-cisco scan-snyk

report:
	goat chain-report
	cat docs/CHAINS.md

clean:
	rm -rf evaluations/*/latest.json evaluations/*/report.md
```

#### 1.3 Add `pyproject.toml` optional dependencies for scanners
```toml
[project.optional-dependencies]
scanners = [
    "skillspector @ git+https://github.com/NVIDIA/SkillSpector.git",
    "cisco-ai-skill-scanner",
    "snyk-agent-scan",
]
llm = ["litellm", "anthropic", "openai"]
snyk = ["snyk-agent-scan"]
dev = ["pytest", "ruff", "mypy", "pre-commit"]
```

---

### Phase 2: Scanner-Agnostic Architecture (Week 2)

#### 2.1 Plugin Architecture for Scanners
```python
# goat/scanners/__init__.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

@dataclass
class ScanResult:
    scanner: str
    entry_id: str
    status: str  # "caught" | "weak" | "missed" | "error" | "timeout"
    score: Optional[float] = None
    severity: Optional[str] = None
    findings: List[dict] = field(default_factory=list)
    raw_output: str = ""
    scan_time_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

class ScannerAdapter(ABC):
    name: str
    supported_modes: List[str] = ["atomic"]  # atomic, node, composite
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is installed/configured"""
        pass
    
    @abstractmethod
    def scan(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        """Scan a single skill directory"""
        pass
    
    @abstractmethod
    def scan_batch(self, skill_dirs: List[Path], mode: str = "atomic") -> List[ScanResult]:
        """Scan multiple skills (optimize for batch)"""
        pass

# Registry
SCANNER_REGISTRY: Dict[str, ScannerAdapter] = {}

def register_scanner(adapter: ScannerAdapter):
    SCANNER_REGISTRY[adapter.name] = adapter
```

#### 2.2 Built-in Adapters (drop-in replacements for current hardcoded logic)
```python
# goat/scanners/skillspector.py
class SkillSpectorAdapter(ScannerAdapter):
    name = "skillspector"
    supported_modes = ["atomic"]
    
    def is_available(self) -> bool:
        return shutil.which("skillspector") is not None
    
    def scan(self, skill_dir: Path, mode: str = "atomic", **kwargs) -> ScanResult:
        cmd = ["skillspector", "scan", str(skill_dir), "--format", "json"]
        if kwargs.get("no_llm", True):
            cmd.append("--no-llm")
        # ... execute, parse JSON, return ScanResult
```

#### 2.3 Configuration via `skillsgoat.yaml`
```yaml
# skillsgoat.yaml (project root)
scanners:
  skillspector:
    enabled: true
    timeout: 120
    args: ["--no-llm"]
  cisco:
    enabled: true
    timeout: 180
    args: ["--no-llm", "--policy", "strict"]
  snyk:
    enabled: false  # requires SNYK_TOKEN
    timeout: 300
  custom:
    enabled: false
    cmd: "./my-scanner"
    args: ["--json"]

output:
  formats: ["json", "sarif", "junit"]
  output_dir: "evaluations"
  per_entry_files: true
```

---

### Phase 3: CI/CD Integration & Reporting (Week 3)

#### 3.1 GitHub Actions Workflow (`.github/workflows/scan.yml`)
```yaml
name: Scanner Evaluation
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2AM

jobs:
  scan:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        scanner: [skillspector, cisco]
        mode: [atomic]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[scanners]"
      - run: goat scan --scanners ${{ matrix.scanner }} --mode ${{ matrix.mode }} --format sarif --output evaluations/${{ matrix.scanner }}/latest.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: evaluations/${{ matrix.scanner }}/latest.sarif
          category: ${{ matrix.scanner }}

  regression-check:
    needs: scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          python -c "
import json, sys
with open('evaluations/skillspector/latest.json') as f:
    data = json.load(f)
blind = sum(1 for r in data['rows'] if r['status'] in ('missed', 'weak'))
if blind > 7:  # threshold
    print(f'REGRESSION: {blind} blind chains')
    sys.exit(1)
"
```

#### 3.2 Rich Reporting Output
```python
# goat/reporting.py
def generate_report(results: List[ScanResult], format: str = "markdown") -> str:
    if format == "markdown":
        return generate_markdown_report(results)
    elif format == "sarif":
        return generate_sarif(results)
    elif format == "junit":
        return generate_junit(results)
    elif format == "html":
        return generate_html_report(results)
```

#### 3.3 CI Gate Command
```bash
# New command
goat scan --scanners skillspector,cisco --fail-on blind>5 --format sarif --output evaluations/
# Exit code: 0 = pass, 1 = regression detected, 2 = error
```

---

## Scanner Compatibility Matrix

| Scanner | Current Support | Needed Work | Priority |
|---------|----------------|-------------|----------|
| **SkillSpector** | ✅ Full (static + LLM) | Adapter refactor | 🟢 Done |
| **Cisco skill-scanner** | ✅ Static | LLM adapter, SARIF | 🟠 High |
| **Snyk Labs** | ⚠️ UI only | CLI wrapper or API | 🟠 High |
| **Invariant/Fable** | ❌ | Proxy adapter | 🟡 Medium |
| **Trail of Bits aid** | ✅ Standalone | Wrapper | 🟡 Medium |
| **Semgrep** | ❌ | Rules + wrapper | 🟡 Medium |
| **Custom scanners** | ❌ | Plugin interface | 🟡 Medium |

---

## Quick Wins (Do This Week)

| Task | Effort | Impact |
|------|--------|--------|
| Add `pyproject.toml` + `pip install -e .` | 30 min | 🔴 Critical |
| Add `Dockerfile` + `docker-compose.yml` | 30 min | 🔴 Critical |
| Add `Makefile` with `make scan-all` | 20 min | 🔴 Critical |
| Add `--format sarif|junit|jsonl` to scan | 2 hrs | 🟠 High |
| Add GitHub Actions workflow | 1 hr | 🟠 High |
| Extract scanner adapters (SkillSpector, Cisco) | 3 hrs | 🟠 High |
| Add `--output-dir` + per-entry JSON | 1 hr | 🟠 High |
| Add `--fail-on` for CI gates | 30 min | 🟠 High |

---

## "Golden Path" User Experience (Target)

```bash
# 1. Clone & run in 30 seconds
git clone https://github.com/optimuslabs-io/skillsgoat
cd skillsgoat
make install  # or: docker compose up -d

# 2. Run all scanners, get SARIF + HTML report
make scan-all

# 3. CI gate passes/fails based on blindness threshold
make ci-gate  # exits 0 if blindness < threshold, else 1

# 4. View HTML report
open evaluations/report.html
```

---

## Appendix: Current Pain Points (Real Examples)

### Pain Point 1: "How do I run this?"
```bash
# Current (broken):
git clone ...
cd skillsgoat
pip install pyyaml  # Manual!
python3 goat.py scan --scanners skillspector --no-llm
# Error: skillspector not in PATH
# Need to: pip install skillspector @ git+https://...

# Desired:
make install && make scan-skillspector
```

### Pain Point 2: "How do I add a new scanner?"
```python
# Current: Edit goat.py, add to SCANNER_CONFIGS, modify run_scanner(), modify scanner_verdict()
# Desired:
# 1. Create goat/scanners/my_scanner.py implementing ScannerAdapter
# 2. Register in goat/scanners/__init__.py: register_scanner(MyScanner())
# 3. Add to skillsgoat.yaml config
# 4. Run: goat scan --scanners myscanner
```

### Pain Point 3: "How do I use this in CI?"
```yaml
# Current: Manual script writing
# Desired:
# .github/workflows/scan.yml exists, just works
# goat scan --scanners skillspector,cisco --fail-on blind>5 --format sarif
# Exit code 0 = pass, 1 = regression, 2 = error
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-27 | Adopt `pyproject.toml` + `src/` layout | Modern Python packaging; enables `pip install -e .` |
| 2026-08-27 | Scanner adapter pattern | Decouple corpus from scanners; enable plugin ecosystem |
| 2026-08-27 | SARIF + JUnit + HTML output | Standard formats for CI/CD integration |
| 2026-08-27 | `make scan-all` as golden path | Matches developer expectations |
| 2026-08-27 | `--fail-on` for CI gates | Enables PR blocking on regression |

---

## Next Steps

1. [ ] Create `pyproject.toml` + `Dockerfile` + `Makefile`
2. [ ] Refactor `goat.py` → `src/goat/` package with scanner adapters
3. [ ] Add GitHub Actions workflow
3. [ ] Add SARIF/JUnit/HTML output formats
4. [ ] Write integration test for SkillSpector adapter
5. [ ] Add `goat doctor` command for environment diagnostics
5. [ ] Document scanner adapter SDK for vendors

---

*Review complete. Ready to implement Phase 1.*
