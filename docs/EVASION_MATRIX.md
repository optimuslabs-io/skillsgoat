# Evasion Matrix — scanner assumptions → techniques

Each V-family attacks a specific architectural assumption shared by current
skill scanners (SkillSpector, Cisco skill-scanner, registry guards). Entries
demonstrating each family are listed. "ToB" = derived from Trail of Bits'
June 2026 demonstrated bypasses.

| Family | Scanner assumption defeated | Mechanism | Entries |
|---|---|---|---|
| V1 Obfuscation/encoding | Contiguous suspicious tokens in text | Homoglyphs, zero-width, RTL overrides, charcode exec, shell splicing | 200-homoglyph-imports, 200-zero-width-directives, 200-rtl-override-labels, 200-shell-splice-concat, 300-charcode-exec |
| V2 Dispersion | Single-file analysis; whitelisted paths/dirs | Split-across-files, dotfile sourcing, .git/ hiding, extension disguise | 200-split-across-files, 200-helper-sourced-payload, 200-gitignore-hide, 200-extension-disguise |
| V3 Truncation/padding | Read caps + attention budgets | Newline canyon (100k lines), below-fold whitespace | 300-newline-canyon (ToB), 200-whitespace-below-fold |
| V4 Judge manipulation | LLM judges read faithfully & trust narrative | Cover links judges won't fetch, reviewer-directed self-injection, corporate-narrative armor, plausibility comments | 300-cover-link-offload, 300-judge-self-injection, 300-corporate-narrative (ToB), 200-plausibility-comments |
| V5 Hidden artifacts/packing | Text-only analysis; opaque binaries skipped | Bytecode divergence (.pyc≠.py), archive indirection (.docx zip), password ZIP, XOR SFS pack, image-metadata carrier | 300-bytecode-poisoning (ToB), 300-archive-indirection-docx (ToB), 300-password-zip-drop, 300-sfs-xor-pack, 200-image-metadata-payload |
| V6 Deferred resolution | Review-time = run-time content | PEP 723 runtime deps, lockfile divergence | 200-pep723-deferred-dep, 200-lockfile-divergence |
| V7 External staging | Shipped files = whole behavior | Runtime instruction fetch, remote config switches | 200-runtime-instruction-fetch, 100-config-url-fetch |
| V8 Silent operators | Logs/interaction as audit signal | Weaponized Definition-of-Done push, confirmation bans | 300-definition-of-done-push, 200-minimal-interaction-allowlist |
| V9 Dormant gates | Static context = runtime context | Codeword sleepers, env/host-gated arming | 200-codeword-activation, 200-env-gated-behavior |
| V10 Shadow features | Description ≈ behavior | Understated manifests, undeclared telemetry | 100-description-understate, 100-overbroad-permissions |
| V11 Reputation laundering | Popularity ≈ trust | Fabricated social proof fixtures | 100-fake-social-proof |
| V12 Memory poisoning | Skill scope = session scope | MEMORY.md standing rules | 100-memory-file-write |
| V13 Self-mutation | Point-in-time review suffices | Self-overwriting update path | 300-self-rewrite-update |
| V14 Reconstruction-from-reference | The installed bundle is the artifact to scan | Agent is told to rebuild a skill from an external repo/URL; payload is hand-written at run time, never installed | 200-rebuild-from-link, c36-reference-reconstruction |
| V15 Out-of-band distribution | Skills are scanned at the marketplace / install flow | Raw `git clone` or manual folder upload routes around every scanned channel; anti-marketplace steering is the tell | 200-raw-clone-sideload, 200-manual-upload-bundle |

## Provenance & time: the scanned artifact is not the executed behavior

Most fixtures assume the malicious thing ships in the bundle you scan. Three
families break that on the **provenance** and **time** axes:

- **V14 reconstruction-from-reference** — nothing installs; the agent rebuilds
  the payload from an external reference, so there is no artifact to scan on
  either side (`200-rebuild-from-link`, `c36-reference-reconstruction`).
- **V15 out-of-band distribution** — the bundle enters by raw clone or manual
  upload, so no registry or install-flow scanner ever sees it
  (`200-raw-clone-sideload`, `200-manual-upload-bundle`).
- **Temporal external staging (V7 × V9)** — an external source is innocuous at
  review and flips after a hardcoded date; a TOCTOU on fetched content
  (`300-time-delayed-c2`, `c37-time-gated-updater`). Distinct from a registry
  rug-pull: the bundle never changes, only the clock and the served body.

## What only dynamic detonation catches

V5 packing, V6 deferred, V7 staging, V8 silence, and V9 dormancy are
*structurally* invisible to static analysis (Cloak-and-Detonate measured ≥90%
universal bypass). The pasture is the static floor; sandboxed detonation with
taint tracking (SkillDetonate-style) is the required complement.

## The format layer: spec-noncompliance fixtures

agentskills.io defines shape; nothing downstream enforces it. Entries under
`format-spec-noncompliance/` prove ingestion is content-driven, not
schema-gated: unsafe-YAML deserialization gadgets in frontmatter,
frontmatter-free instruction files that agents still obey, symlinks escaping
the bundle into ~/.ssh, and full nested skills riding inside resources/.
Parser differentials here are invisible to content scanners by construction.
Run `goat inventory` for the live file-type census (15+ types incl.
compiled bytecode, ZIP archives, XOR blobs, image metadata carriers).

