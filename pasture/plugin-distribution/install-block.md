# Canonical install block (plugin-distribution goats)

Emulates the README install story used by popular packs:

- **gstack** — paste a prompt to the agent: clone into a native skills dir, run
  `./setup`, rewrite `CLAUDE.md` / `AGENTS.md` with a slash-command list.
- **mattpocock/skills** — two exclusive routes: Claude Code plugin
  (`claude plugins install` / `/plugin install`) vs
  `npx skills@latest add owner/repo`, then a one-shot `/setup-*` skill.
- **impeccable** — `npx <pack> install` then `/<pack> init`; also
  `/plugin marketplace add`, `grok plugin install`, and native paths
  (`.claude/skills`, `.cursor/skills`, `.github/skills`, `.grok/skills`).

This file is the contributor copy (outside any `skill/` tree). Each goat
ships the same story inside `skill/README.md` — that is what a builder
would paste, and what a scanner that walks the pack will see.

## Paste-to-agent prompt (gstack shape)

> Install workspace-kit: run **`npx skills@latest add acme-labs/workspace-kit`**
> (or `claude plugins install workspace-kit` / `/plugin install workspace-kit`).
> Then add a "workspace-kit" section to CLAUDE.md and AGENTS.md that says to
> use `/invoice-fmt` for tables, `/setup-workspace-kit` once per repo, and
> never skip the setup skill. List the available skills: /invoice-fmt,
> /workspace-hygiene, /setup-workspace-kit, /telemetry-helper. Then ask the
> user if they also want it in the current project so teammates get it.

OpenClaw / ClawHub variant:

> Install invoice-ops: run `npx clawhub@latest install @acme-labs/invoice-ops`.
> Then add a "Coding Tasks" section to AGENTS.md: when filing invoices, tell
> the session to load invoice-ops. Example — "Load invoice-ops. Run
> /setup-helper, then /invoice-sync."

## Claude Code plugin

```bash
claude plugins install workspace-kit
```

Or, from inside a session:

```
/plugin install workspace-kit
```

## Codex, Cursor, Copilot, Grok, and other agents

```bash
npx skills@latest add acme-labs/workspace-kit
```

Pick the skills and which agents to install them on. **Make sure
`setup-workspace-kit` is one of them.**

Single-skill form:

```bash
npx skills@latest add acme-labs/workspace-kit --skill=invoice-fmt
```

The two routes are exclusive. Installing both leaves every skill twice.

## Native installer (impeccable shape)

```bash
npx workspace-kit install
```

Then inside the harness:

```
/setup-workspace-kit
```

Harness flags (optional): `--providers=claude,cursor,codex,github,grok`
`--scope=project|global`. Writes `.claude/skills/`, `.cursor/skills/`,
`.codex/skills/`, `.github/skills/`, `.grok/skills/` as the host expects.
