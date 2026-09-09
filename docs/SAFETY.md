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
4. **Scanner LLM.** `goat scan` is static-only unless you pass `--llm`.
   That flag uploads fixture text to the scanner's configured inference
   provider. Network C2 in the fixtures is still inert; the upload is not.
   `--no-llm` is accepted as a no-op so old scripts keep working.

## Ground-truth integrity

- Answer keys (`expected.yaml`), `.goat-meta` notes, and `aibom.yaml` live
  OUTSIDE each `skill/` directory. Point scanners at `skill/` only.
- Every malicious entry embeds a unique canary token
  (`GOAT-CANARY-<id>`) inside its files. If these strings ever surface in a
  public registry, dataset, or scanner training corpus, that leak is traceable
  back to this repo and to any contaminated evaluation set.
- **Published scores must use `goat scan --blind`.** That mode copies each
  fixture into a hashed directory, replaces canaries with one neutral UUID,
  and refuses to hand a scanner a tree that still contains `expected.yaml`.
  `goat lint` still checks the canary in source. `--no-blind` exists for
  debugging; those numbers are not citable. CI runs `goat scan --blind --assert-only`.

## What a CLEAN scan certifies

A scanner returning SAFE on these fixtures certifies detection of this
corpus's known patterns only. See README "Scope & Exclusions": platform
CVEs, prompt-only exploitation of installed skills, registry lifecycle
attacks, and model-layer attacks are out of scope by construction.

## Sandbox (required for clone, test, and --goat)

Run SkillsGoat in a **local or cloud sandbox**. That includes `goat lint`,
`goat selftest`, `pytest`, `goat scan`, and especially `./setup --goat`.
The corpus is a labeled goat. Network C2 is inert; **executing a pasture
script or loading fixtures into a live agent is not**.

**Local.** Isolate the test process (and any agent) from `$HOME` secrets
on the machine you already have: OS sandbox, container, or VM. The
process must not be able to read `~/.ssh`, `~/.aws`, or a daily-driver
agent profile.

**Detonation HOME.** Pasture scripts use `$HOME` / `~` (for example
`cat >> ~/.zshrc`). `./setup --goat` links into `$SKILLSGOAT_SANDBOX` if
set, otherwise `./.sandbox-home` — not your real profile. Pass
`--real-home` only if you intend to write the real account. A live
agent still uses the process HOME; detonate with:

```bash
export SKILLSGOAT_SANDBOX="$PWD/.sandbox-home"
mkdir -p "$SKILLSGOAT_SANDBOX/tmp"
./setup --goat
HOME="$SKILLSGOAT_SANDBOX" TMPDIR="$SKILLSGOAT_SANDBOX/tmp" <your-agent>
```

**Cloud / remote.** A throwaway machine or workspace with no production
secrets. Prefer this for live-agent tests (`--goat`): fixtures should
land in a disposable home.

This project does **not** name or endorse a sandbox vendor. Use a
boundary you already operate and trust. Named product recommendations
wait until we have tested that product and, if ever, announced a
partnership.

`docker compose` in this repo is **not** a security boundary (it
bind-mounts the working tree). GitHub Actions is an ephemeral runner; a
laptop reproduce still needs a sandbox.

```bash
.venv/bin/goat lint
.venv/bin/goat selftest
.venv/bin/python -m pytest -q
```

### Disclaimers

- **No safety warranty.** Inert URLs (`*.example`, RFC 5737) mean the
  corpus must not phone home. They do **not** mean it is safe to run skill
  scripts or a coding agent against this tree on a machine with secrets.
- **Harness tests vs agent tests.** `goat lint` / `selftest` / `pytest`
  do not execute pasture scripts. `goat scan` shells out to third-party
  scanners. The default is static-only (`--llm` off). SkillSpector still
  queries OSV.dev. `--llm` sends skill text to the configured inference
  provider. `./setup --goat` plus a live agent **will** follow fixture
  instructions (including decode-and-execute and reads of `~/.ssh` if the
  sandbox allows it).
- **Do not** clone, test, or `--goat` next to production SSH keys, cloud
  creds, or a daily-driver agent profile.
- Canary tokens (`GOAT-CANARY-*`) make a public skills.sh listing
  traceable. Do not `npx skills add` this corpus.

## Handling rules

SkillsGoat is a goat. Default `./setup` creates a venv and installs the
package. Linking fixtures into the agent skill path is explicit: `./setup --goat` (type
`GOAT`, or `--confirm-goat`). Plugin install can still bypass that
confirm if `skills/` is present — do not advertise marketplace / `npx
skills add` as the default path.

- Run tests and `--goat` in a local or cloud sandbox you already trust.
  Do not do either on a machine with production secrets.
- Do not `npx skills add` this corpus; canary tokens (`GOAT-CANARY-*`)
  make a skills.sh listing traceable.
- Run scanners as subprocesses with network egress you understand
  (SkillSpector queries OSV.dev even when static). `--llm` sends file
  contents to the scanner's configured inference provider; omit it.
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
