# SkillsGoat Makefile
# Common tasks for development, testing, and evaluation

.PHONY: help install setup setup-index uninstall-skills test lint scan-all scan-skillspector scan-cisco scan-snyk report clean doctor

# Default target
help:
	@echo "SkillsGoat - Vulnerable-by-design AI agent skill corpus"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install Python deps in development mode"
	@echo "  setup            Link pasture fixtures into agent skill dirs (goat install)"
	@echo "  doctor           Check environment and scanner availability"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run lint + selftest"
	@echo "  lint             Validate corpus consistency"
	@echo "  selftest         Run harness sanity checks"
	@echo ""
	@echo "Scanning:"
	@echo "  scan-all         Run all scanners (atomic mode)"
	@echo "  scan-skillspector  Run SkillSpector scanner"
	@echo "  scan-cisco         Run Cisco skill-scanner"
	@echo "  scan-snyk          Run Snyk Labs scanner (requires SNYK_TOKEN)"
	@echo "  scan-chains        Run compound chain evaluation"
	@echo "  scan-all-modes     Run all modes (atomic, node, composite)"
	@echo ""
	@echo "Reporting:"
	@echo "  report           Generate all reports (CHAINS.md, scanner reports)"
	@echo "  report-chains    Generate CHAINS.md catalog"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean            Remove generated evaluation artifacts"
	@echo "  clean-all        Remove all generated files + virtual env"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci-gate          Run scans and fail if blindness threshold exceeded"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install --upgrade pip
	pip install -e ".[dev,scanners]"

setup:
	./setup

setup-index:
	./setup --index-only

uninstall-skills:
	./setup --uninstall

# Check environment and scanner availability
doctor:
	@echo "=== SkillsGoat Environment Check ==="
	@python3 --version
	@which python3
	@echo ""
	@echo "Python packages:"
	@pip list | grep -E "(pyyaml|skillspector|cisco|snyk|litellm)"
	@echo ""
	@echo "CLI tools:"
	@which skillspector || echo "skillspector: NOT FOUND"
	@which skill-scanner || echo "skill-scanner: NOT FOUND"
	@which snyk-agent-scan || echo "snyk-agent-scan: NOT FOUND"
	@echo ""
	@echo "Claude CLI:"
	@which claude && claude --version || echo "claude: NOT FOUND"
	@echo ""
	@echo "Git status:"
	@git status --short
	@echo ""
	@echo "GitHub auth:"
	@gh auth status 2>/dev/null || echo "gh: not authenticated"

# =============================================================================
# Testing & Validation
# =============================================================================

lint:
	.venv/bin/python goat.py lint

selftest:
	.venv/bin/python goat.py selftest

test: lint selftest
	@echo "All tests passed!"

# =============================================================================
# Scanning
# =============================================================================

# Run all scanners in atomic mode (default)
scan-all:
	@echo "=== Running all scanners (atomic mode) ==="
	@$(MAKE) scan-skillspector
	@$(MAKE) scan-cisco
	@$(MAKE) scan-snyk

scan-skillspector:
	@echo "=== Running SkillSpector (static) ==="
	.venv/bin/python goat.py scan --scanners skillspector --no-llm --format json --output evaluations/skillspector/latest.json

scan-cisco:
	@echo "=== Running Cisco skill-scanner ==="
	.venv/bin/python goat.py scan --scanners cisco --no-llm --format json --output evaluations/cisco/latest.json

scan-snyk:
	@if [ -z "$$SNYK_TOKEN" ]; then \
		echo "SKIP: SNYK_TOKEN not set. Set SNYK_TOKEN to run Snyk Labs scan."; \
		exit 0; \
	fi
	@echo "=== Running Snyk Labs ==="
	.venv/bin/python goat.py scan --scanners snyk --format json --output evaluations/snyk/latest.json

# Chain evaluation modes
scan-chains:
	@echo "=== Running chain evaluation (node + composite modes) ==="
	.venv/bin/python goat.py scan --scanners skillspector --mode both --format json --output evaluations/skillspector/chains.json

scan-all-modes:
	@$(MAKE) scan-skillspector
	@$(MAKE) scan-chains

# Full evaluation pipeline
scan-full: scan-all scan-chains
	@echo "=== Full evaluation complete ==="

# =============================================================================
# Reporting
# =============================================================================

report: report-chains report-scanners

