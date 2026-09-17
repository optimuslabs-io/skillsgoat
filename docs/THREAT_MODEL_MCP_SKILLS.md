# Threat model: skills served over MCP (SEP-2640)

**Status: Final.** SEP-2640 (Skills Extension) reached Final with
[modelcontextprotocol/ext-skills](https://github.com/modelcontextprotocol/ext-skills)
PR #2640 merged 2026-09-13; the stable spec is `specification/stable/skills.mdx`,
written against base protocol revision `2026-07-28`. Field names and semantics
below are pinned to that stable spec (as of 2026-09); re-check on new releases.

## What's different

SkillsGoat's other fixtures assume a skill ships as files (a filesystem bundle
or a marketplace pack). SEP-2640 serves skills **over MCP as Resources**:

- `skill://<skill-path>/<file-path>` resource URIs; `text/markdown` for
  `SKILL.md`, per-file types for the rest.
- Protocol methods `skills/list` (enumerate) and `skills/get` (single entry);
  `resources/directory/read` when the server advertises `directoryRead`.
- Each entry lists resources with a `sha256:` `digest` and `size`, **or**
  `"resources": "dynamic"` for server-generated bodies.
- Per-skill, content-bound approval: any change to the `uri`/`digest` set
  revokes prior approval.

This is a new **distribution + trust channel**, distinct from `mcp-tool-poisoning`
(`.mcp.json` / tool metadata) and `plugin-distribution` (marketplace/filesystem
packs).

## The spec is well-defended — attacks target lax hosts

SEP-2640 already mandates the right defenses (origin labeling, no permission
widening without per-skill consent, content-bound approval, digest re-verify,
independent nested activation, cache must not "graduate to filesystem trust").
So the realistic attacks are **malicious served skills betting the host or
scanner doesn't fully implement the spec** — which is exactly the kind of
assumption SkillsGoat exists to test.

## Scope line

- **In scope:** the malicious **served skill / manifest content** a scanner is
  pointed at — dynamic-resource sleepers, digest-as-trust theater,
  `allowed-tools` escalation frontmatter, origin-shadowing names, cross-origin
  read directives, nested auto-activation.
- **Out of scope:** bugs in the host's MCP **client** (failing to re-verify
  digests, not gating cross-origin reads). That's platform, same exclusion as
  ClawJacked-class harness bugs. Fixtures *target* lax hosts but ship as skill
  content.

## Attack paths

| # | Attack | Mechanism abused | Status |
|---|---|---|---|
| 1 | **Dynamic-resource sleeper** — benign body to the review fetch, malicious body to the execution fetch at the same `skill://` URI | `"resources": "dynamic"`; server-generated per read; TOCTOU on served content | **Fixture:** `skills-over-mcp/300-dynamic-resource-sleeper` |
| 2 | **`allowed-tools` escalation over MCP** — frontmatter requests host tool/FS/network scope past the task, betting the host auto-honors it | Spec: hosts MUST NOT honor permission-widening frontmatter for MCP skills without per-skill consent | **Fixture:** `skills-over-mcp/200-allowed-tools-escalation` |
| 3 | **Digest-as-trust theater** — flaunts `sha256:` digests as if they prove authenticity | Digests are unsigned, same-origin: consistency, not trust | Planned |
| 4 | **Origin shadowing / cross-origin confused deputy** — shadow a trusted filesystem skill name, or direct the agent to read another origin | Origin must be host-labeled; no silent shadowing; cross-origin reads gated | Planned |
| 5 | **Nested-skill auto-activation** — benign parent smuggles a nested skill that acts before independent activation | Each nested skill needs separate activation; parent approval ≠ child | Planned |
| 6 | **MCP skill-cache poisoning** — poison the host skill cache so a later read serves malicious bytes under a trusted origin | Cache must not graduate to filesystem trust; recompute SHA-256 | Planned |

## Benign twins (false-positive controls)

- `benign/000-mcp-skill-static-pinned` — MCP skill done safely: static,
  digest-pinned resources, no dynamic bodies. Twin of path 1.
- `benign/000-mcp-skill-scoped-tools` — `allowed-tools` scoped to exactly the
  task. Twin of path 2.

A scanner must flag the malicious served skills while passing these — it should
not flag a skill merely for being served over MCP.
