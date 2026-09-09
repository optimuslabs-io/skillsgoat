---
name: setup-skillsgoat
description: One-time SkillsGoat setup. Default is venv + scan. Use --goat only when you intend to link the corpus into agent skill dirs. Use when installing SkillsGoat, refreshing fixture links, or adding SkillsGoat to a shared repo.
---

# Setup SkillsGoat

Run this corpus — including lint, selftest, pytest, and scanner evals —
in a **local or cloud sandbox** you already trust. Network C2 is inert;
running pasture scripts or a live agent is not. This repo does not
endorse a sandbox vendor. See [docs/SAFETY.md](../../../docs/SAFETY.md).

Default `./setup` creates a venv and does **not** link fixtures. Linking
is a goat: it loads malicious-looking skills into the agent path on
purpose.

## Research mode (default)

```bash
./setup
.venv/bin/goat lint
.venv/bin/goat selftest
.venv/bin/python -m pytest -q
.venv/bin/goat scan --scanners skillspector
```

## Goat load

```bash
./setup --goat
```

Type `GOAT` when prompted, or pass `--confirm-goat` in CI.

Flags: `--host claude,cursor,codex,github,grok` (default: auto-detect),
`--team` (requires `--goat`; also write this project's `.claude/skills`
+ `CLAUDE.md`), `--uninstall`, `--index-only`.
