# The canonical install block

README and docs/USAGE.md must say **this**. Run SkillsGoat in a sandbox.
Default is clone + scan. `./setup --goat` loads fixtures into the agent
skill path on purpose. Endpoints are inert (`*.example` / RFC 5737).

Do not list this repo on skills.sh. Do not `npx skills add` it.
Plugin manifests stay in the tree for discovery testing; they are not
the documented 30-second path.

## Sandbox first (required recommendation)

Do not clone this onto a machine that holds production secrets, and do
not `./setup --goat` on the host agent profile you use for real work.

**Free local (default):** [nono](https://nono.sh) — open-source kernel
isolation (Seatbelt on macOS, Landlock on Linux). `brew install nono`.
Confine clone + scan + the agent to this repo; secrets under `~/.ssh`
and `~/.aws` stay out of reach.

**Free isolated machine:** [Daytona](https://www.daytona.io) — throwaway
sandbox computers (signup compute credits, no card). Use this when you
want `--goat` without sharing a filesystem with host secrets.

The in-repo `docker-compose.yml` is **not** isolation: it bind-mounts
`~/.claude`. Prefer nono or Daytona.

## Research clone (default)

```bash
brew install nono   # https://nono.sh — Linux: see their packages, not curl|bash
git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git
cd skillsgoat && ./setup
nono run --allow . -- .venv/bin/python goat.py lint
nono run --allow . -- .venv/bin/python goat.py scan --scanners skillspector --no-llm
```

Or clone inside a [Daytona](https://www.daytona.io) sandbox and run the
same `./setup` / `goat.py` commands there.

Point scanners at `pasture/<category>/<id>/skill/` (or the whole pack
under plugin-distribution entries). See [docs/USAGE.md](../docs/USAGE.md).

## Goat load (optional)

Links every pasture `skill/` into detected agent dirs. Type `GOAT` when
prompted, or pass `--confirm-goat` in CI. Prefer a Daytona sandbox (the
whole home is disposable). If you stay on a laptop, run the *agent*
under nono after linking — `./setup --goat` writes into `~/.claude` /
`~/.cursor` on the host.

```bash
./setup --goat
# or:  ./setup --goat --confirm-goat --host claude,cursor
# team / project links:
./setup --goat --team --confirm-goat
```

Then start the agent inside the sandbox, not on the bare host:

```bash
nono run --allow . -- claude
```

Uninstall: `./setup --uninstall`.

## Plugin / marketplace (not advertised)

`.claude-plugin/` is in the tree. `claude plugins install` bypasses
`./setup` and can still load `skills/` if that index exists. Refresh it
only with `./setup --index-only`. Do not document marketplace add or
`npx skills add` as the default install.
