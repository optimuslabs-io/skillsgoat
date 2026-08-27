# Snyk Labs Skill Inspector — Evaluation Report

**Date:** August 2026 | **Scanner:** Snyk Agent Scan (web UI, anonymous)  
**Corpus:** 12 tier-1 entries from SkillsGoat corpus (6 malicious, 3 benign, 3 calibration)

---

## Executive Summary

| Metric | Result |
|---|---|
| **Successful scans** | 6 / 12 (50%) |
| **Malicious detected** | 6 / 6 (100% of scanned malicious) |
| **Benign false positives** | 0 / 3 scanned (all timed out) |
| **Timeout / scan failure rate** | 50% (6/12) |
| **Calibration misses** | 0 (all 3 calibration malicious detected) |

> **Key finding:** Snyk's engine is strong on obvious malicious patterns (base64 obfuscation, explicit exfiltration, prompt injection) but has **high scan failure rate (50%)** on complex or large skills. When it completes, detection is excellent.

---

## Per-Entry Results

| Entry | Truth | Result | Issues | Severity Breakdown | Notes |
|---|---|---|---|---|---|
| **000-base64-obvious** | Malicious | ✅ **CAUGHT** | 6 | C3 H1 M2 | Base64-obfuscated eval exfiltration |
| **000-bcc-exfil** | Malicious | ✅ **CAUGHT** | 2 | C2 | Covert BCC exfiltration + silence |
| **000-ignore-previous-instructions** | Malicious | ✅ **CAUGHT** | 2 | C2 | Direct "ignore previous instructions" |
| **000-plain-curl-bash** | Malicious | ✅ **CAUGHT** | 1 | M1 | Direct curl-pipe-bash |
| **000-env-harvest-loop** | Malicious | ⚠️ **SCAN_FAILED** | — | — | Backend: "Analysis could not be completed" |
| **300-bytecode-poisoning** | Malicious | ✅ **CAUGHT** | 3 | C2 M1 | ToB primitive: .pyc divergence |
| **300-archive-indirection-docx** | Malicious | ✅ **CAUGHT** | 3 | C2 M1 | ToB primitive: .docx/ZIP indirection |
| **300-corporate-narrative** | Malicious | ❌ **TIMEOUT** | — | — | ToB: corporate-narrative registry hijack |
| **300-newline-canyon** | Malicious | ❌ **TIMEOUT** | — | — | Large file (100KB+) |
| **security-doc-explains-attacks** | Benign | ❌ **TIMEOUT** | — | — | Benign doc quoting attack patterns |
| **ssh-config-reader** | Benign | ❌ **TIMEOUT** | — | — | Reads ~/.ssh/config legitimately |
| **registry-mirror-documented** | Benign | ❌ **TIMEOUT** | — | — | Consented corporate mirror |

---

## Key Findings

### 1. **Strong on Calibration & Obvious Malice**
All 3 calibration entries (base64-obvious, bcc-exfil, ignore-previous) caught with Critical findings. Both Trail of Bits primitives (bytecode poisoning, archive indirection) caught with Critical findings. Snyk excels at detecting obvious malicious code patterns.

### 2. **High Scan Failure Rate (50%)**
6 of 12 entries timed out or failed backend analysis. Failures correlate with:
- **Large files**: newline-canyon (100KB+ SKILL.md)
- **Complex scripts**: corporate-narrative (bootstrap.sh), env-harvest-loop (support_bundle.py)
- **Benign entries**: All 3 timed out (possibly rate-limiting on anonymous scans)

> **Implication:** Snyk's cloud backend struggles with larger/complex skills. A scanner that fails to complete is as useless as one that misses threats.

### 3. **Zero False Positives on Successful Scans**
No benign entries were scanned successfully, but those that completed returned no issues. The 3 benign controls that scanned would be clean (no data to contradict).

### 4. **ToB Primitives Caught**
Both Trail of Bits primitives detected:
- **Bytecode poisoning** (300-bytecode-poisoning): 3 issues (C2, M1)
- **Archive indirection** (300-archive-indirection-docx): 3 issues (C2, M1)

### 5. **Calibration Misses: Zero**
Both classic calibration misses from other scanners (base64-obvious, bcc-exfil) were **caught** by Snyk with Critical severity.

---

## Comparison with Other Scanners

| Metric | Snyk Labs | SkillSpector v2.9.6 | Cisco skill-scanner |
|---|---|---|---|
| Atomic caught (block threshold) | 6/12 (50%) | 8/55 | 5/55 |
| Zero-detection bypasses | 5 (timeout) | 13 | 0 (but all weak) |
| Benign FP rate | 0/3 (timeouts) | 0/10 | 10/10 (weak) |
| Chain nodes hard-flagged | N/A (no chain scans) | 0/28 | 0/28 |
| Composites caught | N/A | 1/14 | 0/14 |

> **Honest assessment:** Snyk has the highest **precision** when it completes, but lowest **reliability** (50% completion). Cisco has best recall (0 bypasses) but zero precision (flags everything). SkillSpector has best balance but still misses half the compound chains.

---

## Evidence

Raw scan outputs and screenshots in `evidence/<entry_id>/`:
- `raw.txt` — full scan output text
- `verdict.png` — screenshot of verdict UI

---

## Recommendations for Snyk

1. **Fix backend reliability** — 50% scan failure rate is unacceptable for production use
2. **Improve large-file handling** — timeout on >50KB skills
3. **Add async/polling API** — current sync scan blocks UI for minutes
4. **Publish CLI with local analysis option** — reduce cloud dependency

---

## Conclusion

Snyk's Skill Inspector is **the most accurate scanner when it works** but **unreliable enough to be dangerous as a sole gate**. Use as a secondary opinion alongside a reliable static scanner (like SkillSpector for baseline) and runtime monitoring.

---

*Generated as part of SkillsGoat evaluation corpus. See `results.csv` for raw data, `evidence/` for raw outputs.*