report-chains:
	.venv/bin/python goat.py chain-report

report-scanners:
	@echo "=== Generating scanner reports ==="
	@for scanner in skillspector cisco snyk; do \
		if [ -f "evaluations/$$scanner/latest.json" ]; then \
			echo "  Generating report for $$scanner..."; \
			.venv/bin/python -c "import json, sys; d=json.load(open('evaluations/$$scanner/latest.json')); print(f'{d.get(\"scanner\", \"unknown\")}: caught={d.get(\"caught\",0)} weak={d.get(\"weak\",0)} bypassed={d.get(\"bypassed\",0)} fp={d.get(\"false_positives\",0)} blindness={d.get(\"blindness_rate\",0):.1%}')" evaluations/$$scanner/chains.json 2>/dev/null || true; \
		done

report:
	@$(MAKE) report-chains
	@$(MAKE) report-scanners
	@echo "=== Generating HTML report ==="
	@.venv/bin/python -c "
import json, glob
from pathlib import Path
report = ['# SkillsGoat Evaluation Report', '', 'Generated: ' + __import__('datetime').datetime.now().isoformat(), '']
for f in glob.glob('evaluations/*/latest.json'):
    with open(f) as fp: d = json.load(fp)
    scanner = d.get('scanner', 'unknown')
    r = d.get('rows', [])
    caught = sum(1 for r in r if r.get('status')=='CAUGHT')
    weak = sum(1 for r in r if r.get('status')=='WEAK-FLAG')
    bypassed = sum(1 for r in r if r.get('status')=='BYPASSED')
    print(f'## {scanner}')
    print(f'- Caught: {caught}')
    print(f'- Weak: {weak}')
    print(f'- Bypassed: {bypassed}')
    print()
" > evaluation_report.md
	@echo "Report written to evaluation_report.md"

# =============================================================================
# CI/CD Gates
# =============================================================================

# Fail if blindness threshold exceeded
ci-gate:
	@echo "=== CI Gate: Checking blindness thresholds ==="
	@python3 -c "
import json, sys, glob
failed = False
for f in glob.glob('evaluations/*/chains.json'):
    with open(f) as fp:
        d = json.load(fp)
    blind = d.get('structurally_blind', 0)
    total = d.get('chains', 0)
    rate = blind / max(d['chains'], 1)
    scanner = f.split('/')[1]
    print(f'{scanner}: {blind}/{total} blind ({rate:.1%})')
    if scanner == 'skillspector' and rate > 0.5:
        print(f'  FAIL: {scanner} blindness rate {rate:.1%} > 50%')
        sys.exit(1)
    if scanner == 'cisco' and rate > 0.5:
        print(f'  FAIL: {scanner} blindness rate {rate:.1%} > 50%')
        sys.exit(1)
print('All gates passed!')
"

# =============================================================================
# Reporting & Documentation
# =============================================================================

report-chains:
	.venv/bin/python goat.py chain-report

# Regenerate indexes and AIBOM manifests
index:
	.venv/bin/python goat.py index --emit-aibom

# Inventory of file types in corpus
inventory:
	.venv/bin/python goat.py inventory

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -rf evaluations/*/latest.json evaluations/*/chains.json evaluations/*/report.md evaluations/*/*.json
	rm -rf evaluations/.composite
	rm -f evaluations/snyk-labs/results.csv
	rm -rf evaluations/snyk-labs/evidence/*/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

clean-all: clean
	rm -rf .venv
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf htmlcov .coverage

# =============================================================================
# Development Helpers
# =============================================================================

# Format code
fmt:
	ruff format .
	ruff check --fix .

# Type check
typecheck:
	mypy goat.py

# Run pre-commit hooks
pre-commit:
	pre-commit run --all-files

# Update dependencies
update-deps:
	pip install --upgrade pip
	pip install -e ".[dev,scanners]" --upgrade

# Install pre-commit hooks
install-hooks:
	pre-commit install

# =============================================================================
# CI/CD Shortcuts
# =============================================================================

# Run full CI pipeline locally
ci-local: lint test scan-all scan-chains ci-gate
	@echo "=== Local CI pipeline complete ==="

# Quick sanity check
smoke-test:
	.venv/bin/python goat.py scan --scanners skillspector --no-llm --mode atomic --timeout 30 --output /tmp/smoke.json
	@echo "Smoke test passed!"

