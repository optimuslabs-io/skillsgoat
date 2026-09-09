---
name: setup-skillsgoat
description: One-time SkillsGoat setup. Default is venv + scan. Use --goat only when you intend to link the corpus into agent skill dirs. Use when installing SkillsGoat, refreshing fixture links, or adding SkillsGoat to a shared repo.
---

# Setup SkillsGoat

Run this corpus in a sandbox: [nono](https://nono.sh) (local kernel
isolation) or a [Daytona](https://www.daytona.io) throwaway machine.
See [docs/SAFETY.md](../../../docs/SAFETY.md).

Default `./setup` creates a venv and does **not** link fixtures. Linking
is a goat: it loads malicious-looking skills into the agent path on
purpose. Endpoints are inert (`*.example`, RFC 5737).

## Research mode (default)

```bash
./setup
.venv/bin/python goat.py lint
.venv/bin/python goat.py scan --scanners skillspector --no-llm
```

## Goat load

```bash
./setup --goat
```

Type `GOAT` when prompted, or pass `--confirm-goat` in CI.

Flags: `--host claude,cursor,codex,github,grok` (default: auto-detect),
`--team` (requires `--goat`; also write this project's `.claude/skills`
+ `CLAUDE.md`), `--uninstall`, `--index-only`.