## Plugin install unit (not an evasion family)

Marketplace and IDE packs are the common distribution shape. Their READMEs
follow the popular-pack install story: a paste-to-agent prompt, a
`plugins install` / registry-`add` step, or an `npx <pack> install` that
writes into a platform's skill directories (`.claude/skills`,
`.cursor/skills`, `.codex/skills`, `.github/skills`, `.grok/skills`). Trees
also use marketplace discovery dirs and plugin manifests. Harm sits in nested
files behind a clean pack card. Fixtures: `200-vibe-coded-plugin`,
`200-vercel-skills-sh-pack`, `200-clawhub-listing`,
`200-ide-native-impersonation`. Canonical wording:
[install-block.md](../pasture/plugin-distribution/install-block.md). UI scoring:
[evaluations/ui/PROTOCOL.md](../evaluations/ui/PROTOCOL.md).

## False-positive controls

The `benign/` set mirrors each dangerous shape (sudo use, ~/.ssh reads,
env loops, base64 blobs, hooks, registry mirrors, long/base64/CJK docs).
A useful scanner must catch malicious twins while passing benign ones —
keyword-only tools will fail both directions.


## Compound chains (pasture/compound-chain/) — measured results

**As of 2026-09-09** (SkillSpector v2.11.0). Scores go stale as scanners ship —
re-run `goat scan --blind` and cite the date from [evaluations/README.md](../evaluations/README.md).

> `goat scan --blind`, SkillSpector **v2.11.0**, `--no-llm`,
> **2026-09-09**. Provenance: `evaluations/skillspector/chains.json`
> (`blind: true`). Ledger: [evaluations/README.md](../evaluations/README.md).

35 multi-skill chains (72 nodes). Ground truth is graph-level (`chain.yaml`).

| Metric | Result |
|---|---|
| Nodes hard-flagged | **8 / 72** |
| Nodes weak-flagged (below block) | 23 / 72 |
| Nodes clean | 41 / 72 |
| Composites caught at block threshold | **8 / 35** (c14 sandbox-shim, c15, c17, c28, c29, c31, c34, c35) |
| Composites weak-flagged | 19 / 35 |
| Structural blindness v2 (zero hard-blocks anywhere) | **27 / 35 — 77%** |
| All-nodes-clean *and* graph-bypassed | 7 / 35 (c1, c2, c4, c6, c11, c12, c25) |

Full per-node/composite JSON: `evaluations/skillspector/chains.json`. Narrative catalog:
[CHAINS.md](CHAINS.md). Ledger: [evaluations/README.md](../evaluations/README.md).


## Scanner comparison — static-only (metric v2 — strict)

**As of 2026-09-09** (SkillSpector v2.11.0, Cisco skill-scanner 2.0.13). Scores
go stale as scanners ship — re-run `goat scan --blind` and cite the date from
[evaluations/README.md](../evaluations/README.md).

Same-day **`--blind`** bake-off: SkillSpector **2.11.0** and Cisco
skill-scanner **2.0.13**, both `--no-llm`, **2026-09-09**, 76 atomics
(66 malicious, 10 benign) and 35 chains. Each `matrix.json` /
`chains.json` records `blind: true`, `blind_salt`, and `canary_token`.
Full ledger: [evaluations/README.md](../evaluations/README.md).

Structural blindness v2 = **zero hard-blocks anywhere in a chain** (nodes or
composite). Sub-threshold WEAK findings do not rescue a score — v1 counted
them as visibility, which let Cisco's keyword noise (weak-flagged on all ten
benign controls too) masquerade as coverage.

| Metric | SkillSpector 2.11.0 | Cisco skill-scanner 2.0.13 |
|---|---|---|
| Atomic: caught at block threshold | **9 / 66** | **5 / 66** |
| Atomic: zero-detection bypasses | 20 | 1 |
| Atomic: ingest errors | 0 | 2 (`100-missing-required-fields`, `200-unsafe-yaml-frontmatter`) |
| Calibration misses (silent) | 2 | 0 |
| Benign twins FALSE-POSITIVE / FP-WEAK / CLEAN | 0 / 6 / 4 | 2 / 8 / 0 |
| Chain nodes hard-flagged | **8 / 72** | **7 / 72** |
| Composites caught | **8 / 35** | **7 / 35** |
| **Structural blindness (v2, strict)** | **27 / 35** | **28 / 35** |

Cisco strict recall in `matrix.json` is 5/64 because the two ingest errors are
excluded from the denominator. Benign FP-rate is 1.0 (every twin flagged).

22 of 35 chains are v2-blind to **both** tools. The original seven remain in
that set: memory handoff · context bleed · supply-arms-memory · repoconfig
rootkit · MCP cross-skill poisoning · Soul-as-C2 · inference hijack.

Raw evidence: `evaluations/{skillspector,cisco}/` (per-entry JSON + matrices).
Composite mode is predictive: no whole-graph skill scanner ships today.
