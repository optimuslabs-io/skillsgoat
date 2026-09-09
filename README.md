# SkillsGoat

A deliberately vulnerable corpus for testing whether agent-skill scanners catch real attacks.

Agent skills (`SKILL.md` bundles) ship executable behavior for Claude Code, Codex CLI, OpenClaw, and Cursor. They run with your local privileges. Their descriptions land in model context before anyone reads the files, and the ecosystem ships them unsigned and unscanned. SkillsGoat is built like WebGoat, DVWA, and AI Goat: one fixture per documented class of skill compromise, including techniques that already bypass current scanners.

> ⚠️ **These skills are malicious by design.** Installing SkillsGoat loads the fixtures into the agent skill path. That is the goat. Endpoints are inert `*.example` / RFC 5737 addresses; archives contain markers, not malware. Don't do this on a machine with production secrets. See [docs/SAFETY.md](docs/SAFETY.md).

## What's inside

**74 attack fixtures + 35 compound chains**, each with machine-readable ground truth:

- **Calibration set (10):** must-catch patterns. A scanner missing these is broken, not weak.
- **Classics (10):** metadata injection, indirect injection, exfiltration, destructive commands, curl-pipe-bash, over-permission, persistence, memory poisoning, confused deputy, typosquatting.
- **Evasion families V1–V13 (~30):** homoglyph/zero-width/charcode obfuscation, payload dispersion, truncation canyons, LLM-judge manipulation (cover links, judge self-injection, corporate-narrative social engineering), bytecode poisoning, archive indirection, XOR packing, deferred dependency resolution, external staging, silent operators / weaponized Definition-of-Done, dormant codeword gates, shadow features, reputation laundering, self-mutation.
- **Trail-of-Bits primitives (4, derived):** newline-canyon truncation, `.docx` archive indirection, divergent `.pyc` bytecode, corporate-mirror registry hijack. Each reproduces a bypass shown against ClawHub, skills.sh, and Cisco skill-scanner in June 2026.
- **Ecosystem classes (9):** transitive dependency poisoning, composition trust-transfer, DNS/error side-channels, model artifact theft, repo-config hook execution (`.claude/settings.json`), MCP tool poisoning, marketplace / IDE packs (gstack / mattpocock / impeccable install stories, ClawHub listings, packs that impersonate native Claude/Codex/Copilot/Grok skills), wallet exhaustion.
- **Format-spec noncompliance (4):** unsafe-YAML frontmatter gadgets, frontmatter-free bundles, symlink escapes out of the bundle, nested skill-in-skill recursion. Nothing downstream enforces agentskills.io.
- **Benign FP-bait (10):** look suspicious on purpose; measure false-positive rates.

Every entry has `skill/` (the only thing you point a scanner at), `expected.yaml` (verdict, category mapping to OWASP AST10 / SkillSpector pattern codes / V-codes, a plain-English rationale), and an embedded canary token.

## Scope & Exclusions

SkillsGoat covers malicious and vulnerable skill *content*: what ships inside a bundle, and what happens when an agent loads it. These adjacent threats are out of scope:

| Excluded | Why | Where it lives later |
|---|---|---|
| **Platform vulnerabilities** (localhost WebSocket hijacking, checkout-time RCE from harness bugs) | Bugs in the agent platform itself, not skill content | Vendor advisories / CVE process |
| **Prompt-only exploitation** (adversarial prompts weaponizing *already-installed benign* skills — SkillAttack-style) | Nothing malicious ships in any bundle; needs a live-agent detonation harness | Phase 3: gym/detonation layer |
| **Registry & lifecycle attacks on installed fleets** (rug-pulls, deleted-account dependency takeover, fleet update drift) | Registry/ops problem; needs a marketplace simulator | Phase 2: version-drift suite |
| **Model-layer attacks** (base-model jailbreaks, training-data poisoning) | Independent of the skills layer | OWASP LLM Top 10 territory |

In scope: injection, obfuscation, packing, persistence, memory/soul poisoning, supply-chain chaining, marketplace-hosted packs (Vercel skills.sh, ClawHub, Cursor plugins, third-party trees that impersonate native Claude/Codex/Copilot/Grok skills), and compound cross-skill attacks under `pasture/compound-chain/`.

