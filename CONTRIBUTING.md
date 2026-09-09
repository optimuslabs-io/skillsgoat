# Contributing

SkillsGoat is a research corpus. Run it in a sandbox ([nono](https://nono.sh)
or [Daytona](https://www.daytona.io); see [docs/SAFETY.md](docs/SAFETY.md)).
Default install is clone + `goat lint` / `goat scan`. Do not add live hosts,
real credentials, or functioning malware.

## Add a fixture

```bash
./setup
.venv/bin/python goat.py new --category obfuscation-encoding --tier 200 --name "my-technique"
# edit pasture/<category>/200-my-technique/{expected.yaml,skill/SKILL.md}
.venv/bin/python goat.py lint
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

Run `goat lint` and `goat selftest` before opening a PR. If you add or
re-run a scanner matrix, update `evaluations/README.md` with date,
scanner version, and corpus snapshot in the same PR.
