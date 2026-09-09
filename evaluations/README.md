# Scanner evaluation ledger

Re-run matrices from a **local or cloud sandbox** you already trust.
`goat scan` may upload skill text to the scanner or an LLM. Do not quote
recall, FP-rate, or chain blindness without a **last-run date**, a scanner
version (or UI build), which corpus snapshot was scored, and **`blind: true`**
in `matrix.json`. `goat scan` defaults to `--blind` (hashed fixture dirs,
canaries stripped, `expected.yaml` never in scanner input). `--no-blind`
scores are debugging artifacts.

Scores go stale when fixtures are added or when a vendor ships a new engine.

| Scanner | Surface | Last run | Version / build | Corpus scored | Blind? | Notes |
|---|---|---|---|---|---|---|
| NVIDIA SkillSpector | CLI (`goat scan`) | **2026-09-09T05:49Z** | v2.11.0 `--no-llm` | 76 atomics; 35 chains | **yes** (`blind: true`, salt+token in [matrix.json](skillspector/matrix.json) / [chains.json](skillspector/chains.json)) | Strict recall 9/66; FP-rate 0.6; chain structural blindness 27/35. [report](skillspector/report.md) |
| Cisco skill-scanner | CLI | **2026-09-09T05:54Z** | 2.0.13, static / no LLM | 76 atomics; 35 chains | **yes** | Strict recall 5/64 (two ingest errors); FP-rate 1.0; chain structural blindness 28/35. [report](cisco/report.md) |
| Nova Hunting (`novarun`) | CLI | **2026-09-09T05:55Z** | parser mismatch (`novarun --version` is usage text) | 76 atomics attempted | **yes** (staged blind; every row still `ERROR`) | Not a score. [report](nova/report.md) |
| Snyk Agent Scan | CLI `snyk-agent-scan` | **2026-09-03** | 0.6.1 | 12 tier-1 ids, not the full pasture | **no** | Not re-run blind (`SNYK_TOKEN` unset). [report](snyk/report.md) |
| Snyk Labs Skill Scan | web UI | **August 2026** (day not recorded) | anonymous Labs page | 12 tier-1 | n/a | 50% timeout. Prefer CLI date above. [report](snyk-labs/report.md) |
| Gen Agent Trust Hub | UI / `POST /api/scan/lookup` | **2026-09-03** | https://ai.gendigital.com/skill-scanner | none (ClawHub URL only) | n/a | Format-blindness, not a corpus score. [report](gen/report.md) |
| Socket via skills.sh | UI / audit API | **2026-09-03** | skills.sh + `add-skill.vercel.sh/audit` | none (goat 404) | n/a | Do not `npx skills add` this corpus. [report](socket/report.md) |
| Metano SkillTracer | UI | probe only (no `scanned_at`) | labs.metano.ai | not scored | n/a | Public reports; do not upload pasture. [PROTOCOL](ui/PROTOCOL.md) |
| Manifold Manifest | UI | never run | manifest.manifold.security | — | n/a | GitHub-repo input only. [drivers](ui/drivers.yaml) |
| Air ScanAir | product graph | never run | air.security | — | n/a | Repo-graph, not a SKILL.md dropzone. [drivers](ui/drivers.yaml) |

The [evasion matrix comparison](../docs/EVASION_MATRIX.md) is the SkillSpector
v2.11.0 / Cisco 2.0.13 **2026-09-09 `--blind`** bake-off on 76 atomics + 35
chains. Cite it only with `scanned_at` and `"blind": true` from the JSON
linked above.

`docs/USAGE.md` already says re-run monthly and pin version in `matrix.json`.
This file is the index that README and papers should cite.
