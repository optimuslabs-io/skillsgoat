# Snyk Labs Skill Scan — Manual Evaluation Protocol

Snyk's skill scanner is UI-only (no CLI/API), so this is a scripted manual
pass. Budget ~45 min. Evidence discipline: save a screenshot + the raw report
text for every entry, or the run doesn't count.

## Setup
1. Open https://labs.snyk.io/experiments/skill-scan/
2. Create `evaluations/snyk-labs/evidence/<entry-id>/` per entry tested.
3. Record scanner version/date shown in the UI footer in `metadata.yaml`.

## Sample set (prioritized; stop after tier-2 if time-boxed)

**Tier 1 — must-run (12)**
- Calibration: `000-base64-obvious`, `000-bcc-exfil`, `000-env-harvest-loop`,
  `000-ignore-previous-instructions`, `000-plain-curl-bash`
- ToB primitives: `300-bytecode-poisoning`, `300-archive-indirection-docx`,
  `300-corporate-narrative`, `300-newline-canyon`
- Benign controls: `security-doc-explains-attacks`, `ssh-config-reader`,
  `registry-mirror-documented`

**Tier 2 — chain spot-checks (6 composites via zip upload if supported)**
- Assemble with: `.venv/bin/python -c "from goat import discover_chains, assemble_composite; from pathlib import Path; c=[c for c in discover_chains() if c['id']in('c1-memory-handoff','c11-soul-c2','c6-mcp-cross-skill','c12-inference-hijack','c13-skill-factory','c5-repoconfig-rootkit')]; [assemble_composite(x, Path('evaluations/.composite')/x['id']) for x in c]"`
  then zip each `evaluations/.composite/<id>/skill/` and submit.
- If zip upload is rejected, record "unsupported" — that itself is a finding
  (no whole-graph surface = structural blindness by construction).

## Per-entry procedure
1. Upload/submit the entry's `skill/` directory contents (zip if required).
2. Screenshot full verdict → `evidence/<id>/verdict.png`.
3. Copy raw findings text → `evidence/<id>/raw.txt`.
4. Log one row in `results.csv`:
   `entry_id,truth,reported_severity,findings_count,matched_expected(Y/N),notes`

## Expected results (from sibling scanners — hypothesis to test)
- Prose-only injections (bcc-exfil, ignore-previous): likely weak/no signal
- Narrative armor (`corporate-narrative`): likely passes (ToB showed exactly this vs Snyk-integrated scanners)
- Bytecode/docx: post-ToB fixes may catch; verify which side of June→Aug these fall

## Reporting
Write `evaluations/snyk-labs/report.md`: methodology → per-tier tables →
comparison vs `skillspector/report.md` + `cisco/report.md` → limitations
(UI-only, no version pinning beyond date, single run per entry).
