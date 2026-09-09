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
skill/ directory. `goat scan` defaults to --blind: hashed fixture dirs,
canaries replaced with a neutral UUID, expected.yaml never in scanner
input. Lint still checks the canary in source. Publish scores only from
--blind runs. Plugin-distribution entries use skill/ as a marketplace
or IDE pack (Vercel skills.sh, ClawHub, Cursor plugin, or fake native
Claude/Codex/Copilot/Grok paths), not a lone SKILL.md.
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
import tempfile
from pathlib import Path

from goat.blind import (
    BlindLeakError,
    BlindSession,
    assert_blind_tree,
    open_session,
    plaintext_canary_hits,
    provenance_fields,
)

try:
    import yaml
except ImportError:  # pragma: no cover
    print("error: PyYAML required.  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parents[2]
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
                "canary_packed": bool(data.get("canary_packed", False)),
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
            "canary_packed": bool(d.get("canary_packed", False)),
            "why": d.get("why", ""),
            "entry_dir": entry_dir,
        })
    return chains


def assemble_composite(chain: dict, dest: Path, node_skill_dirs: dict | None = None,
                       label: str | None = None) -> Path:
    """Copy all nodes into one scannable bundle (real copies, not symlinks)."""
    sk = dest / "skill"
    if sk.exists():
        shutil.rmtree(sk)
    sk.mkdir(parents=True)
    display = label or chain["id"]
    parts = ["---", f"name: {display}-composite",
             "description: >",
             f"  Whole-graph composite of SkillsGoat chain {display}.",
             "---", "", f"# {display}", ""]
    for nname, nmeta in chain["nodes"].items():
        src = (node_skill_dirs or {}).get(nname) or nmeta["skill_dir"]
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


# ---------------------------------------------------------------- lint / safety

_URL_RE = re.compile(r"https?://[^\s\"'<>\\)`\]]+", re.I)
_HOME_RE = re.compile(r"(?:/Users/|/home/)")
_PYC_FIXTURE = (
    PASTURE / "hidden-artifact-packing" / "300-bytecode-poisoning"
    / "skill" / "scripts" / "utils.cpython-314.pyc"
)
_SKIP_LINT_SUFFIXES = {
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".zip",
    ".docx", ".dat", ".pdf", ".so", ".dylib",
}


def decode_smuggled(text: str) -> str:
    """Undo Unicode Tags, drop variation selectors / ZWSP so hidden URLs surface."""
    chars: list[str] = []
    for ch in text:
        o = ord(ch)
        if 0xE0020 <= o <= 0xE007E:
            chars.append(chr(o - 0xE0000))
        elif 0xE0000 <= o <= 0xE001F:
            continue
        elif 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF:
            continue
        else:
            chars.append(ch)
    s = "".join(chars)
    for z in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        s = s.replace(z, "")
    return s


def _hostname_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if host.startswith("[") and "]" in host:
        host = host[1:host.index("]")]
    elif host.count(":") == 1:
        host = host.split(":")[0]
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if re.fullmatch(r"192\.0\.2\.\d+", host):
        return True
    if re.fullmatch(r"198\.51\.100\.\d+", host):
        return True
    if re.fullmatch(r"203\.0\.113\.\d+", host):
        return True
    if host in {"example.com", "example.net", "example.org"}:
        return True
    if host.endswith(".example.com") or host.endswith(".example.net") or host.endswith(".example.org"):
        return True
    if host == "example" or host.endswith(".example"):
        return True
    return False


def _urls_disallowed(text: str) -> list[str]:
    from urllib.parse import urlparse

    bad = []
    for raw in _URL_RE.findall(text):
        raw = raw.rstrip(".,;:)]}>\"'")
        try:
            host = urlparse(raw).hostname or ""
        except ValueError:
            bad.append(raw)
            continue
        if not host or not _hostname_allowed(host):
            bad.append(raw)
    return bad


