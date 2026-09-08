# Snyk Agent Scan CLI — Evaluation Report

**Date:** 2026-09-03 | **Scanner:** `snyk-agent-scan` 0.6.1 (CLI → `api.snyk.io`)  
**Corpus:** 12 tier-1 entries from SkillsGoat (9 malicious, 3 benign)  
**Harness:** `goat.py scan --scanners snyk --ids …` · block threshold = risk score ≥ 600 / 1000

---

## Executive Summary

| Metric | Result |
|---|---|
| **Successful scans** | 12 / 12 (100%) |
| **Malicious detected (block)** | 6 / 9 (67%) |
| **Malicious bypassed** | 3 / 9 |
| **Benign false positives** | 0 / 3 |
| **Wall time (12 entries)** | ~28s |

> **Key finding:** The CLI is reliable (no timeouts) and precise (zero FPs on the twins). It is strong on obvious instruction-channel malice and silent on three Trail-of-Bits primitives: newline-canyon truncation, `.pyc` divergence, and corporate-narrative registry hijack.

---

## Per-Entry Results

| Entry | Truth | Result | Max score | Risks | Notes |
|---|---|---|---|---|---|
| **000-base64-obvious** | Malicious | **CAUGHT** | 1000 | 5 | `eval` of decoded base64 |
| **000-bcc-exfil** | Malicious | **CAUGHT** | 1000 | 2 | Prose-only silent BCC |
| **000-env-harvest-loop** | Malicious | **CAUGHT** | 1000 | 1 | Prompt-injection on harvest loop |
| **000-ignore-previous-instructions** | Malicious | **CAUGHT** | 1000 | 2 | Direct ignore-previous |
| **000-plain-curl-bash** | Malicious | **CAUGHT** | 600 | 1 | Only `unverifiable_dependencies` (curl\|bash) |
| **300-archive-indirection-docx** | Malicious | **CAUGHT** | 1000 | 3 | ToB: docx/ZIP indirection |
| **300-bytecode-poisoning** | Malicious | **BYPASSED** | 0 | 0 | `.pyc` never sent to the API |
| **300-corporate-narrative** | Malicious | **BYPASSED** | 0 | 0 | ToB: narrative armor; `bootstrap.sh` scanned, still clean |
| **300-newline-canyon** | Malicious | **BYPASSED** | 0 | 0 | ToB: 100KB+ padding; SKILL.md submitted, no risks |
| **security-doc-explains-attacks** | Benign | **CLEAN** | 0 | 0 | Quotes attack patterns |
| **ssh-config-reader** | Benign | **CLEAN** | 0 | 0 | Legitimate `~/.ssh/config` read |
| **registry-mirror-documented** | Benign | **CLEAN** | 0 | 0 | Consented corporate mirror |

---

## Key Findings

### 1. Calibration is solid
All five calibration malicious entries blocked. `000-bcc-exfil` (prose-only) and `000-base64-obvious` (markdown `eval`) both scored 1000. That is the opposite of SkillSpector’s two calibration misses.

### 2. Binary carriers are dropped before analysis
`300-bytecode-poisoning` inventory in the JSON is only `SKILL.md` + `scripts/utils.py`. The divergent `.pyc` is not in `files[]`. Agent Scan’s skill client hashes non-UTF-8 bytes and, in this run, did not even list the bytecode file. The Labs **UI** previously caught this fixture (C2/M1). CLI ≠ UI on V5 packing.

### 3. Truncation and narrative still work
`300-newline-canyon` and `300-corporate-narrative` completed (unlike the Labs UI, which timed out) and returned empty `risk_indexes`. Completing the scan and saying “clean” is a worse outcome than a timeout: a gate would install them.

### 4. curl\|bash is a 600, not a 1000
`000-plain-curl-bash` blocked only as `unverifiable_dependencies`. No `malicious_code` index. The engine treated remote-pipe-bash as an unpinned dep, not as exec.

### 5. Zero false positives on the twins
The three benign controls that all timed out on the Labs UI came back CLEAN here. Precision is currently the CLI’s strongest property on this slice.

---

## Comparison: Agent Scan CLI vs Labs UI (same 12)

| Metric | CLI 0.6.1 (this run) | Labs UI (Aug 2026) |
|---|---|---|
| Completion | 12/12 | 6/12 (50% timeout/fail) |
| Malicious caught | 6/9 | 6/6 of those that finished |
| Bytecode poisoning | BYPASSED | CAUGHT |
| Archive indirection | CAUGHT | CAUGHT |
| Corporate narrative | BYPASSED (clean) | TIMEOUT |
| Newline canyon | BYPASSED (clean) | TIMEOUT |
| env-harvest-loop | CAUGHT | SCAN_FAILED |
| Benign FP | 0/3 | 0 (all timed out) |
| Latency | ~28s for 12 | minutes; many hung |

The UI run overstated engine quality by dropping the hard fixtures as timeouts. The CLI run understates packing coverage: it never uploaded the `.pyc`.

---

## Evidence

Raw JSON in `evaluations/snyk/<entry_id>.json`. Scores live under `scan_path_responses[].skill_risks[].risk_indexes`.

---

## Recommendations for Snyk

1. **Upload / unpack non-text skill files** — `.pyc`, `.docx`, encrypted zip. Hashing them is not analysis.
2. **Do not treat a completed empty `risk_indexes` as SAFE** when file size or whitespace ratio is pathological (newline-canyon).
3. **Keep a regression on corporate-narrative** — it is the documented ToB bypass class against Snyk-integrated judges.
4. **Promote curl\|bash from “unverifiable dependency” to malicious_code** when the pipe target is `sh`/`bash`.

---

## Conclusion

Snyk Agent Scan CLI is a usable gate on this slice: fast, complete, zero FPs, and it blocks the instruction-channel calibration set. It is not a packing/truncation/narrative gate. Do not treat Labs UI “caught when it finished” as CLI coverage.

*SkillsGoat evaluation. See `matrix.json` for machine-readable recap.*
