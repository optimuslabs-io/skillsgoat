# SkillsGoat

**Learn what makes an AI agent skill dangerous — and find out whether real scanners actually catch it.**

Agent skills (`SKILL.md` bundles) are a new way to distribute executable behavior for AI agents (Claude Code, Codex CLI, OpenClaw, Cursor). They run with your local privileges, their descriptions are read into model context before any human looks, and the ecosystem ships them unsigned and unscanned. SkillsGoat is a deliberately vulnerable corpus — in the spirit of WebGoat/DVWA/AI Goat — that captures *every documented class of skill compromise*, including the techniques proven to evade today's scanners.

> ⚠️ **These skills are malicious by design.** Never install them into a live agent. All endpoints are inert `*.example`/RFC 5737 addresses; archives contain markers, not malware. See [docs/SAFETY.md](docs/SAFETY.md).

## What's inside

**69 entries across 30 categories**, each with machine-readable ground truth:

- **Calibration set (10)** — must-catch patterns. A scanner missing these is broken, not weak.
- **Classics (10)** — metadata injection, indirect injection, exfiltration, destructive commands, curl-pipe-bash, over-permission, persistence, memory poisoning, confused deputy, typosquatting.
- **Evasion families V1–V13 (~30)** — homoglyph/zero-width/charcode obfuscation, payload dispersion, truncation canyons, LLM-judge manipulation (cover links, judge self-injection, corporate-narrative social engineering), bytecode poisoning, archive indirection, XOR packing, deferred dependency resolution, external staging, silent operators / weaponized Definition-of-Done, dormant codeword gates, shadow features, reputation laundering, self-mutation.
- **Trail-of-Bits primitives (4, derived)** — newline-canyon truncation, `.docx` archive indirection, divergent `.pyc` bytecode, corporate-mirror registry hijack. Each reproduces a bypass demonstrated against ClawHub, skills.sh, and Cisco skill-scanner in June 2026.
- **Ecosystem classes (8)** — transitive dependency poisoning, composition trust-transfer, DNS/error side-channels, model artifact theft, repo-config hook execution (`.claude/settings.json`), MCP tool poisoning, wallet exhaustion.
- **Format-spec noncompliance (4)** — unsafe-YAML frontmatter gadgets, frontmatter-free bundles, symlink escapes out of the bundle, nested skill-in-skill recursion: proof that nothing downstream enforces agentskills.io
- **Benign FP-bait (10)** — look suspicious on purpose; measure false-positive rates.

Every entry: `skill/` (the only thing you point a scanner at) + `expected.yaml` (verdict, category mapping to OWASP AST10 / SkillSpector pattern codes / V-codes, plain-English rationale) + an embedded canary token.

## Use it

```bash
pip install pyyaml

python3 goat.py lint          # validate corpus consistency
python3 goat.py index         # regenerate indexes (--emit-aibom for manifests)
python3 goat.py quiz          # learn: benign or malicious?
python3 goat.py scan --scanners skillspector --no-llm   # evaluate a scanner
python3 goat.py selftest
```

Scanner evaluation requires the scanner CLIs on PATH (`skillspector`, `skill-scanner`). Results land in `evaluations/<scanner>/report.md`.

## Layout

```
taxonomy.yaml               fixed category registry
pasture/<category>/<tier>-<name>/
  expected.yaml             ground truth (OUTSIDE scannable tree)
  skill/                    point scanners HERE
docs/
  PROBLEM_SPACE.md          the full problem landscape & risk ranking
  EVASION_MATRIX.md         scanner assumption → technique map (V1–V13)
  SAFETY.md                 inert-payload policy, canaries, disclosure
tools/gen_binaries.py       regenerates .pyc/.docx/.dat/.zip artifacts
evaluations/<scanner>/      per-scanner matrices and raw JSON
```

## Tiers

| Tier | Meaning |
|---|---|
| 000 | In plain sight — every scanner must catch |
| 100 | One hop away (another file or step) |
| 200 | Purpose-built to slip past pattern matching |
| 300 | Multi-stage, judge-targeting, binary-artifact based |

## Credits & lineage

Inspired by [nandangupta-security/SkillsGoat](https://github.com/nandangupta-security/SkillsGoat), [trailofbits/overtly-malicious-skills](https://github.com/trailofbits/overtly-malicious-skills) (primitives derived, not copied verbatim), [AI Goat](https://github.com/orcasecurity-research/AIGoat), [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/), NVIDIA SkillSpector, Cisco skill-scanner, Snyk ToxicSkills, and the Cloak-and-Detonate evasion study.

## Responsible use

This is defensive research tooling: ground truth for scanner evaluation and analyst training. If evaluation reveals weaknesses in maintained scanners, notify vendors before publishing exploit detail. See [docs/SAFETY.md](docs/SAFETY.md).
