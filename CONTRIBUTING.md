# Contributing

SkillsGoat is a research corpus. **Clone and test in a local or cloud
sandbox** you already trust. See [docs/SAFETY.md](docs/SAFETY.md) for
disclaimers: inert C2 does not mean it is safe to run pasture scripts or
a live agent on a machine with secrets. This repo does not endorse a
sandbox vendor.

Default install is clone + `goat lint` / `goat selftest` / `pytest`. Do
not add live hosts, real credentials, or functioning malware. Conduct:
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Add a fixture

```bash
./setup
.venv/bin/goat new --category obfuscation-encoding --tier 200 --name "my-technique"
# edit pasture/<category>/200-my-technique/{expected.yaml,skill/SKILL.md}
.venv/bin/goat lint
```

Chains live under `pasture/compound-chain/<id>/` with `chain.yaml` and
`nodes/<name>/skill/`. Every node must be defensibly CLEAN alone.

## Rules `goat lint` enforces

- Answer keys (`expected.yaml`, `chain.yaml`) stay **outside** `skill/`
- Unique `GOAT-CANARY-*` / `GOAT-CHAIN-*` embedded in skill files as
  **plaintext** (`goat lint` checks source; `goat scan --blind` strips them
  at scan time). A canary that exists only inside a zip/pyc would survive
  blind staging — set `canary_packed: true` on `expected.yaml` / `chain.yaml`
  only if that is intentional.
- Categories come from `taxonomy.yaml`
- URLs, including those hidden in Unicode Tags / ZWSP / variation
  selectors, must be `*.example` / RFC 2606 / RFC 5737 / localhost
- No `/Users/` or `/home/` paths in `pasture/` or `evaluations/`
- Symlinks must be repo-relative; no `$HOME` / `.ssh` / `.aws` targets
- `utils.cpython-314.pyc` exists (regenerate with `python3 tools/gen_binaries.py`;
  do not `make clean` before committing it). The `cpython-314` tag is
  intentional: the file is an inert artifact, not an importable module on
  the 3.11/3.12 harness runtime.

## Dual-use

Payloads stay inert. Hidden unicode must still decode to an allowed
URL. Do not copy live C2, wallets, or ransomware. Cite techniques in
`NOTICE.md`, not copied exploits.

## Pull requests

Run `goat lint`, `goat selftest`, `goat scan --blind --assert-only`, and
`pytest` in a sandbox before opening a PR. If you add or re-run a scanner
matrix, update `evaluations/README.md` with date, scanner version, corpus
snapshot, and `"blind": true` in the same PR. Scanner evals may upload
skill text; do that from a sandbox too. Do not cite `--no-blind` scores.
