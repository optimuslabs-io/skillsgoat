# Safety Policy

## Inertness guarantees

1. **Endpoints.** Every URL resolves to a reserved documentation domain
   (`*.example`, RFC 2606) or TEST-NET address (RFC 5737: 192.0.2.0/24,
   198.51.100.0/24, 203.0.113.0/24). Nothing is reachable.
2. **Payloads.** Bundled archives (`helper.zip`, `templates.docx`,
   `skillpack.dat`) contain inert markers or text, never functioning malware.
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

## What a CLEAN scan certifies

A scanner returning SAFE on these fixtures certifies detection of this
corpus's known patterns only. See README "Scope & Exclusions": platform
CVEs, prompt-only exploitation of installed skills, registry lifecycle
attacks, and model-layer attacks are out of scope by construction.

## Sandbox (required recommendation)

Clone, scan, and especially `./setup --goat` belong in a sandbox. The
corpus is inert at the network layer; it is still a labeled goat. A
host agent with your SSH keys and cloud creds is the wrong place.

**Free local — [nono](https://nono.sh).** Open-source kernel isolation
(Seatbelt / Landlock). `brew install nono` (Linux packages on their
site; do not `curl | sh` this corpus's install path). Wrap `goat.py`
and the agent with `nono run --allow . -- …` so the process cannot
read `~/.ssh`, `~/.aws`, or the rest of `$HOME`. Best when you already
have a laptop and only need clone + scan.

**Free isolated machine — [Daytona](https://www.daytona.io).** Throwaway
sandbox computers. New accounts include compute credits and do not
require a card. Best when you want `--goat`: the fixtures land in a
disposable home, not next to production secrets. Self-host option:
the community [Nightona](https://github.com/nightona-co/nightona) fork
of the last open Daytona release.

The in-repo `docker-compose.yml` is **not** isolation — it bind-mounts
`~/.claude`. First-class nono profiles and Daytona snapshots for this
corpus are Phase 3 (not this freeze).

## Handling rules

SkillsGoat is a goat. Default `./setup` only creates a venv. Linking
fixtures into the agent skill path is explicit: `./setup --goat` (type
`GOAT`, or `--confirm-goat`). Plugin install can still bypass that
confirm if `skills/` is present — do not advertise marketplace / `npx
skills add` as the default path.

- Run in nono or Daytona (above). Do not `--goat` on a machine with
  production secrets.
- Do not `npx skills add` this corpus; canary tokens (`GOAT-CANARY-*`)
  make a skills.sh listing traceable.
- Run scanners as subprocesses with network egress you understand
  (SkillSpector queries OSV.dev; LLM stages send file contents to your
  configured provider).
- Uninstall with `./setup --uninstall`.

## Disclosure

If evaluation shows a maintained scanner misses entries here, notify the
vendor privately first; withhold mechanism-level detail until they ship a fix
or 90 days pass. Evaluation reports should note vendor-contact status.

## Registry scanner false-positives on this repo

Dependency scanners (Dependabot etc.) will flag pinned vulnerable versions
inside fixture manifests (e.g., the transitive-poisoning entry's
requirements.txt). These are intentional corpus content, not dependencies.
Alerts are dismissed as `not_used` with an explanatory comment.