def sanitize_paths(obj, repo_root: Path):
    """Replace local absolute paths so committed eval JSON cannot dox a machine."""
    repo = str(Path(repo_root).resolve())
    home = str(Path.home())

    def clean_str(s: str) -> str:
        if repo:
            s = s.replace(repo, "<REPO>")
        if home:
            s = s.replace(home, "<HOME>")
        s = re.sub(r"/Users/[^/\s\"']+", "<HOME>", s)
        s = re.sub(r"/home/[^/\s\"']+", "<HOME>", s)
        return s

    if isinstance(obj, dict):
        return {
            clean_str(k) if isinstance(k, str) else k: sanitize_paths(v, repo_root)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [sanitize_paths(v, repo_root) for v in obj]
    if isinstance(obj, str):
        return clean_str(obj)
    return obj


def _dump_json(path: Path, obj, raw_paths: bool = False) -> None:
    if not raw_paths:
        obj = sanitize_paths(obj, REPO)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def _lint_safety(problems: list[str]) -> None:
    """URL allowlist, decoded unicode, symlink policy, home paths, bytecode file."""
    repo_res = str(REPO.resolve())
    if not _PYC_FIXTURE.is_file():
        problems.append(
            f"{_PYC_FIXTURE.relative_to(REPO)}: bytecode fixture missing "
            "(run python3 tools/gen_binaries.py; do not make clean first)"
        )

    for p in PASTURE.rglob("*"):
        rel = str(p.relative_to(REPO))
        if p.is_symlink():
            target = os.readlink(p)
            if target.startswith("/") or target.startswith("~") or "$HOME" in target:
                problems.append(f"{rel}: absolute/home symlink -> {target}")
                continue
            resolved = (p.parent / target).resolve()
            if not str(resolved).startswith(repo_res + os.sep) and str(resolved) != repo_res:
                problems.append(f"{rel}: symlink escapes repo -> {target}")
            continue
        if not p.is_file() or p.suffix.lower() in _SKIP_LINT_SUFFIXES:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        if _HOME_RE.search(text):
            problems.append(f"{rel}: committed home-directory path")
        for url in _urls_disallowed(text) + _urls_disallowed(decode_smuggled(text)):
            problems.append(f"{rel}: live/non-inert URL {url}")

    eval_root = REPO / "evaluations"
    if eval_root.is_dir():
        for p in eval_root.rglob("*"):
            if not p.is_file() or p.suffix.lower() in _SKIP_LINT_SUFFIXES:
                continue
            try:
                data = p.read_bytes()
            except OSError:
                continue
            if b"\0" in data[:8192]:
                continue
            text = data.decode("utf-8", errors="replace")
            if _HOME_RE.search(text):
                problems.append(f"{p.relative_to(REPO)}: committed home-directory path")


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
        # canary must be plaintext-greppable so --blind can actually strip it
        if e["canary"]:
            if e.get("canary_packed"):
                blob = "\n".join(read_skill_files(e["skill_dir"]).values())
                if e["canary"] not in blob:
                    problems.append(
                        f"{where}: canary_packed set but canary {e['canary']} not found in skill files"
                    )
            else:
                try:
                    hits = plaintext_canary_hits(e["skill_dir"], e["canary"])
                except BlindLeakError as exc:
                    problems.append(f"{where}: {exc}")
                else:
                    if not hits:
                        problems.append(
                            f"{where}: canary {e['canary']} is not plaintext-greppable in skill/ "
                            "(zip/pyc-only would survive goat scan --blind). "
                            "Embed it in a text file or set canary_packed: true"
                        )
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
        joined_hits = []
        blob: list[str] = []
        packed_ok = c.get("canary_packed")
        for nname, nmeta in c["nodes"].items():
            sd = nmeta["skill_dir"]
            if not (sd / "SKILL.md").is_file():
                problems.append(f"{where}: node {nname} missing skill/SKILL.md")
                continue
            try:
                joined_hits.extend(plaintext_canary_hits(sd, c["canary"]) if c.get("canary") else [])
            except BlindLeakError as exc:
                problems.append(f"{where}: {exc}")
            if packed_ok:
                for f in sd.rglob("*"):
                    if f.is_file() and not f.is_symlink():
                        try:
                            blob.append(f.read_text(errors="replace"))
                        except Exception:
                            pass
        if c["canary"] and not packed_ok and not joined_hits:
            problems.append(
                f"{where}: chain canary {c['canary']} is not plaintext-greppable in any node "
                "(set canary_packed: true to exempt a packed-only canary)"
            )
        if c["canary"] and packed_ok:
            joined = "\n".join(blob)
            if c["canary"] not in joined:
                problems.append(f"{where}: canary_packed set but chain canary not found in any node")
        for e in c["edges"]:
            if e.get("from") not in c["nodes"] or e.get("to") not in c["nodes"]:
                problems.append(f"{where}: edge references unknown node: {e}")
            elif not e.get("via"):
                problems.append(f"{where}: edge missing 'via': {e}")

    _lint_safety(problems)

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
    "nova": {
        "cmd": ["novarun", "scan"],
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


def scanner_version(scanner: str) -> str:
    cfg = SCANNER_CONFIGS.get(scanner) or {}
    exe_name = (cfg.get("cmd") or [scanner])[0]
    exe = resolve_exe(exe_name)
    if not exe:
        return "unknown"
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        line = (proc.stdout or proc.stderr).strip().splitlines()
        return (line[0] if line else "unknown")[:160]
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _report_provenance(recap: dict) -> list[str]:
    return [
        f"- scanned_at: {recap.get('scanned_at')}",
        f"- llm_enabled: {recap.get('llm_enabled')}",
        f"- scanner_version: {recap.get('scanner_version', 'unknown')}",
        f"- blind: {recap.get('blind')}",
        f"- canary_token: {recap.get('canary_token')}",
        f"- blind_salt: {recap.get('blind_salt')}",
    ]


def scan_chain_node(scanner, chain, nname, skill_dir, use_llm, timeout):
    report, err = run_scanner(scanner, skill_dir, use_llm=use_llm, timeout=timeout)
    if err:
        return {"chain": chain["id"], "node": nname, "status": f"ERROR: {err}"}
    state, score, summary = scanner_verdict(scanner, report)
    status = {"missed": "NODE-CLEAN", "weak": "NODE-WEAK", "caught": "NODE-FLAGGED"}[state]
    return {"chain": chain["id"], "node": nname, "status": status,
            "score": score, "summary": summary}


def cmd_scan_chains(scanner, mode, use_llm, timeout, raw_paths: bool = False,
                    session: BlindSession | None = None):
    outdir = REPO / "evaluations" / scanner
    outdir.mkdir(parents=True, exist_ok=True)
    chains = discover_chains()
    rows, structurally_blind = [], 0
    tmp = REPO / "evaluations" / ".composite"
    tmp.mkdir(parents=True, exist_ok=True)
    for c in chains:
        node_rows = []
        if mode in ("node", "both"):
            for nname, nmeta in c["nodes"].items():
                skill_dir = session.chain_node_dir(c["id"], nname) if session else nmeta["skill_dir"]
                r = scan_chain_node(scanner, c, nname, skill_dir, use_llm, timeout)
                node_rows.append(r)
                print(f"[{scanner}] {c['id']:32s} node:{nname:14s} {r['status']}")
                raw, _ = run_scanner(scanner, skill_dir, use_llm=use_llm, timeout=timeout)
                _dump_json(outdir / f"{c['id']}__{nname}.json", raw or {}, raw_paths)
        graph_row = None
        if mode in ("composite", "both"):
            if session:
                dest = session.composite_dest(c["id"])
                alias = dest.name
                sk = assemble_composite(
                    c, dest,
                    node_skill_dirs=session.chains[c["id"]]["nodes"],
                    label=alias,
                )
                assert_blind_tree(dest, pasture=PASTURE)
            else:
                sk = assemble_composite(c, tmp / c["id"])
            report, err = run_scanner(scanner, sk, use_llm=use_llm, timeout=timeout)
            if err:
                graph_status = f"ERROR: {err}"
            else:
                _dump_json(outdir / f"{c['id']}__composite.json", report, raw_paths)
                state, score, summary = scanner_verdict(scanner, report)
                graph_status = {"caught": "GRAPH-CAUGHT", "weak": "GRAPH-WEAK", "missed": "GRAPH-BYPASSED"}[state]
            print(f"[{scanner}] {c['id']:32s} composite          {graph_status}")
            graph_row = {"status": graph_status}
            if not err:
                graph_row.update({"score": score, "summary": summary})
        # v2 (strict): structurally_blind = zero hard-blocks anywhere in the chain.
        # Sub-threshold WEAK findings cannot rescue a score (they carry no
        # signal on noisy scanners — see EVASION_MATRIX correction note).
        any_caught = any(r["status"] == "NODE-FLAGGED" for r in node_rows)
        graph_caught = graph_row is not None and graph_row["status"] == "GRAPH-CAUGHT"
        if not any_caught and not graph_caught:
            structurally_blind += 1
        rows.append({"chain": c["id"], "nodes": node_rows, "graph": graph_row})
    recap = {
        "scanner": scanner, "mode": mode,
        "scanned_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "scanner_version": scanner_version(scanner),
        "llm_enabled": use_llm,
        "chains": len(chains),
        "structurally_blind": structurally_blind,
        "blindness_rate": round(structurally_blind / max(len(chains), 1), 3),
        "rows": rows,
    }
    recap.update(provenance_fields(session))
    _dump_json(outdir / "chains.json", recap, raw_paths)
    print(f"\n[{scanner}] chains={len(chains)} structurally_blind={structurally_blind}/{len(chains)} "
          f"({recap['blindness_rate']:.0%}) → evaluations/{scanner}/chains.json\n")
    return recap


def _prepare_blind(entries, chains, args) -> BlindSession:
    keep = (getattr(args, "keep_blind", "") or "").strip()
    if keep:
        root = Path(keep).resolve()
        root.mkdir(parents=True, exist_ok=True)
        owned = False
    else:
        root = Path(tempfile.mkdtemp(prefix="goat-blind-"))
        owned = True
    print(f"[blind] staging under {root}")
    try:
        session = open_session(entries, chains, root=root, owned=owned, pasture=PASTURE)
    except Exception:
        if owned:
            shutil.rmtree(root, ignore_errors=True)
        raise
    print(f"[blind] canaries → {session.token}; "
          f"{len(session.atomic)} atomics, {len(session.chains)} chains")
    return session


def cmd_scan(args) -> int:
    assert_only = getattr(args, "assert_only", False)
    use_blind = getattr(args, "blind", True) or assert_only
    if assert_only:
        try:
            session = _prepare_blind(discover_entries(), discover_chains(), args)
        except BlindLeakError as exc:
            print(f"BLIND FAIL: {exc}", file=sys.stderr)
            return 1
        try:
            print("blind OK — scanner input has no expected.yaml, chain.yaml, "
                  "or live GOAT-CANARY / GOAT-CHAIN; fixture dir names are hashed")
        finally:
            session.cleanup()
        return 0
    scanners = args.scanners.split(",")
    unknown = [s for s in scanners if s not in SCANNER_CONFIGS]
    if unknown:
        print(f"unknown scanners: {unknown}; known: {list(SCANNER_CONFIGS)}", file=sys.stderr)
        return 2
    if "snyk" in scanners and not os.environ.get("SNYK_TOKEN"):
        print("snyk requires SNYK_TOKEN. Get an API token at https://app.snyk.io/account",
              file=sys.stderr)
        return 2
    if not use_blind:
        print("warning: --no-blind scans the live pasture tree; canaries and "
              "fixture names leak the answer key. Do not publish these numbers.",
              file=sys.stderr)
    mode = getattr(args, "mode", "atomic")
    session = None
    try:
        if mode in ("node", "composite", "both"):
            if use_blind:
                try:
                    session = _prepare_blind(None, discover_chains(), args)
                except BlindLeakError as exc:
                    print(f"BLIND FAIL: {exc}", file=sys.stderr)
                    return 1
            raw_paths = getattr(args, "raw_paths", False)
            for sc in scanners:
                cmd_scan_chains(sc, mode, not args.no_llm, args.timeout, raw_paths,
                                session=session)
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
        if use_blind:
            try:
                session = _prepare_blind(entries, None, args)
            except BlindLeakError as exc:
                print(f"BLIND FAIL: {exc}", file=sys.stderr)
                return 1
        rows, misses = [], []
        for scanner in scanners:
            outdir = REPO / "evaluations" / scanner
            outdir.mkdir(parents=True, exist_ok=True)
            matrix = []
            detected = weak = fp = fn = tn = 0
            for e in entries:
                skill_dir = session.atomic[e["id"]] if session else e["skill_dir"]
                report, err = run_scanner(scanner, skill_dir, use_llm=not args.no_llm,
                                          timeout=args.timeout)
                if err:
                    row = {"id": e["id"], "truth": e["verdict"], "status": f"ERROR: {err}"}
                else:
                    _dump_json(outdir / f"{e['id']}.json", report, getattr(args, "raw_paths", False))
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
                            fn += 1
                            misses.append(e["id"])
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
                "scanner_version": scanner_version(scanner),
                "scanned_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                "total": total, "caught": detected, "weak_flagged": weak,
                "bypassed": fn, "false_positives": fp, "clean_benign": tn,
                "malicious_recall_strict": round(detected / max(detected + weak + fn, 1), 3),
                "malicious_detection_any": round((detected + weak) / max(detected + weak + fn, 1), 3),
                "benign_fp_rate": round(fp / max(fp + tn, 1), 3),
                "rows": matrix,
            }
            recap.update(provenance_fields(session))
            _dump_json(outdir / "matrix.json", recap, getattr(args, "raw_paths", False))
            md = [f"# Evaluation matrix — {scanner}\n"]
            md.extend(_report_provenance(recap))
            md += [
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
    finally:
        if session is not None:
            session.cleanup()


# ---------------------------------------------------------------- selftest

def cmd_selftest(args) -> int:
    ok = True
    entries = discover_entries()
    cal = [e for e in entries if "calibration" in e["categories"]]
    if len(cal) < 5:
        print(f"selftest FAIL: calibration set too small ({len(cal)})")
        ok = False
    benign = [e for e in entries if e["verdict"] == "benign"]
    mal = [e for e in entries if e["verdict"] == "malicious"]
    if not benign or not mal:
        print("selftest FAIL: need both verdict classes")
        ok = False
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
    out = REPO / "docs" / "CHAINS.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(chains)} chains)")
    return 0

# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(prog="goat", description=__doc__,
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
    scan.add_argument("--raw-paths", action="store_true",
                      help="do not sanitize absolute paths in written eval JSON")
    scan.add_argument("--blind", dest="blind", action="store_true", default=True,
                      help="stage hashed dirs and strip canaries (default; required to publish scores)")
    scan.add_argument("--no-blind", dest="blind", action="store_false",
                      help="scan the live pasture tree (leaks the answer key; do not publish)")
    scan.add_argument("--keep-blind", default="",
                      help="write the blind staging tree here instead of a temp dir")
    scan.add_argument("--assert-only", action="store_true",
                      help="stage a blind tree, leak-assert, and exit (no scanners)")
    scan.set_defaults(func=cmd_scan)

    sub.add_parser("chain-report", help="generate docs/CHAINS.md").set_defaults(func=cmd_chain_report)
    sub.add_parser("inventory", help="census of bundle file types/symlinks").set_defaults(func=cmd_inventory)
    sub.add_parser("selftest", help="harness sanity checks").set_defaults(func=cmd_selftest)

    setup = sub.add_parser("setup", help="link fixtures into agent skill dirs (requires --goat)")
    setup.add_argument("--host", default="auto")
    setup.add_argument("--scope", choices=["global", "project"], default="global")
    setup.add_argument("--project", default=".")
    setup.add_argument("--team", action="store_true")
    setup.add_argument("--uninstall", action="store_true")
    setup.add_argument("--index-only", action="store_true")
    setup.add_argument("--goat", action="store_true",
                       help="link every pasture skill into agent dirs")
    setup.add_argument("--confirm-goat", action="store_true",
                       help="skip the interactive GOAT prompt (CI)")
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("-v", "--verbose", action="store_true")
    setup.add_argument("--real-home", action="store_true",
                       help="link into the real $HOME (default: SKILLSGOAT_SANDBOX or .sandbox-home)")
    setup.set_defaults(func=cmd_setup)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