Evaluate UI-only vendors (Metano, Gen, Socket, Manifold, Air) with browser automation against that plugin unit, not a pasted `SKILL.md`. See [evaluations/ui/PROTOCOL.md](evaluations/ui/PROTOCOL.md).

## Compound chains

Single-skill fixtures test one weakness at a time. Real compromises chain across **state channels** (agent memory, context window, repo/env state, shared tool layer) and **trust edges** (skill→skill, dep→skill, external→skill, session→future). Under `pasture/compound-chain/`, each entry is a multi-skill bundle where **every node scans clean alone** and only the graph is malicious. Ground truth (`chain.yaml`) covers four deployment contexts: developer endpoint, long-lived server agent, CI/CD runner, and hosted sandbox. See [docs/CHAIN_SCHEMA.md](docs/CHAIN_SCHEMA.md).

## Roadmap

Next: version-drift suite (benign→poisoned paired fixtures), judge-benchmark leaderboard, detonation layer.

## Install (30 seconds)

The install commands live in [.agents/install-block.md](.agents/install-block.md).

Open Claude Code and paste this. Claude does the rest.

> Install SkillsGoat: run **`git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git ~/.claude/skills/skillsgoat && cd ~/.claude/skills/skillsgoat && ./setup`**. Then add a "SkillsGoat" section to CLAUDE.md that says this is a goat (fixtures are malicious by design, endpoints inert), to use `/setup-skillsgoat` after git pull, and to evaluate scanners with `python3 goat.py scan --scanners skillspector --no-llm`. Then ask the user if they also want SkillsGoat on the current project so teammates get it (`./setup --team`).

### Claude Code plugin

```bash
claude plugins marketplace add optimuslabs-io/skillsgoat
claude plugins install skillsgoat
```

Or `/plugin marketplace add optimuslabs-io/skillsgoat` then `/plugin install skillsgoat`. Then `/setup-skillsgoat` once.

### Codex, Cursor, Copilot, Grok, and other agents

```bash
npx skills@latest add optimuslabs-io/skillsgoat
```

Pick the skills and which agents to install them on. **Make sure `setup-skillsgoat` is one of them.** This installs the pasture fixtures.

The plugin route and the skills.sh route are exclusive. Installing both leaves every fixture twice.

Then run `/setup-skillsgoat` once per machine (and `./setup --team` in a shared repo). After that: `python3 goat.py lint`, `python3 goat.py scan --scanners skillspector --no-llm`.

## Layout

```
taxonomy.yaml               fixed category registry
setup                       gstack-style installer (links fixtures into agent dirs)
skills/                     npx skills add discovery index (symlinks into pasture)
pack/skills/setup-skillsgoat
.claude-plugin/             Claude marketplace plugin (loads skills/)
pasture/<category>/<tier>-<name>/
  expected.yaml             ground truth (OUTSIDE scannable tree)
  skill/                    point scanners HERE (plugin-distribution: marketplace/IDE pack)
docs/
  EVASION_MATRIX.md         scanner assumption → technique map (V1–V13)
  SAFETY.md                 inert-payload policy, canaries, disclosure
tools/gen_binaries.py       regenerates .pyc/.docx/.dat/.zip artifacts
evaluations/<scanner>/      per-scanner matrices and raw JSON
evaluations/ui/             browser/computer-use protocol for UI-only vendors
```

## Tiers

| Tier | Meaning |
|---|---|
| 000 | In plain sight. Every scanner must catch these. |
| 100 | One hop away (another file or step) |
| 200 | Built to slip past pattern matching |
| 300 | Multi-stage, judge-targeting, or binary-artifact based |

## Credits & lineage

Inspired by [nandangupta-security/SkillsGoat](https://github.com/nandangupta-security/SkillsGoat), [trailofbits/overtly-malicious-skills](https://github.com/trailofbits/overtly-malicious-skills) (primitives derived, not copied verbatim), [AI Goat](https://github.com/orcasecurity-research/AIGoat), [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/), NVIDIA SkillSpector, Cisco skill-scanner, Snyk ToxicSkills, and the Cloak-and-Detonate evasion study.

## Responsible use

This is defensive research tooling: ground truth for scanner evaluation and analyst training. If evaluation shows a gap in a maintained scanner, notify the vendor before publishing exploit detail. See [docs/SAFETY.md](docs/SAFETY.md).
