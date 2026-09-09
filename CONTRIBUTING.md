# Contributing

SkillsGoat is a research corpus. **Clone and test in a local or cloud
sandbox** you already trust. See [docs/SAFETY.md](docs/SAFETY.md) for
disclaimers: inert C2 does not mean it is safe to run pasture scripts or
a live agent on a machine with secrets. This repo does not endorse a
sandbox vendor.

Default install is clone + `goat lint` / `goat selftest` / `pytest`. Do
not add live hosts, real credentials, or functioning malware.

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
- Unique `GOAT-CANARY-*` / `GOAT-CHAIN-*` embedded in skill files
- Categories come from `taxonomy.yaml`
- URLs, including those hidden in Unicode Tags / ZWSP / variation
  selectors, must be `*.example` / RFC 2606 / RFC 5737 / localhost
- No `/Users/` or `/home/` paths in `pasture/` or `evaluations/`
- Symlinks must be repo-relative; no `$HOME` / `.ssh` / `.aws` targets
- `utils.cpython-314.pyc` exists (regenerate with `python3 tools/gen_binaries.py`;
  do not `make clean` before committing it)

## Dual-use

Payloads stay inert. Hidden unicode must still decode to an allowed
URL. Do not copy live C2, wallets, or ransomware. Cite techniques in
`NOTICE.md`, not copied exploits.

## Pull requests

Run `goat lint`, `goat selftest`, and `pytest` in a sandbox before opening
a PR. If you add or re-run a scanner matrix, update `evaluations/README.md`
with date, scanner version, and corpus snapshot in the same PR. Scanner
evals may upload skill text; do that from a sandbox too.
