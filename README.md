# SkillsGoat

**A practice target for AI agent-skill scanners, the way WebGoat is one for web scanners.** SkillsGoat is a set of agent skills that are malicious by design, each labeled with the correct answer, so you can measure whether a scanner actually catches them.

- **83 single-skill fixtures** — 70 malicious, 13 benign (the benign ones look suspicious on purpose, to catch false alarms).
- **37 compound chains** — each skill looks harmless on its own; only the combination is the attack.
- **Every payload is inert** — fake `*.example` endpoints, no real network calls.

It's for people building or evaluating skill scanners, and analysts learning what a malicious skill looks like.

## How to use this

Work from a sandbox (see the ⚠️ note below). Pick the workflow you need:

- **Evaluate any scanner.** Point it at `pasture/<category>/<id>/skill/` and compare its verdict to that entry's `expected.yaml` (which lives one level up, outside what the scanner sees). Nothing else is required.
- **Score a supported scanner.** `goat scan --scanners skillspector` runs it across the whole collection, strips the answer key first (blind), and writes a matrix to `evaluations/skillspector/`. Adapters ship for `skillspector`, `cisco`, `snyk`, and `nova`.
- **Include the compound chains.** Add `--mode both` to also score the attacks where every skill scans clean on its own and only the graph is malicious.
- **Gate CI on it.** `goat scan --blind --assert-only` proves the answer key never reaches a scanner; add your own recall / false-positive threshold to fail a build.
- **Add your own scanner.** Register its command in `SCANNER_CONFIGS` (`src/goat/main.py`): the executable, its JSON flag, and its static-only flag.
- **Read the scores.** Recall, false-positive rate, and compound-chain blindness per scanner, dated, in [evaluations/README.md](evaluations/README.md). Only `"blind": true` matrices are citable.

