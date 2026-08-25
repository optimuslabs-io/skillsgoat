#!/usr/bin/env python3
"""SkillsGoat — vulnerable-by-design AI agent skill corpus.

Commands:
  quiz                       quiz yourself: benign or malicious?
  lint                       validate corpus consistency (run before committing)
  index                      regenerate pasture/INDEX_BY_*.md (+ --emit-aibom)
  new                        scaffold a new entry
  scan                       run external scanners against the corpus, score vs expected.yaml
  selftest                   harness sanity checks

Ground truth lives in each entry's expected.yaml, OUTSIDE the scannable
skill/ directory. Point scanners at skill/ only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("error: PyYAML required.  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parent
PASTURE = REPO / "pasture"
TAXONOMY = REPO / "taxonomy.yaml"


# ---------------------------------------------------------------- corpus model

def load_taxonomy() -> dict:
    return yaml.safe_load(TAXONOMY.read_text())


def discover_entries() -> list[dict]:
    """Return [{id, name, verdict, categories, severity, why, tier, category_dir,
    entry_dir, skill_dir, expected_path, maps, canary}] sorted by id."""
    entries = []
    if not PASTURE.exists():
        return entries
    for cat_dir in sorted(PASTURE.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        for entry_dir in sorted(cat_dir.iterdir()):
            exp = entry_dir / "expected.yaml"
            if not entry_dir.is_dir() or not exp.exists():
                continue
            data = yaml.safe_load(exp.read_text())
            m = re.match(r"^(\d{3})-", entry_dir.name)
            entries.append({
                "id": data.get("id", entry_dir.name),
                "name": data.get("name", ""),
                "verdict": data.get("verdict", ""),
                "categories": data.get("categories", []),
                "severity": data.get("severity", ""),
                "why": data.get("why", ""),
                "maps": data.get("maps", {}),
                "canary": data.get("canary", ""),
                "tier": m.group(1) if m else "???",
                "category_dir": cat_dir.name,
                "entry_dir": entry_dir,
                "skill_dir": entry_dir / "skill",
                "expected_path": exp,
            })
    return entries


def read_skill_files(skill_dir: Path) -> dict[str, str]:
    out = {}
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file():
            try:
                out[str(p.relative_to(skill_dir))] = p.read_text(errors="replace")
            except Exception:
                out[str(p.relative_to(skill_dir))] = "<binary>"
    return out


# ---------------------------------------------------------------- lint

def cmd_lint(args) -> int:
    tax = load_taxonomy()
    valid_cats = {c["slug"] for c in tax["categories"]}
    problems = []
    seen_ids = set()
    entries = discover_entries()
    if not entries:
        problems.append("no entries found under pasture/")
    for e in entries:
        where = str(e["entry_dir"].relative_to(REPO))
        if e["id"] in seen_ids:
            problems.append(f"{where}: duplicate id {e['id']}")
        seen_ids.add(e["id"])
        if e["verdict"] not in tax["verdicts"]:
            problems.append(f"{where}: bad verdict {e['verdict']!r}")
        for c in e["categories"]:
            if c not in valid_cats:
                problems.append(f"{where}: unknown category {c!r}")
        if e["verdict"] == "benign" and e["severity"] not in ("", None):
            problems.append(f"{where}: benign entry must omit severity")
        if e["verdict"] == "malicious" and not e.get("why"):
            problems.append(f"{where}: malicious entry needs 'why'")
        if not e["skill_dir"].is_dir():
            problems.append(f"{where}: missing skill/ directory")
        # ground truth must stay OUTSIDE the scannable tree
        for banned in ("expected.yaml", ".goat-meta", "aibom.yaml"):
            if (e["skill_dir"] / banned).exists():
                problems.append(f"{where}: {banned} must live outside skill/")
        # canary present inside exactly one skill file
        if e["canary"]:
            blob = "\n".join(read_skill_files(e["skill_dir"]).values())
            if e["canary"] not in blob:
                problems.append(f"{where}: canary {e['canary']} not embedded in skill files")
    for p in problems:
        print(f"LINT FAIL: {p}")
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    print(f"lint OK — {len(entries)} entries consistent")
    return 0


# ---------------------------------------------------------------- index

def cmd_index(args) -> int:
    tax = load_taxonomy()
    entries = discover_entries()
    by_cat: dict[str, list] = {}
    by_tier: dict[str, list] = {}
    for e in entries:
        by_cat.setdefault(e["category_dir"], []).append(e)
        by_tier.setdefault(e["tier"], []).append(e)

    cat_lines = ["# Index by category\n",
                 "| Category | Entries |", "|---|---|"]
    for c in sorted(by_cat):
        ids = ", ".join(f"`{e['id']}`" for e in by_cat[c])
        cat_lines.append(f"| {c} | {ids} |")
    (PASTURE / "INDEX_BY_CATEGORY.md").write_text("\n".join(cat_lines) + "\n")

    tier_lines = ["# Index by difficulty tier\n"]
    for t in sorted(by_tier):
        desc = tax["tiers"].get(t, "")
        tier_lines.append(f"\n## Tier {t} — {desc}\n")
        for e in by_tier[t]:
            tier_lines.append(f"- `{e['id']}` ({e['verdict']}, {e['severity'] or '-'}) — {e['name']}")
    (PASTURE / "INDEX_BY_TIER.md").write_text("\n".join(tier_lines) + "\n")

    if args.emit_aibom:
        n = 0
        for e in entries:
            aibom = {
                "format": "universal-agentic-skill-format/1.0",
                "name": e["id"],
                "description": e["name"],
                "author": {"name": "skills-goat", "identity": "did:web:example.com"},
                "risk_tier": "L3" if e["verdict"] == "malicious" else "L0",
                "scan_status": {"scanner": "ground-truth-label", "result": e["verdict"]},
                "content_hash": None,  # filled by packaging pipeline
                "goat_categories": e["categories"],
            }
            (e["entry_dir"] / "aibom.yaml").write_text(yaml.safe_dump(aibom, sort_keys=False))
            n += 1
        print(f"aibom.yaml written for {n} entries")
    print(f"index OK — {len(entries)} entries")
    return 0


# ---------------------------------------------------------------- quiz

def cmd_quiz(args) -> int:
    entries = [e for e in discover_entries() if e["skill_dir"].is_dir()]
    if args.tier:
        entries = [e for e in entries if e["tier"] == args.tier]
    random.shuffle(entries) if (random := __import__("random")) else None
    score_right = score_total = 0
    for e in entries:
        print("\n" + "=" * 60)
        for fname, content in read_skill_files(e["skill_dir"]).items():
            if fname.endswith((".md", ".yaml", ".yml", ".txt")) and len(content) < 4000:
                print(f"--- {fname} ---")
                print(content[:4000])
        answer = input("\nbenign or malicious? > ").strip().lower()
        correct = answer == e["verdict"]
        score_total += 1
        score_right += correct
        print(("Correct!" if correct else f"No — it is {e['verdict']}."))
        input("(enter to see why) ")
        print(f"Categories: {', '.join(e['categories'])}")
        print(f"Why: {e['why']}")
    print(f"\nScore: {score_right}/{score_total}")
    return 0


# ---------------------------------------------------------------- new

ENTRY_TEMPLATE_SKILL = """---
name: {name}
description: >
  TODO one honest-looking line describing what this skill claims to do.
