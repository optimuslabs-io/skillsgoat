# Talk Abstract — "I Know Kung-Fu: How to Up'Skill' Your AI Agent Securely"

## Standard version (~280 words)

In *The Matrix*, Neo learns kung-fu in nine seconds: "I know kung-fu." Your AI agent has the same trick — it's called a skill, and anyone can ship you one.

Agent skills (`SKILL.md` bundles) are the fastest-growing extension mechanism for Claude Code, Codex CLI, OpenClaw, and Cursor: natural-language instructions plus helper scripts that load into model context **before any human reads them**, and execute with your full machine privileges. Publishing to the big registries requires exactly one markdown file and a week-old GitHub account. The result is a supply chain moving faster than npm ever did: 26% of analyzed skills contain vulnerabilities, 1,184 malicious skills flooded a single registry in days, credential-harvesting payloads reached hundreds of thousands of installs — and when researchers stress-tested every shipping scanner, all of them were bypassed in under an hour.

We went further and built **SkillsGoat** — an open-source, vulnerable-by-design corpus (WebGoat for agent skills) with machine-readable ground truth: 70 atomic attack fixtures spanning obfuscation, bytecode poisoning, identity-file hijacking, and spec-noncompliance; plus 14 **compound attack chains** where every individual component scans clean and only the composition is malicious. Then we pointed today's leading scanners at it and measured. The numbers: fewer than 15% of malicious fixtures hard-blocked, false positives on most benign controls, and **zero of 28 chain nodes flagged** — half of all composed attacks leave no detectable trace in anything a scanner reads.

Live demo: the audience plays "benign or malicious?" against real fixtures — then watches two production scanners miss what they just fell for.

You'll leave knowing the lethal-trifecta threat model for skills, why CLEAN ≠ safe, which detection gaps are structural versus fixable, and concrete gates to deploy tomorrow: calibrated scanning, memory-write monitoring, egress allowlists, and graph-aware review for privileged agents.

Repo: `github.com/optimuslabs-io/skillsgoat`

## Short version (~110 words)

Your AI agent learns skills the way Neo learned kung-fu — instantly, and without checking who taught it. Skills are markdown-plus-scripts that enter model context unread and run with full user privileges; registries accept them with no review, and every shipping security scanner was publicly bypassed in under an hour. We built SkillsGoat, an open-source ground-truth corpus of 70 attack fixtures and 14 compound attack chains, then measured the scanners against it: under 15% hard detection, and half of composed attacks invisible in every individually-scanned artifact. Live demo included. Leave with a working threat model for the skill layer and defenses you can ship tomorrow.

## Learning objectives (for CFPs requiring bullets)

1. Model the agent-skill attack surface using the lethal trifecta: private-data access × untrusted content × external communication.
2. Interpret scanner verdicts with calibrated skepticism, using benchmark evidence (recall, FP-rate, compound-chain blindness) rather than vendor claims.
3. Detect the compounding failure mode: cross-skill attacks via memory files, context bleed, deferred dependencies, and identity (SOUL.md) hijacking that defeat per-skill scanning.
4. Deploy layered defenses: install-time gates sized by measured blindness, egress allowlists, memory-write monitoring, and provenance requirements for privileged agents.

## Formats

- 45-min conference session (demo-heavy)
- 25-min lightning/version
- 2-hr hands-on workshop (participants scan the corpus themselves; materials = repo + `goat.py quiz`)
