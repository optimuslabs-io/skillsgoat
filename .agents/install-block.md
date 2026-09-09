# The canonical install block

README and docs/USAGE.md must say **this**. Run SkillsGoat — including
`goat lint`, `goat selftest`, `pytest`, and scanner evals — in a **local
or cloud sandbox**. Default is clone + scan. `./setup --goat` loads
fixtures into the agent skill path on purpose. Endpoints are inert
(`*.example` / RFC 5737). Local side effects are **not** inert if an
agent or a human runs a pasture script.

Do not list this repo on skills.sh. Do not `npx skills add` it.
Plugin manifests stay in the tree for discovery testing; they are not
the documented 30-second path.

## Sandbox first (required for clone, test, and --goat)

Do not clone this onto a machine that holds production secrets. Do not
run tests or `./setup --goat` on the host agent profile you use for
real work.

**Local sandbox:** an OS-level or container/VM isolation on the machine
you already have, such that the test process and any agent cannot read
`~/.ssh`, `~/.aws`, or other production secrets.

**Cloud / remote sandbox:** a throwaway machine or workspace that does
not hold production secrets. Prefer this for `--goat` and any live-agent
test: the whole home should be disposable.

This project does **not** endorse a sandbox vendor. Pick a tool you
already trust, or wait until we have tested a product and (if ever)
announced a partnership. `docker compose` in this repo is a convenience
wrapper, **not** a security boundary (it bind-mounts the working tree).
GitHub Actions CI is an ephemeral runner; reproducing tests on a laptop
still needs a sandbox.

Disclaimers: [docs/SAFETY.md](../docs/SAFETY.md).

## Research clone + test (default)

Do this **inside** the sandbox you chose:

```bash
git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git
cd skillsgoat && ./setup
.venv/bin/goat lint
.venv/bin/goat selftest
.venv/bin/python -m pytest -q
# optional scanner eval (may upload skill text to the scanner/LLM):
.venv/bin/goat scan --scanners skillspector --no-llm   # --blind is the default
.venv/bin/goat scan --blind --assert-only              # leak gate; no scanners
```

Point scanners at `pasture/<category>/<id>/skill/` (or the whole pack
under plugin-distribution entries). See [docs/USAGE.md](../docs/USAGE.md).

## Goat load (optional)

Links every pasture `skill/` into detected agent dirs **under
`$SKILLSGOAT_SANDBOX` or `./.sandbox-home`**, not your real `$HOME`, unless
you pass `--real-home`. Type `GOAT` when prompted, or pass `--confirm-goat`
in CI. Prefer a throwaway remote machine. Detonate the agent with
`HOME=$SKILLSGOAT_SANDBOX TMPDIR=$SKILLSGOAT_SANDBOX/tmp` so scripts that
append to `~/.zshrc` cannot dirty your real shell config.

```bash
export SKILLSGOAT_SANDBOX="$PWD/.sandbox-home"
./setup --goat
# or:  ./setup --goat --confirm-goat --host claude,cursor
# team / project links:
./setup --goat --team --confirm-goat
```

Then start the agent inside the sandbox, not on the bare host.

Uninstall: `./setup --uninstall`.

## Plugin / marketplace (not advertised)

`.claude-plugin/` is in the tree. `claude plugins install` bypasses
`./setup` and can still load `skills/` if that index exists. Refresh it
only with `./setup --index-only`. Do not document marketplace add or
`npx skills add` as the default install.
