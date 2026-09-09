# Scanner evaluation ledger

Do not quote recall, FP-rate, or chain blindness without a **last-run date**, a scanner version (or UI build), and which corpus snapshot was scored. Scores go stale when fixtures are added (plugin-distribution, C35+) or when a vendor ships a new engine.

Re-run CLI matrices after Phase 0–1 packaging; refresh this table in the same PR as the new `matrix.json`.

| Scanner | Surface | Last run | Version / build | Corpus scored | Notes |
|---|---|---|---|---|---|
| NVIDIA SkillSpector | CLI (`goat.py scan`) | **2026-09-03** | `--no-llm` (report does not pin a package version) | 70 atomics (`matrix.json` `total: 70`) | Missing plugin-distribution four + C35. [report](skillspector/report.md) |
| Cisco skill-scanner | CLI | **2026-08-25** | static / no LLM | 70 atomics | Oldest full matrix; same 70-entry snapshot. [report](cisco/report.md) |
| Snyk Agent Scan | CLI `snyk-agent-scan` | **2026-09-03** | 0.6.1 | 12 tier-1 ids, not the full pasture | [report](snyk/report.md) |
| Nova Hunting (`novarun`) | CLI | **2026-09-02** | parser mismatch | attempted full matrix | Every row `ERROR: bad json`. Not a score. [report](nova/report.md) |
| Snyk Labs Skill Scan | web UI | **August 2026** (day not recorded) | anonymous Labs page | 12 tier-1 | 50% timeout. Prefer CLI date above. [report](snyk-labs/report.md) |
| Gen Agent Trust Hub | UI / `POST /api/scan/lookup` | **2026-09-03** | https://ai.gendigital.com/skill-scanner | none (ClawHub URL only) | Format-blindness, not a corpus score. [report](gen/report.md) |
| Socket via skills.sh | UI / audit API | **2026-09-03** | skills.sh + `add-skill.vercel.sh/audit` | none (goat 404) | Do not `npx skills add` this corpus. [report](socket/report.md) |
| Metano SkillTracer | UI | probe only (no `scanned_at`) | labs.metano.ai | not scored | Public reports; do not upload pasture. [PROTOCOL](ui/PROTOCOL.md) |
| Manifold Manifest | UI | never run | manifest.manifold.security | — | GitHub-repo input only. [drivers](ui/drivers.yaml) |
| Air ScanAir | product graph | never run | air.security | — | Repo-graph, not a SKILL.md dropzone. [drivers](ui/drivers.yaml) |

The [evasion matrix comparison](../docs/EVASION_MATRIX.md) mixes SkillSpector **2026-09-03** with Cisco **2026-08-25**. Treat that table as two dated snapshots, not a same-day bake-off.

`docs/USAGE.md` already says re-run monthly and pin version in `matrix.json`. This file is the index that README and papers should cite.
