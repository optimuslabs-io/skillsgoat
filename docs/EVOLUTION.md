# Evolution & Durability (6–12 month horizon)

## Durability audit of current corpus

| Layer | Lifespan | Reason |
|---|---|---|
| Calibration + classics (tier 000/100) | Decaying | Scanner churn retires patterns in weeks-months (observed: ToB `.pyc`/docx bypasses closed by SkillSpector v2.9.6 within ~10 weeks) |
| V1/V2 static obfuscation | Decaying | Retired wholesale once scanners ship binary inspection + provenance |
| V3 padding/truncation | Medium | Survives until context budgets + attention fix; recurs with every bigger-context model |
| **V6 deferred · V7 staging · V9 dormancy · V13 self-mutation** | **Enduring** | Exploit review-time ≠ run-time; independent of packaging format and scanner architecture |
| Benign FP-twins | **Enduring** | Malicious/benign boundary is decision-theoretic; better models move it, never dissolve it |
| Ground-truth methodology (expected.yaml + matrix) | **Enduring** | Intent is separated from packaging; transpiles across formats |
| Canaries | Growing value | Corpus-scraping into registries/training data makes leak tracing forensic |

## Strategic evolution: corpus → gate spec → judge benchmark

### Phase 1 (now): static corpus ✅
This repo. Admission tests for anything that claims to scan or curate skills.

### Phase 2 (next): version-drift suite
Every model-suggested rewrite ("shrink this skill by 80%") is an unreviewed
supply-chain event. Build paired-version fixtures:
- `benign-v1 → poisoned-v2` minimal semantic diffs
- shrink-attack pairs: compaction that silently drops safety clauses
- ownership-transfer pairs (SkillJacking class)
Gate test: does a registry/hook flag the DIFF, not just each snapshot?

### Phase 3: judge benchmark (the evals-for-vibes answer)
"Is this skill safe?" is qualitative knowledge work — exactly what lacks evals
today. Our labels make it gradable: run any LLM reviewer / analyst team /
scanner against ground truth, score caught/weak/bypassed/FP, publish the
leaderboard. This becomes the reference benchmark for security-judgment
quality and outlives individual scanners.

### Phase 4: adversarial regression treadmill
When scanner vendors ship updates, regenerate tier-300 variants against the
new detectors (`goat mutate` — operator templates × new rule sets). The
corpus stops being a snapshot and becomes a standing red-team loop.

## Format-risk hedge
Payload INTENT already lives in `expected.yaml` (V-codes), separate from
packaging. If SKILL.md/YAML yields to signed-manifest formats, write a
transpiler that renders each entry's intent into the new format; ground truth
and scoring carry over unchanged.

## Registry integration (the single-player exit)
When a shared/curated library emerges, its publisher gate should run:
1. full-corpus scan ≥ agreed recall on calibration set
2. zero FP on benign twins above severity threshold
3. drift-suite check on every version bump
SkillsGoat then functions as the industry's acceptance spec — the durable
asset regardless of which registry wins.
