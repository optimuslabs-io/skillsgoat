# SkillsGoat Usability Review: Making It Trivial to Test with Any Scanner/Model

**Status:** Living document | **Date:** 2026-08-27 | **Reviewer:** Security Researcher

---

## Executive Summary

SkillsGoat is a **high-quality, comprehensive corpus** (76 atomic + 35 compound = 111 fixtures) with excellent ground truth. However, the **developer experience for scanner/model evaluation has significant friction points** that prevent "zero-to-results" in under 5 minutes.

**Bottom line:** The corpus is excellent. The tooling around it needs work to make it a "drop-in" benchmark for any scanner or model.

---

## Current State Assessment

### ✅ What Works Well
| Aspect | Status | Notes |
|--------|--------|-------|
| Corpus quality | ✅ Excellent | 76 atomic + 35 compound = 111 fixtures, rich ground truth |
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
| **Snyk Labs** | ✅ CLI (`snyk-agent-scan`, 12-entry subset) | Full corpus + Labs UI protocol already documented | 🟡 Medium |
| **Nova Hunting** | ⚠️ Adapter present, eval is all JSON parse errors | Finish parser, re-run matrix | 🟠 High |
| **Socket / Gen / Metano / Manifold / Air** | ⚠️ UI protocol + drivers; Metano snapshot only; Socket/Gen `unsupported` | Three-surface plugin matrix (`evaluations/ui/PROTOCOL.md`) | 🟠 High |
| **Invariant/Fable** | ❌ | Proxy adapter | 🟡 Medium |
| **Trail of Bits aid** | ✅ Standalone | Wrapper | 🟡 Medium |
| **Semgrep** | ❌ | Rules + wrapper | 🟡 Medium |
| **Custom scanners** | ❌ | Plugin interface | 🟡 Medium |

---

## Quick Wins (Do This Week)

| Task | Effort | Impact | Status |
|------|--------|--------|--------|
| Add `pyproject.toml` + `pip install -e .` | 30 min | 🔴 Critical | ✅ Files exist; `goat.py` vs `src/goat` still diverged |
| Add `Dockerfile` + `docker-compose.yml` | 30 min | 🔴 Critical | ⚠️ Dockerfile installs extras before `COPY .` |
| Add `Makefile` with `make scan-all` | 20 min | 🔴 Critical | ⚠️ Duplicate `report` / `report-chains` targets; first loop is invalid |
| Add `--format sarif|junit|jsonl` to scan | 2 hrs | 🟠 High | ❌ |
| Add GitHub Actions workflow | 1 hr | 🟠 High | ❌ |
| Extract scanner adapters (SkillSpector, Cisco) | 3 hrs | 🟠 High | ⚠️ `src/goat/scanners/` exists but scan path still uses `SCANNER_CONFIGS` |
| Add `--output-dir` + per-entry JSON | 1 hr | 🟠 High | ❌ |
| Add `--fail-on` for CI gates | 30 min | 🟠 High | ❌ (`make ci-gate` sketched, unproven) |

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
| 2026-09-08 | Land packaging/install/plugin-distribution on PR #1; treat remaining items below as the follow-up plan | Corpus + install path shipped half-wired; do not start Phase 2/3 until P0 is closed |

---

## Follow-up from packaging PR (2026-09-08)

Items found unfinished on `feat/install-packaging-plugin-distribution` ([PR #1](https://github.com/optimuslabs-io/skillsgoat/pull/1)). Do these before new corpus work.

### P0 — correctness (broken or lying)

1. [ ] **One CLI.** Delete `goat_cli.py` and `src/goat/main_old.py`. Make `goat.py` and `src/goat/main.py` the same program (`setup` lives only on root `goat.py` today; `pip install` `goat` has Nova configs but no `setup`).
2. [x] **Restore bytecode payload.** `300-bytecode-poisoning` deleted `utils.cpython-314.pyc`. Regenerate with `python3 tools/gen_binaries.py` so the ToB primitive still has divergent `.pyc`.
3. [x] **Regenerate `docs/CHAINS.md`.** Disk has 35 chains including `c35-encrypted-prompt-injection`; catalog still says 34 and omits C35. Run `python3 goat.py chain-report`.
4. [ ] **Fix `Makefile`.** `report` and `report-chains` are defined twice; the first `report-scanners` loop is syntactically invalid.
5. [ ] **Fix Dockerfile.** `pip install -e ".[dev,scanners]"` runs before `COPY .`, so the editable package is missing at install time.

### P1 — finish what this PR started

6. [ ] **Wire or delete `src/goat/scanners/`.** Adapter package is unused; `cmd_scan` still uses hardcoded `SCANNER_CONFIGS`. Either call `create_scanner()` from the scan path or drop the unused module.
7. [ ] **Nova eval that is not all errors.** Adapter JSON parse does not match `novarun` output (`evaluations/nova/report.md`). Fix parser, re-run matrix.
8. [ ] **Score new fixtures.** Plugin-distribution (`200-clawhub-listing`, `200-vibe-coded-plugin`, `200-vercel-skills-sh-pack`, `200-ide-native-impersonation`) and C35 are absent from Cisco/SkillSpector/Snyk matrices.
9. [ ] **`tests/` directory** referenced by `pyproject.toml` does not exist. Add lint/selftest (and one adapter) tests or remove the pytest config.
10. [x] **Stale counts.** After P0 catalog regen, confirm README “74 fixtures + 35 chains” and `USABILITY_REVIEW` fixture counts.

### P2 — eval coverage and CI

11. [ ] **UI three-surface matrix** for Metano / Gen / Socket / Manifold / Air per `evaluations/ui/PROTOCOL.md` (skill-md / directory / plugin). Today: Metano form snapshot only; Socket/Gen scored `unsupported`; Manifold/Air not probed. Do not upload pasture fixtures to public report feeds.
12. [ ] **Snyk CLI beyond the 12-entry subset** once P1 matrices exist.
13. [ ] GitHub Actions: `goat lint` + `goat selftest` on PR (scanners optional).
14. [ ] `--format sarif|junit`, `--fail-on`, `goat doctor`.
15. [ ] Document scanner adapter SDK only after adapters are actually on the scan path.

### P3 — deferred (README roadmap; not this follow-up)

16. [ ] Version-drift suite (benign→poisoned pairs).
17. [ ] Judge-benchmark leaderboard.
18. [ ] Live-agent detonation / gym layer.
19. [ ] Publish install routes after PR merge (`claude plugins marketplace add`, `npx skills add`) and verify they resolve.

### Left uncommitted on purpose

- `src/goat/main_old.py` — delete in P0, do not merge as a third CLI.

---

## Next Steps

Phase 1 files landed on PR #1; they are not done. Execute **P0 → P1 → P2** above. P3 stays roadmap.

1. [x] Create `pyproject.toml` + `Dockerfile` + `Makefile` (repair in P0)
2. [ ] Refactor `goat.py` → `src/goat/` package with scanner adapters **wired into `scan`**
3. [ ] Add GitHub Actions workflow
4. [ ] Add SARIF/JUnit/HTML output formats
5. [ ] Write integration test for SkillSpector adapter (`tests/` missing)
6. [ ] Add `goat doctor` command for environment diagnostics
7. [ ] Document scanner adapter SDK for vendors

---

*Updated 2026-09-08 with unfinished work from the packaging/install PR.*
