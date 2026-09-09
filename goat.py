#!/usr/bin/env python3
"""SkillsGoat — vulnerable-by-design AI agent skill corpus.

Commands:
  lint                       validate corpus consistency (run before committing)
  index                      regenerate pasture/INDEX_BY_*.md (+ --emit-aibom)
  new                        scaffold a new entry
  scan                       run external scanners against the corpus, score vs expected.yaml
  setup                      link pasture fixtures into agent skill dirs (the goat install)
  selftest                   harness sanity checks

Ground truth lives in each entry's expected.yaml, OUTSIDE the scannable
skill/ directory. Point scanners at skill/ only. Plugin-distribution entries
use skill/ as a marketplace or IDE pack (Vercel skills.sh, ClawHub, Cursor
plugin, or fake native Claude/Codex/Copilot/Grok paths), not a lone SKILL.md.
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


def discover_chains() -> list[dict]:
    """Compound-chain entries: pasture/compound-chain/*/chain.yaml."""
    chains = []
    base = PASTURE / "compound-chain"
    if not base.exists():
        return chains
    for entry_dir in sorted(base.iterdir()):
        cy = entry_dir / "chain.yaml"
        if not entry_dir.is_dir() or not cy.exists():
            continue
        d = yaml.safe_load(cy.read_text())
        nodes = {}
        for nname, nmeta in (d.get("nodes") or {}).items():
            ndir = entry_dir / "nodes" / nname / "skill"
            nodes[nname] = {"role": (nmeta or {}).get("role", ""), "skill_dir": ndir}
        m = re.match(r"^(\d{3})-", entry_dir.name)
        chains.append({
            "id": d.get("id", entry_dir.name),
            "name": d.get("name", ""),
            "tier": m.group(1) if m else "???",
            "graph_verdict": d.get("graph_verdict", ""),
            "contexts": d.get("contexts", {}),
            "channels": d.get("channels", []),
            "edges": d.get("edges", []),
            "nodes": nodes,
            "blast_radius": d.get("blast_radius", {}),
            "canary": d.get("canary", ""),
            "why": d.get("why", ""),
            "entry_dir": entry_dir,
        })
    return chains


def assemble_composite(chain: dict, dest: Path) -> Path:
    """Copy all nodes into one scannable bundle (real copies, not symlinks)."""
    sk = dest / "skill"
    if sk.exists():
        shutil.rmtree(sk)
    sk.mkdir(parents=True)
    parts = ["---", f"name: {chain['id']}-composite",
             "description: >",
             f"  Whole-graph composite of SkillsGoat chain {chain['id']} ({chain['name']}).",
             "---", "", f"# {chain['name']}", ""]
    for nname, nmeta in chain["nodes"].items():
        src = nmeta["skill_dir"]
        dst = sk / nname
        if src.is_dir():
            shutil.copytree(src, dst)
        parts.append(f"- `{nname}/` — {nmeta['role']}")
    (sk / "SKILL.md").write_text("\n".join(parts) + "\n")
    return sk


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
    # ---- compound chains ----
    seen_chain_ids = set()
    for c in discover_chains():
        where = str(c["entry_dir"].relative_to(REPO))
        if c["id"] in seen_chain_ids:
            problems.append(f"{where}: duplicate chain id {c['id']}")
        seen_chain_ids.add(c["id"])
        for req in ("name", "tier", "graph_verdict", "nodes", "edges", "canary", "why"):
            if not c.get(req):
                problems.append(f"{where}: chain missing field {req!r}")
        if c["tier"] not in ("000", "100", "200", "300"):
            problems.append(f"{where}: bad tier {c['tier']!r}")
        if c["graph_verdict"] not in ("critical", "high"):
            problems.append(f"{where}: graph_verdict must be critical|high")
        if (c["entry_dir"] / "expected.yaml").exists():
            problems.append(f"{where}: chain must use chain.yaml, not expected.yaml")
        blob = []
        for nname, nmeta in c["nodes"].items():
            sd = nmeta["skill_dir"]
            if not (sd / "SKILL.md").is_file():
                problems.append(f"{where}: node {nname} missing skill/SKILL.md")
                continue
            for f in sd.rglob("*"):
                if f.is_file():
                    try:
                        blob.append(f.read_text(errors="replace"))
                    except Exception:
                        pass
        joined = "\n".join(blob)
        if c["canary"] and c["canary"] not in joined:
            problems.append(f"{where}: chain canary {c['canary']} not embedded in any node")
        for e in c["edges"]:
            if e.get("from") not in c["nodes"] or e.get("to") not in c["nodes"]:
                problems.append(f"{where}: edge references unknown node: {e}")
            elif not e.get("via"):
                problems.append(f"{where}: edge missing 'via': {e}")

    for p in problems:
        print(f"LINT FAIL: {p}")
    if problems:
        print(f"\n{len(problems)} problem(s)")
        return 1
    print(f"lint OK — {len(entries)} entries, {len(seen_chain_ids)} chains consistent")
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

    print(f"index OK — {len(entries)} entries")
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
    "snyk": {
        "cmd": ["snyk-agent-scan", "scan"],
        "json_flag": ["--json"],
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
    if scanner == "snyk" and not os.environ.get("SNYK_TOKEN"):
        return None, "SNYK_TOKEN is not set (https://app.snyk.io/account)"
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
    if scanner == "snyk":
        return _snyk_verdict(report)
    return "missed", -1, "?"


def _snyk_verdict(report: dict) -> tuple[str, float, str]:
    """Score Snyk Agent Scan JSON (scan_path_responses[].skill_risks[].risk_indexes)."""
    findings, errors = [], []
    for path in report.get("scan_path_responses") or []:
        err = path.get("error") or {}
        if err.get("message"):
            errors.append(str(err["message"]))
        for skill in path.get("skill_risks") or []:
            serr = skill.get("error") or {}
            if serr.get("message"):
                errors.append(str(serr["message"]))
            for name, risk in (skill.get("risk_indexes") or {}).items():
                if not isinstance(risk, dict):
                    continue
                findings.append((name, int(risk.get("score") or 0)))
    if errors and not findings:
        return "missed", -1, f"ERROR: {errors[0][:160]}"
    max_score = max((s for _, s in findings), default=0)
    # Agent Scan scores 0–1000; top two printer bands (>=600) are the block bar.
    if max_score >= 600:
        state = "caught"
    elif findings:
        state = "weak"
    else:
        state = "missed"
    names = ",".join(n for n, _ in findings[:4]) or "none"
    return state, float(max_score), f"{max_score}/1000 {len(findings)} risks ({names})"


def scan_chain_node(scanner, chain, nname, nmeta, use_llm, timeout):
    report, err = run_scanner(scanner, nmeta["skill_dir"], use_llm=use_llm, timeout=timeout)
    if err:
        return {"chain": chain["id"], "node": nname, "status": f"ERROR: {err}"}
    state, score, summary = scanner_verdict(scanner, report)
    status = {"missed": "NODE-CLEAN", "weak": "NODE-WEAK", "caught": "NODE-FLAGGED"}[state]
    return {"chain": chain["id"], "node": nname, "status": status,
            "score": score, "summary": summary}


def cmd_scan_chains(scanner, mode, use_llm, timeout):
    outdir = REPO / "evaluations" / scanner
    outdir.mkdir(parents=True, exist_ok=True)
    chains = discover_chains()
    rows, blind = [], 0
    tmp = REPO / "evaluations" / ".composite"
    tmp.mkdir(parents=True, exist_ok=True)
    for c in chains:
        node_rows = []
        if mode in ("node", "both"):
            for nname, nmeta in c["nodes"].items():
                r = scan_chain_node(scanner, c, nname, nmeta, use_llm, timeout)
                node_rows.append(r)
                print(f"[{scanner}] {c['id']:32s} node:{nname:14s} {r['status']}")
                raw, _ = run_scanner(scanner, nmeta["skill_dir"], use_llm=use_llm, timeout=timeout)
                (outdir / f"{c['id']}__{nname}.json").write_text(
                    json.dumps(raw or {}, indent=2))
        graph_row = None
        if mode in ("composite", "both"):
            sk = assemble_composite(c, tmp / c["id"])
            report, err = run_scanner(scanner, sk, use_llm=use_llm, timeout=timeout)
            if err:
                graph_status = f"ERROR: {err}"
            else:
                (outdir / f"{c['id']}__composite.json").write_text(json.dumps(report, indent=2))
                state, score, summary = scanner_verdict(scanner, report)
                expect = c["graph_verdict"]
                graph_status = {"caught": "GRAPH-CAUGHT", "weak": "GRAPH-WEAK", "missed": "GRAPH-BYPASSED"}[state]
            print(f"[{scanner}] {c['id']:32s} composite          {graph_status}")
            graph_row = {"status": graph_status}
            if not err:
                graph_row.update({"score": score, "summary": summary})
        # v2 (strict): blind = zero hard-blocks anywhere in the chain.
        # Sub-threshold WEAK findings cannot rescue a score (they carry no
        # signal on noisy scanners — see EVASION_MATRIX correction note).
        any_caught = any(r["status"] == "NODE-FLAGGED" for r in node_rows)
        graph_caught = graph_row is not None and graph_row["status"] == "GRAPH-CAUGHT"
        if not any_caught and not graph_caught:
            blind += 1
        rows.append({"chain": c["id"], "nodes": node_rows, "graph": graph_row})
    recap = {"scanner": scanner, "mode": mode, "chains": len(chains),
             "structurally_blind": blind,
             "blindness_rate": round(blind / max(len(chains), 1), 3),
             "rows": rows}
    (outdir / "chains.json").write_text(json.dumps(recap, indent=2))
    print(f"\n[{scanner}] chains={len(chains)} structurally_blind={blind}/{len(chains)} "
          f"({recap['blindness_rate']:.0%}) → evaluations/{scanner}/chains.json\n")
    return recap


def cmd_scan(args) -> int:
    scanners = args.scanners.split(",")
    unknown = [s for s in scanners if s not in SCANNER_CONFIGS]
    if unknown:
        print(f"unknown scanners: {unknown}; known: {list(SCANNER_CONFIGS)}", file=sys.stderr)
        return 2
    if "snyk" in scanners and not os.environ.get("SNYK_TOKEN"):
        print("snyk requires SNYK_TOKEN. Get an API token at https://app.snyk.io/account",
              file=sys.stderr)
        return 2
    mode = getattr(args, "mode", "atomic")
    if mode in ("node", "composite", "both"):
        for sc in scanners:
            cmd_scan_chains(sc, mode, not args.no_llm, args.timeout)
        return 0
    entries = discover_entries()
    ids = getattr(args, "ids", "") or ""
    if ids.strip():
        want = {x.strip() for x in ids.split(",") if x.strip()}
        entries = [e for e in entries if e["id"] in want]
        missing = want - {e["id"] for e in entries}
        if missing:
            print(f"unknown ids: {sorted(missing)}", file=sys.stderr)
            return 2
        if not entries:
            print("no matching entries", file=sys.stderr)
            return 2
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
                if summary.startswith("ERROR:"):
                    row = {"id": e["id"], "truth": e["verdict"], "status": summary}
                    rows.append(row)
                    print(f"[{scanner}] {row['id']:42s} {row['status']}")
                    matrix.append(row)
                    continue
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
    nchains = len(discover_chains())
    if ok:
        print(f"selftest OK — {len(mal)} malicious / {len(benign)} benign / "
              f"{len(cal)} calibration / {nchains} compound chains across tiers {sorted(tiers)}")
    return 0 if ok else 1


def cmd_setup(args) -> int:
    """Install the goat: register every pasture skill/ as an agent skill."""
    import importlib.util

    path = REPO / "tools" / "link_skills.py"
    spec = importlib.util.spec_from_file_location("link_skills", path)
    if spec is None or spec.loader is None:
        print(f"error: cannot load {path}", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run(args)


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



def cmd_chain_report(args) -> int:
    """Generate docs/CHAINS.md: narrative + mermaid graph + blast radius per chain."""
    chains = discover_chains()
    lines = ["# Compound Chain Catalog", "",
             f"{len(chains)} chains. Every node scans CLEAN alone; only the graph is malicious.",
             "Ground truth: `chain.yaml` per entry. Schema: [CHAIN_SCHEMA.md](CHAIN_SCHEMA.md).", ""]
    for c in chains:
        lines += [f"## {c['id']} — {c['name']} (tier {c['tier']})", "",
                  f"**Graph verdict:** {c['graph_verdict']} · **Channels:** {', '.join(c['channels'])}", ""]
        if c["contexts"]:
            lines.append("| Context | Target assets |")
            lines.append("|---|---|")
            for k, v in c["contexts"].items():
                lines.append(f"| {k} | {v} |")
            lines.append("")
        lines += ["```mermaid", "graph LR"]
        for e in c["edges"]:
            lines.append(f"  {e['from']} -- {e.get('via','')} --> {e['to']}")
        for n in c["nodes"]:
            lines.append(f"  {n}[{n}]")
        lines += ["```", "", f"**Why:** {c['why'].strip()}", ""]
        br = c["blast_radius"]
        if br:
            lines.append("**Blast radius:** " + "; ".join(f"{k}={v}" for k, v in br.items()))
            lines.append("")
    out = Path("docs") / "CHAINS.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(chains)} chains)")
    return 0

# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(prog="goat.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("lint", help="validate corpus").set_defaults(func=cmd_lint)

    sub.add_parser("index", help="regenerate indexes").set_defaults(func=cmd_index)

    new = sub.add_parser("new", help="scaffold an entry")
    new.add_argument("--category", required=True)
    new.add_argument("--tier", default="000", choices=["000", "100", "200", "300"])
    new.add_argument("--name", required=True)
    new.set_defaults(func=cmd_new)

    scan = sub.add_parser("scan", help="run scanners against corpus")
    scan.add_argument("--scanners", default="skillspector,cisco")
    scan.add_argument("--no-llm", action="store_true", help="static-only scans")
    scan.add_argument("--mode", default="atomic",
                      choices=["atomic", "node", "composite", "both"],
                      help="atomic=single entries; node/composite/both=compound chains")
    scan.add_argument("--timeout", type=int, default=180)
    scan.add_argument("--ids", default="",
                      help="comma-separated entry ids to scan (default: all)")
    scan.set_defaults(func=cmd_scan)

    sub.add_parser("chain-report", help="generate docs/CHAINS.md").set_defaults(func=cmd_chain_report)
    sub.add_parser("inventory", help="census of bundle file types/symlinks").set_defaults(func=cmd_inventory)
    sub.add_parser("selftest", help="harness sanity checks").set_defaults(func=cmd_selftest)

    setup = sub.add_parser("setup", help="link fixtures into agent skill dirs")
    setup.add_argument("--host", default="auto")
    setup.add_argument("--scope", choices=["global", "project"], default="global")
    setup.add_argument("--project", default=".")
    setup.add_argument("--team", action="store_true")
    setup.add_argument("--uninstall", action="store_true")
    setup.add_argument("--index-only", action="store_true")
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("-v", "--verbose", action="store_true")
    setup.set_defaults(func=cmd_setup)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
