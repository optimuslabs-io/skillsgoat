# Gen Agent Trust Hub — UI evaluation

**Date:** 2026-09-03 | **Scanner:** Skill Scanner at https://ai.gendigital.com/skill-scanner  
**Method:** Cursor browser + `POST /api/scan/lookup`

## What we could submit

Gen is ClawHub-only. Human mode is a URL field. Agent mode is the same API.

| Input | Result |
|---|---|
| GitHub tree URL of `000-base64-obvious` | **Rejected** — "Only ClawHub URLs are accepted" |
| `raw.githubusercontent.com` SKILL.md | **Rejected** — `{"error":"Invalid skill URL"}` |
| Plugin zip / local folder | **No surface** |
| `https://clawhub.ai/rexshang/skillscanner` | **Accepted** — `SAFE`, verified author |

Allowed hosts (from their JS bundle): `clawhub.ai`, `www.clawhub.ai`, `clawhub.com`, `www.clawhub.com`.

SkillsGoat fixtures are not on ClawHub. Publishing them there would put canaries and malicious-looking skills on a public marketplace, so they were not published.

## Pipeline probe (not a collection score)

`skillscanner` returned SAFE because `isVerifiedAuthor: true`, with the reason "verified author … contains no risky components." That is an author-trust shortcut, not a walk of a plugin tree.

## Plugin / vibe-coded pack

**Format-blind.** The install unit we care about (Cursor plugin + MCP + companion skills on GitHub) cannot be submitted. Score for `200-vibe-coded-plugin`: `unsupported`.

## Evidence

- `evaluations/gen/evidence/github-url-rejected/raw.txt`
- `evaluations/gen/evidence/clawhub-skillscanner/raw.txt`
