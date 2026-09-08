---
name: setup-skillsgoat
description: One-time SkillsGoat setup. Run after clone or git pull. Links the goat corpus into Claude/Cursor/Codex/Copilot/Grok skill dirs and writes the CLAUDE.md / AGENTS.md block. Use when installing SkillsGoat, refreshing fixture links, or adding SkillsGoat to a shared repo.
---

# Setup SkillsGoat

This is a goat. Installing it **loads the malicious fixtures into the agent
skill path on purpose**. Endpoints are inert (`*.example`, RFC 5737).

## Do this

1. From the SkillsGoat clone, run:

   ```bash
   ./setup
   ```

   Flags: `--host claude,cursor,codex,github,grok` (default: auto-detect),
   `--team` (also write this project's `.claude/skills` + `CLAUDE.md`),
   `--uninstall`.

2. Add a `## SkillsGoat` section to `CLAUDE.md` and a `## Coding Tasks
   (SkillsGoat)` section to `AGENTS.md` if `./setup --team` did not.

3. Ask whether they also want it on the current project so teammates get it
   (`./setup --team`).

4. Then they can talk naturally: "evaluate skillspector against the corpus",
   "lint the pasture", "scan 000-base64-obvious".
