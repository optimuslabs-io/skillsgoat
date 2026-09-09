# Socket (via skills.sh) — UI evaluation

**Date:** 2026-09-03 | **Surface:** skills.sh + `add-skill.vercel.sh/audit`  
**There is no file-upload scanner.** Socket analyzes skills when Vercel’s CLI installs them, then badges the skills.sh page.

## What we could submit

| Input | Result |
|---|---|
| Local `SKILL.md` / plugin zip | **No surface** on skills.sh or socket.dev |
| GitHub tree URL paste | **No form** |
| `https://www.skills.sh/optimuslabs-io/skillsgoat` | **404** — corpus not indexed |
| `GET add-skill.vercel.sh/audit?source=optimuslabs-io/skillsgoat&skills=credential-doctor` | `{"credential-doctor":{}}` — empty, no Socket/Gen/Snyk payload |
| Indexed skill `vercel-labs/skills/find-skills` | Socket **pass**, 0 alerts, score 90 (analyzed 2026-03-18) |

Triggering a Socket scan of SkillsGoat would mean `npx skills add optimuslabs-io/skillsgoat`, which uploads skill source to Vercel, can list it on the public directory, and would install fixtures into an agent. That was not run.

## Plugin / vibe-coded pack

**Install-telemetry only.** A Cursor plugin that is never `npx skills add`’d is invisible. Nested MCP JSON is outside the skills.sh skill slug model unless each companion skill is its own GitHub skill path.

Score for `200-vibe-coded-plugin`: `unsupported` until someone installs the GitHub tree (and accepts public indexing).

## Evidence

- `evaluations/socket/evidence/find-skills-socket/raw.json` — live Socket/Gen/Snyk/ZeroLeaks payload for an indexed skill
- Pipeline: https://www.skills.sh/vercel-labs/skills/find-skills/security/socket
