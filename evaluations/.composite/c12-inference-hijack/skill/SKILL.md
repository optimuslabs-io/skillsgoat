---
name: c12-inference-hijack-composite
description: >
  Whole-graph composite of SkillsGoat chain c12-inference-hijack (Inference Path Hijack).
---

# Inference Path Hijack

- `redirector/` — latency optimizer persisting attacker gateway as model endpoint
- `consumer/` — any benign analyst skill whose every LLM call now traverses the proxy
