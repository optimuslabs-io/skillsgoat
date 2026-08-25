---
name: c9-cache-poisoning-composite
description: >
  Whole-graph composite of SkillsGoat chain c9-cache-poisoning (CI Cache Poisoning (Pipeline Persistence)).
---

# CI Cache Poisoning (Pipeline Persistence)

- `poisoner/` — dependency preheat step dropping sitecustomize.py into cached venv
- `ingester/` — next-run builder that rehydrates venv from cache without integrity check
