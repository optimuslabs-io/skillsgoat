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

## What only dynamic detonation catches

V5 packing, V6 deferred, V7 staging, V8 silence, and V9 dormancy are
*structurally* invisible to static analysis (Cloak-and-Detonate measured ≥90%
universal bypass). The corpus is the static floor; sandboxed detonation with
taint tracking (SkillDetonate-style) is the required complement.

## The format layer: spec-noncompliance fixtures

agentskills.io defines shape; nothing downstream enforces it. Entries under
`format-spec-noncompliance/` prove ingestion is content-driven, not
schema-gated: unsafe-YAML deserialization gadgets in frontmatter,
frontmatter-free instruction files that agents still obey, symlinks escaping
the bundle into ~/.ssh, and full nested skills riding inside resources/.
Parser differentials here are invisible to content scanners by construction.
Run `goat.py inventory` for the live file-type census (15+ types incl.
compiled bytecode, ZIP archives, XOR blobs, image metadata carriers).

## Plugin install unit (not an evasion family)

Marketplace and IDE packs are the common distribution shape. Their READMEs
follow the popular-pack install story: a paste-to-agent prompt (gstack),
Claude `claude plugins install` / `/plugin install` vs
`npx skills@latest add` then `/setup-*` (mattpocock), and
`npx <pack> install` writing `.claude/skills`, `.cursor/skills`,
`.codex/skills`, `.github/skills`, `.grok/skills` (impeccable). Trees also
use Vercel discovery dirs (`skills/.curated`, `.experimental`, `.system`),
ClawHub/OpenClaw listings, and plugin manifests. Harm sits in nested files
behind a clean pack card. Fixtures: `200-vibe-coded-plugin`,
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

14 multi-skill chains where every node is individually clean; ground truth is
graph-level (`chain.yaml`). SkillSpector v2.9.6, static-only:

| Metric | Result |
|---|---|
| Nodes hard-flagged | **0 / 28** |
| Nodes weak-flagged (below block) | 7 / 28 |
| Chains fully bypassed (all nodes clean AND graph-level zero detection) | **7 / 14 — 50% structural blindness** |
| Composites caught at block threshold | 1 / 14 (c14 sandbox-shim — shim/LD_PRELOAD rules added post-ToB) |
| Composites weak-flagged | 6 / 14 |

Chains fully invisible: c1 memory-handoff · c2 context-bleed · c4 supply-arms-memory ·
c5 repoconfig-rootkit · c6 mcp-cross-skill · c11 soul-c2 · c12 inference-hijack.
Full per-node/composite JSON: `evaluations/skillspector/chains.json`. Narrative catalog:
[CHAINS.md](CHAINS.md).


## Scanner comparison — static-only (metric v2 — strict)

Last run: SkillSpector **2026-09-03**, Cisco **2026-08-25**. These are not a same-day bake-off. Full ledger: [evaluations/README.md](../evaluations/README.md).

Structural blindness v2 = **zero hard-blocks anywhere in a chain** (nodes or
composite). Sub-threshold WEAK findings no longer rescue a score — v1 counted
them as visibility, which let Cisco's keyword noise (weak-flagged on all ten
benign controls too) masquerade as coverage. Correction first published with
this table.

| Metric | SkillSpector v2.9.6 | Cisco skill-scanner (static) |
|---|---|---|
| Atomic: caught at block threshold | 8 / 55 | 5 / 55 |
| Atomic: zero-detection bypasses | 13 | **0** |
| Calibration misses (silent) | 2 | 0 |
| Benign twins FALSE-POSITIVE / FP-WEAK | 0 / 6 | 2 / 8 |
| Chain nodes hard-flagged | 0 / 28 | **0 / 28** |
| Composites caught | 1 / 14 | **0 / 14** |
| **Structural blindness (v2, strict)** | **13 / 14** | **14 / 14** |

Fully invisible to both tools: memory handoff · context bleed · supply-arms-memory ·
repoconfig rootkit · MCP cross-skill poisoning · Soul-as-C2 · inference hijack.
One composite caught once (c14 sandbox-shim — LD_PRELOAD rules added post-ToB).

Raw evidence: `evaluations/{skillspector,cisco}/` (per-entry JSON + matrices).
Composite mode is predictive: no whole-graph skill scanner ships today.
