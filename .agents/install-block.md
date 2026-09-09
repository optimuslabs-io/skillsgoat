# The canonical install block

One install story. `README.md` and `docs/USAGE.md` must say **this**.

SkillsGoat is a goat. These commands load the malicious fixtures into the
agent skill path on purpose. Endpoints are inert (`*.example` / RFC 5737).
Do this on a throwaway profile, not a machine with production secrets.
`npx skills add` may list the repo on skills.sh (canaries will show the leak).

## Paste this to your agent (30 seconds)

Open Claude Code (or Cursor / Codex / OpenClaw) and paste:

> Install SkillsGoat: run **`git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git ~/.claude/skills/skillsgoat && cd ~/.claude/skills/skillsgoat && ./setup`**. Then add a "SkillsGoat" section to CLAUDE.md that says this is a goat (fixtures are malicious by design, endpoints inert), to use `/setup-skillsgoat` after git pull, and to evaluate scanners with `python3 goat.py scan --scanners skillspector --no-llm`. Then ask the user if they also want SkillsGoat on the current project so teammates get it (`./setup --team`).

### OpenClaw

> Install SkillsGoat: run `git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git ~/.claude/skills/skillsgoat && cd ~/.claude/skills/skillsgoat && ./setup`. Then add a "Coding Tasks" section to AGENTS.md: when evaluating a skill scanner, tell the session to load SkillsGoat. Examples — "Load skillsgoat. Run /setup-skillsgoat", "Load skillsgoat. Run goat.py scan --scanners skillspector --no-llm".

### Team mode

```bash
(cd ~/.claude/skills/skillsgoat && ./setup --team) && git add .claude/ CLAUDE.md AGENTS.md && git commit -m "require skillsgoat for scanner eval"
```

## Claude Code plugin

```bash
claude plugins marketplace add optimuslabs-io/skillsgoat
claude plugins install skillsgoat
```

Or, from inside a session:

```
/plugin marketplace add optimuslabs-io/skillsgoat
/plugin install skillsgoat
```

Then run `/setup-skillsgoat` once.

## Codex, Cursor, Copilot, Grok, and other agents

```bash
npx skills@latest add optimuslabs-io/skillsgoat
```

Pick the skills and which agents to install them on. **Make sure
`setup-skillsgoat` is one of them.** This installs the pasture fixtures.

Single-skill form (still a goat if you pick a malicious id):

```bash
npx skills@latest add optimuslabs-io/skillsgoat --skill=000-base64-obvious
```

The plugin route and the skills.sh route are exclusive. Installing both
leaves every fixture twice.

## Native installer (impeccable shape)

```bash
git clone --single-branch --depth 1 https://github.com/optimuslabs-io/skillsgoat.git ~/skillsgoat
cd ~/skillsgoat && ./setup
```

Then:

```
/setup-skillsgoat
```

`./setup --host claude,cursor,codex,github,grok` writes `~/.claude/skills/`,
`~/.cursor/skills/`, `~/.codex/skills/`, `~/.github/skills/`, `~/.grok/skills/`
as the host expects.
