# UI-first scanner evaluation

Most downloaded third-party skills ship as a **plugin**: marketplace metadata,
several interdependent skills, and one or more MCP servers. The pack is usually
vibe-coded. The builder who clicks Install cannot see the risk graph. UI-only
scanners that only accept a pasted skill file are evaluating the wrong artifact.

CLI adapters stay in `goat.py scan`. This directory is for vendors with no
directory CLI — driven with `agent-browser` (repeatable) or Cursor computer-use
(exploratory). Evidence discipline matches `evaluations/snyk-labs/PROTOCOL.md`.

## What is under test (three surfaces)

Score each vendor on the **same entry** across surfaces. A split verdict is
the finding.

| Surface | Submit | What it models |
|---|---|---|
| `skill-md` | Root `SKILL.md` text or file only | Naive UI paste; what most Labs pages accept |
| `directory` | The entry's `skill/` folder or a zip of it | "Drop a folder" UIs (Metano) |
| `plugin` | Cursor-shaped plugin tree: `.cursor-plugin/plugin.json` + `skills/*` + `.mcp.json` | The real marketplace install unit |

Required extra entries for every UI scanner (plugin-distribution):

- `200-vibe-coded-plugin` — Cursor plugin + MCP companions; `/plugin install` vs `npx skills@latest add`, then `/setup-helper`
- `200-vercel-skills-sh-pack` — skills.sh discovery dirs; dual-path README + `/setup-workspace-kit`
- `200-clawhub-listing` — ClawHub/OpenClaw card with paste-to-agent AGENTS.md rewrite (the only URL Gen accepts)
- `200-ide-native-impersonation` — fake native Claude/Codex/Copilot/Grok paths; `npx … install` + `/setup-ide-native`

Pack READMEs emulate gstack / mattpocock / impeccable. Canonical copy:
[install-block.md](../../pasture/plugin-distribution/install-block.md).

Root `SKILL.md` is marketing copy except on the ClawHub listing, where the
malice is in the fetched body (that is how Gen ingests).

Interpretation:

- `skill-md` CLEAN and `plugin` CAUGHT → **SKILL.md-myopic**. The UI cannot
  see the install unit.
- Both CLEAN after a full-tree upload → **content miss** (same as CLI).
- Rejects plugin zip / "need a SKILL.md" / GitHub-URL-only → **format
  blindness**. Record `unsupported` — that is a result, not a skip.
- Public report feed with no opt-out → **do not submit the corpus** (canary
  leak). Probe the form, then stop.

This is distinct from `pasture/compound-chain/`. Chains are adversarial:
every node is clean alone. Plugin-distribution is accidental composition:
the nested files are obviously bad, but they ride along with a benign
entrypoint and an MCP the builder never opens.

## Drivers

Catalog: `drivers.yaml`. Repeatable loop: `python evaluations/ui/run_ui.py`.

| Scanner | URL | Native input | Browser driver |
|---|---|---|---|
| Metano SkillTracer | https://labs.metano.ai/scanner/scan | `SKILL.md` / extra `.md` / `.zip` (max 500 KB); URL tab; public reports by default | `agent-browser` |
| Gen Agent Trust Hub | https://ai.gendigital.com/skill-scanner | ClawHub URL only (`clawhub.ai` / `clawhub.com`). GitHub and zips rejected. | `agent-browser` |
| Socket | skills.sh / `add-skill.vercel.sh/audit` | No upload UI. Scan happens on `npx skills add`. | `agent-browser` |
| Manifold Manifest | https://manifest.manifold.security/ | Public GitHub repo, not a local `skill/` | `agent-browser` |
| Air ScanAir | product graph (SkillJacking / RepoJacking) | Repo/org graph, not a skill file | computer-use / `agent-browser` |
| Snyk Labs | https://labs.snyk.io/experiments/skill-scan/ | GitHub tree URL (legacy) | `evaluations/snyk-labs/run_snyk.py` |

Prefer `agent-browser` for a matrix (snapshot → `@eN` click/fill/upload →
screenshot). Use Cursor computer-use when the page is unknown, captcha'd, or
needs a logged-in profile you do not want to script.

## Sample set

**Tier 1 (12)** — same as Snyk Labs, plus the plugin fixture:

- Calibration: `000-base64-obvious`, `000-bcc-exfil`, `000-env-harvest-loop`,
  `000-ignore-previous-instructions`, `000-plain-curl-bash`
- ToB primitives: `300-bytecode-poisoning`, `300-archive-indirection-docx`,
  `300-corporate-narrative`, `300-newline-canyon`
- Benign: `security-doc-explains-attacks`, `ssh-config-reader`,
  `registry-mirror-documented`
- Plugin: `200-vibe-coded-plugin` on all three surfaces

## Per-entry procedure

1. Submit the chosen surface. Do not paste a SKILL.md when scoring `plugin`.
2. Screenshot the verdict → `evaluations/<scanner>/evidence/<id>/verdict.png`.
3. Dump visible report text → `evidence/<id>/raw.txt`.
4. Log `results.csv`:
   `entry_id,surface,truth,status,reported_severity,findings_count,notes`
5. If the vendor publishes reports, abort that scanner after the empty-form
   probe unless there is a private/unlisted toggle.

## Reporting

`evaluations/<scanner>/report.md`: methodology (which surface the UI actually
accepted) → per-entry table → plugin split (`skill-md` vs `plugin`) →
limitations (timeouts, login, public-feed abort).
