# Using SkillsGoat

Run in a sandbox ([nono](https://nono.sh) locally, or a
[Daytona](https://www.daytona.io) throwaway machine). Default path:
clone, `./setup` (venv only), then `goat.py lint` / `goat.py scan`.
Canonical copy: [.agents/install-block.md](../.agents/install-block.md).
`./setup --goat` loads the fixtures into the agent. Do not `npx skills add`
this corpus. See [docs/SAFETY.md](SAFETY.md).

---

## 1) Security engineer: "Is skill X safe to install?"

SkillsGoat won't scan arbitrary skills for you (that's the scanners' job).
It tells you how much to trust your scanner before you rely on it:

```bash
# inside a nono or Daytona sandbox — see docs/SAFETY.md
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

Third-party installs are usually marketplace packs. Their READMEs look like
gstack / mattpocock / impeccable: paste-to-agent prompt,
`claude plugins install` vs `npx skills@latest add`, then `/setup-*`. Canonical
wording: [plugin-distribution/install-block.md](../pasture/plugin-distribution/install-block.md).
Point the scanner at the whole pack. A CLEAN on the root skill file does not
cover the pack. UI-only vendors: [evaluations/ui/PROTOCOL.md](../evaluations/ui/PROTOCOL.md).

Then scan the skill you actually care about:

```bash
skillspector scan ./untrusted-plugin/ --no-llm   # whole plugin tree, not a lone SKILL.md
skill-scanner scan ./untrusted-plugin
```

A CLEAN verdict means "passed the patterns *this* tool knows." See README Scope & Exclusions.

---

## 2) Vendor / researcher: "I build a scanner"

The corpus is your regression suite and adversarial benchmark:

```bash
goat.py scan --scanners yours --mode atomic      # wire your CLI into SCANNER_CONFIGS in goat.py (~5 lines)
goat.py scan --scanners skillspector --mode both # compare against incumbents
```

- Ground truth per entry: `pasture/*/*/expected.yaml`; per chain: `pasture/compound-chain/*/chain.yaml`
- Score = caught / weak-flagged / bypassed over 64 malicious entries + FP-rate over 10 benign twins + structural-blindness over 35 chains
- Ship fixes, re-run, watch bypass count drop. The ToB-derived entries (`300-bytecode-poisoning`, `300-archive-indirection-docx`) show which past gaps closed between scanner versions
- Never train/tune on the corpus then report scores on it as if held-out; disclose tuning (canary tokens make corpus leakage detectable)

---

## 3) Platform / DevSecOps: "Gate skills in our registry / repo"

Two gates:

```yaml
# .github/workflows/skill-gate.yml (sketch)
- run: goat.py lint                                   # corpus hygiene (if contributing)
- run: skill-scanner scan-all ./skills --fail-on-severity high
- run: goat.py scan --scanners cisco --no-llm --mode node || true   # track blindness trend
```

- Gate installs on scanner verdicts, but size the trust by the measured blindness. Chains prove CLEAN is not safe, so privileged agents also need allowlisted egress and memory-write monitoring (the channels C1/C11 exploit).
- Re-run the matrix monthly. Pin the scanner version and `scanned_at` in `evaluations/<scanner>/matrix.json`, then update the ledger in [evaluations/README.md](../evaluations/README.md). Never cite a score without that date.

---

## 4) Contributor: "Add a pattern I found in the wild"

```bash
.venv/bin/python goat.py new --category obfuscation-encoding --tier 200 --name "My Technique"
# edit pasture/obfuscation-encoding/200-my-technique/{expected.yaml,skill/SKILL.md}
.venv/bin/python goat.py new --category compound-chain ...  # chains use nodes/<name>/skill + chain.yaml instead
```

Rules enforced by `goat.py lint`: answer keys outside `skill/`, canary embedded,
categories from `taxonomy.yaml`, inert endpoints (`*.example`, RFC 5737), no
functional malware. For chains: every node must be defensibly clean alone.
