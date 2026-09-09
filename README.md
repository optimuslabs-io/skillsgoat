# SkillsGoat

A deliberately vulnerable corpus for testing whether agent-skill scanners catch real attacks.

Agent skills (`SKILL.md` bundles) ship executable behavior for Claude Code, Codex CLI, OpenClaw, and Cursor. They run with your local privileges. Their descriptions land in model context before anyone reads the files, and the ecosystem ships them unsigned and unscanned. SkillsGoat is built like WebGoat, DVWA, and AI Goat: one fixture per documented class of skill compromise, including techniques that already bypass current scanners.

> ⚠️ **These skills are malicious by design.** Run SkillsGoat in a sandbox. Installing it (`./setup --goat`) loads fixtures into the agent skill path — that is the goat. Endpoints are inert `*.example` / RFC 5737 addresses; archives contain markers, not malware. Do not clone this onto a machine with production secrets. Free default: [nono](https://nono.sh) (local kernel isolation). Throwaway machine: [Daytona](https://www.daytona.io) (sandbox credits, no card). See [docs/SAFETY.md](docs/SAFETY.md).

## What's inside

**74 atomic fixtures (64 malicious + 10 benign) + 35 compound chains**, each with machine-readable ground truth:

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

## Install (research clone)

**Sandbox first.** Canonical commands: [.agents/install-block.md](.agents/install-block.md).
[nono](https://nono.sh) is the free local default; [Daytona](https://www.daytona.io)
is the free throwaway machine. Details: [docs/SAFETY.md](docs/SAFETY.md).

```bash
brew install nono   # https://nono.sh
git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git
cd skillsgoat && ./setup
nono run --allow . -- .venv/bin/python goat.py lint
nono run --allow . -- .venv/bin/python goat.py scan --scanners skillspector --no-llm
```

`./setup` creates a venv and stops. It does **not** link fixtures into
`~/.claude/skills`. To load the goat into agent dirs: `./setup --goat`
(type `GOAT`, or `--confirm-goat` in CI) — do that inside a Daytona
sandbox, or run the agent under nono afterwards.

Plugin manifests (`.claude-plugin/`) stay in the tree for discovery
testing. Do not treat `claude plugins install` or `npx skills add` as
the default path; both can list or load the corpus without the typed
confirm. See [docs/SAFETY.md](docs/SAFETY.md).

## Layout

```
taxonomy.yaml               fixed category registry
setup                       venv + research-mode (use --goat to link fixtures)
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
evaluations/README.md       last-run dates (cite these with any score)
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
