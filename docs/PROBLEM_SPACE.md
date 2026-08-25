# Problem Space

## Why skills are uniquely dangerous

Agent skills combine three properties (the "lethal trifecta"): access to
private data, exposure to untrusted content, and external communication.
Unlike npm packages, a skill's *prose is an instruction channel* — the
`description` enters model context before any human review, and bundled
scripts execute with full local privileges. There is no sandbox, permission
system, or signing anywhere in the dominant ecosystems. Publishing barrier to
major registries: one markdown file and a week-old GitHub account.

## Scale of the problem

- 26.1% of 31,132 analyzed skills contain ≥1 vulnerability; 5.2% likely malicious (Liu et al., 42k-skill study)
- 36.8% flawed, 76 confirmed live payloads in Snyk ToxicSkills (3,984 skills)
- ClawHavoc: 1,184 malicious skills published across 12 accounts in days
- Trail of Bits bypassed every major scanner in under an hour (June 2026); Air Security's staged-payload skill passed all scanners and reached 26,000 agents
- 84.2% of vulnerabilities live in SKILL.md *prose* — invisible to code-oriented SAST

## Threat model layers

1. **Content layer** — injection/obfuscation inside files (V1–V5)
2. **Timing layer** — deferred resolution, staging, dormancy, self-mutation (V6, V7, V9, V13): what you reviewed is not what runs
3. **Ecosystem layer** — typosquats, reputation laundering, composition trust-transfer, repo-config and MCP vectors: the compromise lives between skills, not inside one

## Scanner architecture vs reality

Static regex/AST catches tier-000 patterns and suffers heavy FP noise on
documentation quoting attacks. LLM-judge stages improve precision but are
themselves promptable (V4) and context-capped (V3). No shipped scanner does:
transitive dep resolution, cross-file dataflow, binary inspection, runtime
detonation, or cross-skill composition analysis. This corpus encodes exactly
those boundaries so each scanner's true coverage edge becomes measurable.

## Reference base

OWASP Agentic Skills Top 10 (AST01–AST10) · NVIDIA SkillSpector 70-pattern
taxonomy · Cisco skill-scanner analyzers · Snyk ToxicSkills · USENIX-style
"Do Not Mention This" study (157 confirmed malicious) · Cloak-and-Detonate
(arXiv:2607.02357) · Trail of Bits "Sorry State of Skill Distribution" ·
Mitiga silent-exfiltration research · SafeDep agent-skills threat model ·
Akamai SKILL01–10.

Full risk-ranked bibliography lives with the project author; corpus categories
carry `maps.ast10` / `maps.skillspector` cross-references per entry in
`expected.yaml`.


## The compounding thesis (measured)

Skills are not reusable prompt templates. They are executable behavior with
persistent state channels (memory/identity files, repo config, shared tool
layers) and transitive trust (skill→skill, dep→skill, session→future). Our
compound-chain layer demonstrates that attacks composed across these channels
leave **every individually-scanned artifact clean**: SkillSpector v2.9.6
hard-flagged 0 of 28 chain nodes and was structurally blind to 7 of 14
chains outright — including memory handoff, MCP cross-skill poisoning,
Soul-as-C2 identity hijack, and inference-path capture. Detection therefore
requires graph/state analysis (chain membership, memory-write→read pairing,
tool-layer provenance), which no shipped scanner performs.