New here? Start with [Install and test](#install-and-test-research-clone), then [Scoring (blind)](#scoring-blind).

Any agent that loads a `SKILL.md` bundle runs it with local privileges, and the description lands in model context before anyone reads the files. That is the whole reason to scan them.

> ⚠️ **These skills are malicious by design.** Clone, test (`goat lint` / `selftest` / `pytest` / `goat scan`), and `./setup --goat` in a **local or cloud sandbox** you already trust. Network endpoints are inert (`*.example` / RFC 5737); running a pasture script or a live agent against this tree can still touch local files. Do not do this on a machine with production secrets. We do not endorse a sandbox vendor. Disclaimers: [docs/SAFETY.md](docs/SAFETY.md).

## Terms

- **Pasture** — the fixture tree (`pasture/`). We coined the name; goats graze there. An entry is `pasture/<category>/<id>/`.
- **Collection** — the fixture set in this repo.
- **Bundle** — one skill pack: a `skill/` tree, a marketplace/IDE pack, or a compound-chain node.
- **Repo** — this GitHub tree (harness plus collection).
- **Atomic** — one skill, one technique.
- **Compound chain** — several skills; only the composition is malicious.
- **Tier** — difficulty, `000` (in plain sight) to `300` (multi-stage, binary, or judge-targeting).
- **Ground truth** — the answer key for an entry (`expected.yaml`, or `chain.yaml` for a chain), kept outside the `skill/` tree a scanner sees.
- **Canary** — a unique `GOAT-CANARY-*` token in every fixture; if it shows up in the wild, a fixture leaked.
- **Blind** — the default `goat scan` mode: fixtures are copied to hashed directories with canaries and answer keys stripped, so a scanner can't cheat by reading the label.

## What's inside

The fixtures, grouped by attack type:

- **Calibration set (10):** must-catch patterns. A scanner missing these is broken, not weak.
- **Classics (10):** metadata injection, indirect injection, exfiltration, destructive commands, curl-pipe-bash, over-permission, persistence, memory poisoning, confused deputy, typosquatting.
- **Evasion families V1–V15 (~35):** homoglyph/zero-width/charcode obfuscation, payload dispersion, truncation canyons, LLM-judge manipulation (cover links, judge self-injection, corporate-narrative social engineering), bytecode poisoning, archive indirection, XOR packing, deferred dependency resolution, external staging, silent operators / weaponized Definition-of-Done, dormant codeword gates, shadow features, reputation laundering, self-mutation. Four of these derive Trail of Bits [overtly-malicious-skills](https://github.com/trailofbits/overtly-malicious-skills) primitives (rewritten, not copied): newline-canyon, `.docx` archive indirection, divergent `.pyc`, corporate-narrative registry hijack.
- **Provenance & time (V14–V15 + temporal):** the scanned artifact is not the executed behavior — reconstruction-from-reference (agent rebuilds a skill from an external link; nothing installs), out-of-band distribution (raw clone / manual upload routes around the marketplace), and a time-delayed external sleeper (innocuous at review, fetch-and-exec after a date).
- **Ecosystem classes (9):** transitive dependency poisoning, composition trust-transfer, DNS/error side-channels, model artifact theft, repo-config hook execution (`.claude/settings.json`), MCP tool poisoning, marketplace / IDE packs (install flows, marketplace listings, and packs that impersonate a platform's own native skills), wallet exhaustion.
- **Format-spec noncompliance (4):** unsafe-YAML frontmatter gadgets, frontmatter-free bundles, symlink escapes out of the bundle, nested skill-in-skill recursion. Nothing downstream enforces agentskills.io.
- **Benign FP-bait (13):** look suspicious on purpose; measure false-positive rates.

Every entry has a `skill/` folder (the only thing you point a scanner at) and, kept outside it, an `expected.yaml` answer key: the verdict, a plain-English reason, and category mappings (OWASP AST10, SkillSpector codes, our own V1–V15 evasion families). Each also carries a `GOAT-CANARY-*` token so a leaked fixture can be traced back here.

## Scope & Exclusions

SkillsGoat covers malicious and vulnerable skill *content*: what ships inside a bundle, and what happens when an agent loads it. These adjacent threats are out of scope:

| Excluded | Why |
|---|---|
| **Platform vulnerabilities** (localhost WebSocket hijacking, checkout-time RCE from harness bugs) | Bugs in the agent platform itself, not skill content. Report those upstream. |
| **Prompt-only exploitation** (adversarial prompts weaponizing *already-installed benign* skills — SkillAttack-style) | Nothing malicious ships in any bundle. |
| **Registry & lifecycle attacks on installed fleets** (rug-pulls, deleted-account dependency takeover, fleet update drift) | Registry/ops problem — the *package version* changes. In scope, by contrast: a shipped bundle whose own external URL serves different content over time (`300-time-delayed-c2`) — the bundle never changes, only the clock. |
| **Model-layer attacks** (base-model jailbreaks, training-data poisoning) | Independent of the skills layer. See OWASP LLM Top 10. |

In scope: injection, obfuscation, packing, persistence, memory/soul poisoning, supply-chain chaining, marketplace-hosted packs (e.g. Vercel skills.sh, ClawHub, Cursor plugins) and third-party trees that impersonate a platform's own native skills, provenance-and-time evasion (reconstruction-from-reference, out-of-band distribution, time-delayed external staging), and compound cross-skill attacks under `pasture/compound-chain/`.

Evaluate UI-only scanners with browser automation against that plugin unit, not a pasted `SKILL.md`. See [evaluations/ui/PROTOCOL.md](evaluations/ui/PROTOCOL.md).

## Compound chains

Single-skill fixtures test one weakness at a time. Real compromises chain across **state channels** (agent memory, context window, repo/env state, shared tool layer) and **trust edges** (skill→skill, dep→skill, external→skill, session→future). Under `pasture/compound-chain/`, a **node** is one skill in the bundle and the **graph** is how those skills compose. Nodes are written to look ordinary alone; ground truth (`chain.yaml`) is graph-level. Contexts: developer endpoint, long-lived server agent, CI/CD runner, hosted sandbox. See [docs/CHAIN_SCHEMA.md](docs/CHAIN_SCHEMA.md).

## Install and test (research clone)

**Sandbox first** — a local OS/container/VM isolation, or a throwaway
remote machine. Canonical commands and disclaimers:
[.agents/install-block.md](.agents/install-block.md),
[docs/SAFETY.md](docs/SAFETY.md). This repo does not name a sandbox vendor.

```bash
git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git
cd skillsgoat && ./setup
.venv/bin/goat lint
.venv/bin/goat selftest
.venv/bin/python -m pytest -q
.venv/bin/goat scan --blind --assert-only
```

`./setup` creates a venv, installs the package (`[dev]` only — never the
`[scanners]` extra), and stops. It does **not**
link fixtures into `~/.claude/skills`. To load the goat into agent dirs:
`./setup --goat` (type `GOAT`, or `--confirm-goat` in CI). Links go to
`$SKILLSGOAT_SANDBOX` or `./.sandbox-home`, not your real `$HOME`, unless
you pass `--real-home`. Do that on a
throwaway remote machine, or run the agent with
`HOME=$SKILLSGOAT_SANDBOX TMPDIR=$SKILLSGOAT_SANDBOX/tmp`.

Plugin manifests (`.claude-plugin/`) stay in the tree for discovery
testing. Do not treat `claude plugins install` or `npx skills add` as
the default path; both can list or load the goat without the typed
confirm. See [docs/SAFETY.md](docs/SAFETY.md).

## Layout

```
taxonomy.yaml               fixed category registry
setup                       venv + editable install (use --goat to link fixtures)
src/goat/                   packaged CLI (`pip install -e .` → `goat`)
src/goat/scanners/          unused adapter sketches; `goat scan` uses SCANNER_CONFIGS
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
                            — only `"blind": true` matrices are publication-grade
evaluations/ui/             browser/computer-use protocol for UI-only vendors
```

## Scoring (blind)

`goat scan` defaults to `--blind` and static-only. At scan time it copies each
fixture into a hashed directory, replaces `GOAT-CANARY-*` / `GOAT-CHAIN-*` with
one neutral UUID, and asserts `expected.yaml` / `chain.yaml` are not in the
scanner's input. `goat lint` still requires the canary in source. Use
`--no-blind` only to debug the live tree; do not publish those numbers. Pass
`--llm` only when you intend to upload fixture text to the scanner's inference
provider. CI runs `goat scan --blind --assert-only`.

## Tiers

| Tier | Meaning |
|---|---|
| 000 | In plain sight. Every scanner must catch these. |
| 100 | One hop away (another file or step) |
| 200 | Built to slip past pattern matching |
| 300 | Multi-stage, judge-targeting, or binary-artifact based |

## Credits & lineage

This goat is original. The shape is WebGoat / DVWA / [AI Goat](https://github.com/orcasecurity-research/AIGoat). Four atomics derive Trail of Bits [overtly-malicious-skills](https://github.com/trailofbits/overtly-malicious-skills) primitives (rewritten, not copied). Compound chains cite SkillProbe ([arXiv:2603.21019](https://arxiv.org/abs/2603.21019)) and *Agent Skills in the Wild* ([arXiv:2601.10338](https://arxiv.org/abs/2601.10338)).

SkillSpector, Cisco skill-scanner, and Snyk Agent Scan are evaluation targets, not sources. Full lineage: [NOTICE.md](NOTICE.md). Cite this dataset with [CITATION.cff](CITATION.cff).

## Responsible use

This is defensive research tooling: ground truth for scanner evaluation and analyst training. Test only in a sandbox. Scanner results are published as a benchmark — reproducible, version-pinned, and dated, with a standing right of reply for vendors ([SECURITY.md](SECURITY.md)). See [docs/SAFETY.md](docs/SAFETY.md).
