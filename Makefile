# SkillsGoat Makefile — research clone + scan. Do not treat this as a product installer.

.PHONY: help install setup setup-index uninstall-skills test lint selftest \
	scan-all scan-skillspector scan-cisco scan-snyk scan-chains report report-chains \
	clean doctor index inventory fmt

help:
	@echo "SkillsGoat — labeled research goat. Test in a local or cloud sandbox"
	@echo "(OS sandbox, container, VM, or throwaway remote machine). See docs/SAFETY.md."
	@echo "Network C2 is inert; executing pasture scripts or --goat on a host"
	@echo "with secrets is not."
	@echo ""
	@echo "  install            pip install -e '.[dev]'"
	@echo "  setup              ./setup (venv + editable install; no agent links)"
	@echo "  lint / selftest    goat lint / goat selftest"
	@echo "  test               lint + selftest + pytest"
	@echo "  scan-skillspector  goat scan --scanners skillspector --no-llm"
	@echo "  report-chains      regenerate docs/CHAINS.md"
	@echo "  clean              caches only (does not delete pasture *.pyc)"

install:
	pip install --upgrade pip
	pip install -e ".[dev]"

setup:
	./setup

setup-index:
	./setup --index-only

uninstall-skills:
	./setup --uninstall

doctor:
	@echo "=== SkillsGoat Environment Check ==="
	@python3 --version
	@which goat || echo "goat: not on PATH (pip install -e .)"
	@which skillspector || echo "skillspector: NOT FOUND"
	@which skill-scanner || echo "skill-scanner: NOT FOUND"
	@which snyk-agent-scan || echo "snyk-agent-scan: NOT FOUND"

lint:
	.venv/bin/python goat.py lint

selftest:
	.venv/bin/python goat.py selftest

pytest:
	.venv/bin/python -m pytest -q

test: lint selftest pytest
	@echo "All tests passed!"

scan-all:
	@$(MAKE) scan-skillspector
	@$(MAKE) scan-cisco
	@$(MAKE) scan-snyk

scan-skillspector:
	.venv/bin/python goat.py scan --scanners skillspector --no-llm

scan-cisco:
	.venv/bin/python goat.py scan --scanners cisco --no-llm

scan-snyk:
	@if [ -z "$$SNYK_TOKEN" ]; then \
		echo "SKIP: SNYK_TOKEN not set."; \
		exit 0; \
	fi
	.venv/bin/python goat.py scan --scanners snyk

scan-chains:
	.venv/bin/python goat.py scan --scanners skillspector --no-llm --mode both

report: report-chains

report-chains:
	.venv/bin/python goat.py chain-report

index:
	.venv/bin/python goat.py index --emit-aibom

inventory:
	.venv/bin/python goat.py inventory

# Do not delete pasture bytecode fixtures.
clean:
	rm -rf evaluations/.composite
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -not -path "./pasture/*" -delete 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache

fmt:
	ruff format src/goat goat.py tools tests
	ruff check --fix src/goat goat.py tools tests
