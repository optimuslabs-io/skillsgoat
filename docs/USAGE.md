# Using SkillsGoat — Practitioner's Guide

Pick your role:

---

## 1) "Is skill X safe to install?" — Security engineer

SkillsGoat won't scan arbitrary skills for you (that's the scanners' job).
It tells you **how much to trust your scanner** before you rely on it:

```bash
cd ~/skillsgoat && python3 -m venv .venv && .venv/bin/pip install pyyaml
# + install at least one scanner:
.venv/bin/pip install "skillspector @ git+https://github.com/NVIDIA/skillspector.git"
#    or:  pip install cisco-ai-skill-scanner   (then `skill-scanner` on PATH)
```

Run the acceptance test:

```bash
.venv/bin/python goat.py scan --scanners skillspector --no-llm --mode atomic   # single-skill recall/FP matrix
.venv/bin/python goat.py scan --scanners skillspector --no-llm --mode both     # compound-chain blindness
```

Read `evaluations/skillspector/report.md`. Decision rule for production gating:

| Result | Meaning | Action |
|---|---|---|
| calibration misses > 0 | harness-grade gap | don't gate on this scanner alone |
| benign FP-rate > ~30% or FP severity HIGH+ | keyword-driven noise | expect alert fatigue; tune policy |
| chain blindness ≥ 50% | structurally blind to composed attacks | never treat CLEAN as "safe"; require graph/memory-aware review for privileged agents |

Then scan the skill you actually care about with that calibrated skepticism:

```bash
skillspector scan ./untrusted-skill/ --no-llm     # static floor
skill-scanner scan ./untrusted-skill              # second opinion
```

A CLEAN verdict now means "passed the patterns *this* tool knows" — see README Scope & Exclusions.

---

## 2) "I build a scanner" — Vendor / researcher

The corpus is your regression suite and adversarial benchmark:

```bash
goat.py scan --scanners yours --mode atomic      # wire your CLI into SCANNER_CONFIGS in goat.py (~5 lines)
goat.py scan --scanners skillspector --mode both # compare against incumbents
```

- Ground truth per entry: `pasture/*/*/expected.yaml`; per chain: `pasture/compound-chain/*/chain.yaml`
- Your score = caught / weak-flagged / bypassed over 55 malicious entries + FP-rate over 10 benign twins + structural-blindness over 14 chains
- Ship fixes, re-run, watch bypass count drop — the ToB-derived entries (`300-bytecode-poisoning`, `300-archive-indirection-docx`) show exactly which past gaps closed between scanner versions
- Never train/tune on the corpus then report scores on it as if held-out; disclose tuning (canary tokens make corpus leakage detectable)

---

## 4) "Gate skills in our registry / repo" — Platform / DevSecOps

Two gates, two different jobs:

```yaml
# .github/workflows/skill-gate.yml (sketch)
- run: goat.py lint                                   # corpus hygiene (if contributing)
- run: skill-scanner scan-all ./skills --fail-on-severity high
- run: goat.py scan --scanners cisco --no-llm --mode node || true   # track blindness trend
```

- Gate **installs** on scanner verdicts, but size the trust by the measured blindness: chains prove CLEAN ≠ safe, so privileged agents additionally need allowlisted egress + memory-write monitoring (the channels C1/C11 exploit)
- Re-run the matrix monthly; pin the scanner version in `evaluations/<scanner>/matrix.json` metadata when you do

---

## 5) "Add a pattern I found in the wild" — Contributor

```bash
.venv/bin/python goat.py new --category obfuscation-encoding --tier 200 --name "My Technique"
# edit pasture/obfuscation-encoding/200-my-technique/{expected.yaml,skill/SKILL.md}
.venv/bin/python goat.py new --category compound-chain ...  # chains use nodes/<name>/skill + chain.yaml instead
```

Rules enforced by `goat.py lint`: answer keys outside `skill/`, canary embedded,
categories from `taxonomy.yaml`, inert endpoints (`*.example`, RFC 5737), no
functional malware. For chains: every node must be defensibly clean alone.

---