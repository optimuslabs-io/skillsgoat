# Safety Policy

## Inertness guarantees

1. **Endpoints.** Every URL resolves to a reserved documentation domain
   (`*.example`, RFC 2606) or TEST-NET address (RFC 5737: 192.0.2.0/24,
   198.51.100.0/24, 203.0.113.0/24). Nothing is reachable.
2. **Payloads.** Bundled archives (`helper.zip`, `templates.docx`,
   `skillpack.dat`) contain inert markers or text — never functioning malware.
   The poisoned `.pyc` beacons to an unroutable example domain only.
3. **Credentials.** Any referenced secret files are referenced, never embedded;
   exfiltrated content in simulations is fake or absent.

## Ground-truth integrity

- Answer keys (`expected.yaml`), `.goat-meta` notes, and `aibom.yaml` live
  OUTSIDE each `skill/` directory. Point scanners at `skill/` only.
- Every malicious entry embeds a unique canary token
  (`GOAT-CANARY-<id>`) inside its files. If these strings ever surface in a
  public registry, dataset, or scanner training corpus, that leak is traceable
  back to this repo and to any contaminated evaluation set.

## What a CLEAN scan does and does not certify

A scanner returning SAFE on these fixtures certifies detection of *this
corpus's known patterns only*. See README "Scope & Exclusions": platform
CVEs, prompt-only exploitation of installed skills, registry lifecycle
attacks, and model-layer attacks are out of scope by construction.

## Handling rules

- Do NOT install any entry into a live agent or agent-with-internet session.
- Run scanners as subprocesses with network egress you understand (SkillSpector
  queries OSV.dev; LLM stages send file contents to your configured provider).
- Keep this repository out of default skill-search paths of local agents.

## Disclosure

If evaluation shows a maintained scanner misses entries here, notify the
vendor privately first; withhold mechanism-level detail until they ship a fix
or 90 days pass. Evaluation reports should note vendor-contact status.

## Registry scanner false-positives on this repo

Dependency scanners (Dependabot etc.) will flag pinned vulnerable versions
inside fixture manifests (e.g., the transitive-poisoning entry's
requirements.txt). These are intentional corpus content, not dependencies.
Alerts are dismissed as `not_used` with an explanatory comment.