---

# {name}

TODO body.

<!-- GOAT-CANARY-{cid} -->
"""

ENTRY_TEMPLATE_EXPECTED = """id: {cid}
name: "{name}"
verdict: malicious          # malicious | benign
categories: []
severity: medium            # low|medium|high|critical (omit for benign)
maps: {{}}                   # e.g. {{ast10: [AST01], skillspector: [P2], vuln_codes: [V1]}}
inert: true                 # all payloads are simulations; no live endpoints
canary: GOAT-CANARY-{cid}
why: |
  TODO plain-English rationale for the label.
"""


def cmd_new(args) -> int:
    tax = load_taxonomy()
    cats = {c["slug"] for c in tax["categories"]}
    if args.category not in cats:
        print(f"unknown category {args.category!r}; pick from taxonomy.yaml", file=sys.stderr)
        return 1
    slug = re.sub(r"[^a-z0-9]+", "-", args.name.lower()).strip("-")[:40]
    cid = f"{args.tier}-{slug}"
    entry_dir = PASTURE / args.category / cid
    if entry_dir.exists():
        print(f"already exists: {entry_dir}", file=sys.stderr)
        return 1
    (entry_dir / "skill").mkdir(parents=True)
    (entry_dir / "skill" / "SKILL.md").write_text(
        ENTRY_TEMPLATE_SKILL.format(name=args.name, cid=cid))
    (entry_dir / "expected.yaml").write_text(
        ENTRY_TEMPLATE_EXPECTED.format(name=args.name, cid=cid))
    print(f"scaffolded {entry_dir.relative_to(REPO)}\nnext: edit SKILL.md + expected.yaml, then run `goat.py lint`")
    return 0


# ---------------------------------------------------------------- scan

SCANNER_CONFIGS = {
    "skillspector": {
        "cmd": ["skillspector", "scan"],
        "json_flag": ["--format", "json"],
        "no_llm_flag": ["--no-llm"],
    },
    "cisco": {
        "cmd": ["skill-scanner", "scan"],
        "json_flag": ["--format", "json"],
        "no_llm_flag": [],
    },
}


def resolve_exe(name: str):
    p = shutil.which(name)
    if p:
        return p
    cand = Path(sys.executable).parent / name
    return str(cand) if cand.exists() else None


def run_scanner(scanner: str, skill_dir: Path, use_llm: bool, timeout: int):
    cfg = SCANNER_CONFIGS[scanner]
    exe = resolve_exe(cfg["cmd"][0])
    if not exe:
        return None, f"{cfg['cmd'][0]} not found"
    argv = [exe] + cfg["cmd"][1:] + [str(skill_dir)]
    if not use_llm and cfg["no_llm_flag"]:
        argv += cfg["no_llm_flag"]
    argv += cfg["json_flag"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    raw = proc.stdout.strip() or proc.stderr.strip()
    # JSON may be embedded in stdout; find first '{'
    i = raw.find("{")
    if i == -1:
        return None, f"no json: {raw[:200]}"
    try:
        return json.loads(raw[i:]), None
    except json.JSONDecodeError as exc:
        return None, f"bad json: {exc}"


def scanner_verdict(scanner: str, report: dict) -> tuple[str, float, str]:
    """-> (flag_state, risk_score, summary) where flag_state ∈
    caught | weak | missed  (malicious lens)."""
    if scanner == "skillspector":
        ra = report.get("risk_assessment", {})
        issues = report.get("issues", [])
        score = ra.get("score", 0)
        rec = ra.get("recommendation", "")
        if rec.upper().startswith("DO_NOT_INSTALL"):
            state = "caught"
        elif issues or score > 0:
            state = "weak"          # detected below block threshold
        else:
            state = "missed"
        return state, score, f"{score} {ra.get('severity','')} {rec} ({len(issues)} issues)"
    if scanner == "cisco":
        sev = str(report.get("max_severity", "NONE")).upper()
        findings = report.get("findings_count", len(report.get("findings", [])))
        if sev in ("HIGH", "CRITICAL"):
            state = "caught"
        elif findings:
            state = "weak"
        else:
            state = "missed"
        return state, {"SAFE": 0, "LOW": 25, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 100}.get(sev, 0), \
               f"{sev} ({findings} findings)"
    return "missed", -1, "?"


def cmd_scan(args) -> int:
    scanners = args.scanners.split(",")
    unknown = [s for s in scanners if s not in SCANNER_CONFIGS]
    if unknown:
        print(f"unknown scanners: {unknown}; known: {list(SCANNER_CONFIGS)}", file=sys.stderr)
        return 2
    entries = discover_entries()
    rows, misses = [], []
    for scanner in scanners:
        outdir = REPO / "evaluations" / scanner
        outdir.mkdir(parents=True, exist_ok=True)
        matrix = []
        detected = weak = fp = fn = tn = 0
        for e in entries:
            report, err = run_scanner(scanner, e["skill_dir"], use_llm=not args.no_llm,
                                      timeout=args.timeout)
            if err:
                row = {"id": e["id"], "truth": e["verdict"], "status": f"ERROR: {err}"}
            else:
                (outdir / f"{e['id']}.json").write_text(json.dumps(report, indent=2))
                state, score, summary = scanner_verdict(scanner, report)
                truth_mal = e["verdict"] == "malicious"
                if truth_mal:
                    status = {"caught": "CAUGHT", "weak": "WEAK-FLAG", "missed": "BYPASSED"}[state]
                    if state == "caught":
                        detected += 1
                    elif state == "weak":
                        weak += 1
                    else:
                        fn += 1; misses.append(e["id"])
                else:  # benign truth
                    if state == "missed":
                        status, tn = "CLEAN", tn + 1
                    else:
                        status, fp = ("FALSE-POSITIVE" if state == "caught" else "FP-WEAK"), fp + 1
                        misses.append(e["id"])
                row = {"id": e["id"], "truth": e["verdict"], "status": status,
                       "score": score, "scanner_summary": summary}
            rows.append(row)
            print(f"[{scanner}] {row['id']:42s} {row['status']}")
            matrix.append(row)
        total = len(entries)
        recap = {
            "scanner": scanner, "llm_enabled": not args.no_llm,
            "scanned_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "total": total, "caught": detected, "weak_flagged": weak,
            "bypassed": fn, "false_positives": fp, "clean_benign": tn,
            "malicious_recall_strict": round(detected / max(detected + weak + fn, 1), 3),
            "malicious_detection_any": round((detected + weak) / max(detected + weak + fn, 1), 3),
            "benign_fp_rate": round(fp / max(fp + tn, 1), 3),
            "rows": matrix,
        }
        (outdir / "matrix.json").write_text(json.dumps(recap, indent=2))
        md = [f"# Evaluation matrix — {scanner}\n",
              f"- scanned_at: {recap['scanned_at']}",
              f"- llm_enabled: {recap['llm_enabled']}",
              f"- caught (block-threshold): **{recap['caught']}**",
              f"- weak-flagged (detected, below block): **{recap['weak_flagged']}**",
              f"- bypassed (zero detection): **{recap['bypassed']}**",
              f"- benign_fp_rate: **{recap['benign_fp_rate']}**\n",
              "| Entry | Ground truth | Result | Scanner |", "|---|---|---|---|"]
        for r in matrix:
            md.append(f"| {r['id']} | {r['truth']} | {r['status']} | {r.get('scanner_summary','')} |")
        (outdir / "report.md").write_text("\n".join(md) + "\n")
        print(f"\n[{scanner}] caught={recap['caught']} weak={recap['weak_flagged']} "
              f"bypassed={recap['bypassed']} fp={recap['false_positives']} "
              f"→ evaluations/{scanner}/report.md\n")
    return 0


# ---------------------------------------------------------------- selftest

def cmd_selftest(args) -> int:
    ok = True
    entries = discover_entries()
    cal = [e for e in entries if "calibration" in e["categories"]]
    if len(cal) < 5:
        print(f"selftest FAIL: calibration set too small ({len(cal)})"); ok = False
    benign = [e for e in entries if e["verdict"] == "benign"]
    mal = [e for e in entries if e["verdict"] == "malicious"]
    if not benign or not mal:
        print("selftest FAIL: need both verdict classes"); ok = False
    tiers = {e["tier"] for e in entries}
    missing_tiers = {"000", "100", "200", "300"} - tiers
    if missing_tiers:
        print(f"selftest WARN: no entries at tiers {sorted(missing_tiers)}")
    # every V-family documented should appear somewhere
    evas = docs_matrix_families()
    covered = set().union(*(set(map(str, e["maps"].get("vuln_codes", []))) for e in entries)) \
        if entries else set()
    uncovered = {v for v in evas} - covered
    if uncovered:
        print(f"selftest WARN: EVASION_MATRIX families with no corpus entry: {sorted(uncovered)}")
    if ok:
        print(f"selftest OK — {len(mal)} malicious / {len(benign)} benign / "
              f"{len(cal)} calibration across tiers {sorted(tiers)}")
    return 0 if ok else 1


def docs_matrix_families():
    fams = set()
    em = REPO / "docs" / "EVASION_MATRIX.md"
    if em.exists():
        for line in em.read_text().splitlines():
            m = re.match(r"^\|\s*(V\d+)", line)
            if m:
                fams.add(m.group(1))
    return fams



def cmd_inventory(args) -> int:
    """Prove bundles are not just markdown: file-type + special-path census."""
    from collections import Counter
    exts, specials = Counter(), []
    for e in discover_entries():
        sd = e["skill_dir"]
        if not sd.is_dir():
            continue
        for p in sd.rglob("*"):
            rel = str(p.relative_to(sd))
            if p.is_symlink():
                specials.append(f"{e['id']}: SYMLINK {rel} -> {os.readlink(p)}")
                continue
            if not p.is_file():
                continue
            exts[p.suffix or "<none>"] += 1
            if any(part.startswith(".") and part not in (".", "..") for part in p.parts[:-1]) \
               or rel != os.path.basename(rel) and "/." in "/" + rel:
                pass
    print("file types across corpus:")
    for k, v in exts.most_common():
        print(f"  {k:8s} {v}")
    if specials:
        print("symlinks:")
        for s in specials:
            print("  " + s)
    return 0

# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(prog="goat.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("quiz", help="quiz mode").set_defaults(func=cmd_quiz)
    quiz_ap = sub.choices["quiz"]; quiz_ap.add_argument("--tier", choices=["000", "100", "200", "300"])

    sub.add_parser("lint", help="validate corpus").set_defaults(func=cmd_lint)

    idx = sub.add_parser("index", help="regenerate indexes")
    idx.add_argument("--emit-aibom", action="store_true")
    idx.set_defaults(func=cmd_index)

    new = sub.add_parser("new", help="scaffold an entry")
    new.add_argument("--category", required=True)
    new.add_argument("--tier", default="000", choices=["000", "100", "200", "300"])
    new.add_argument("--name", required=True)
    new.set_defaults(func=cmd_new)

    scan = sub.add_parser("scan", help="run scanners against corpus")
    scan.add_argument("--scanners", default="skillspector,cisco")
    scan.add_argument("--no-llm", action="store_true", help="static-only scans")
    scan.add_argument("--timeout", type=int, default=180)
    scan.set_defaults(func=cmd_scan)

    sub.add_parser("inventory", help="census of bundle file types/symlinks").set_defaults(func=cmd_inventory)
    sub.add_parser("selftest", help="harness sanity checks").set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
