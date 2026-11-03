#!/usr/bin/env python3
"""UI-first scanner harness via agent-browser.

Probe a vendor page (no collection upload) or record evidence for one entry.
Do not submit pasture/ fixtures to scanners that publish public reports
until PROTOCOL.md says the feed is private.

  python evaluations/ui/run_ui.py probe metano
  python evaluations/ui/run_ui.py zip 200-vibe-coded-plugin
  python evaluations/ui/run_ui.py stage anthropic --sample all
  python evaluations/ui/run_ui.py score anthropic
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DRIVERS = yaml.safe_load((HERE / "drivers.yaml").read_text())
PASTURE = REPO / "pasture"


def agent(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["agent-browser", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def find_entry(eid: str) -> Path:
    for p in PASTURE.glob(f"*/{eid}"):
        if (p / "expected.yaml").exists() or (p / "chain.yaml").exists():
            return p
    # benign twins drop the numeric prefix in the directory name
    for p in PASTURE.glob(f"benign/*{eid}*"):
        if (p / "expected.yaml").exists():
            return p
    for p in PASTURE.rglob("expected.yaml"):
        if yaml.safe_load(p.read_text()).get("id") == eid:
            return p.parent
    raise SystemExit(f"unknown entry {eid}")


def zip_skill(eid: str) -> Path:
    entry = find_entry(eid)
    src = entry / "skill"
    if not src.is_dir():
        raise SystemExit(f"no skill/ under {entry}")
    out_dir = HERE / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{eid}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in src.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(src))
    print(dest)
    return dest


def cmd_probe(scanner: str) -> int:
    cfg = DRIVERS["scanners"].get(scanner)
    if not cfg:
        known = ", ".join(DRIVERS["scanners"])
        print(f"unknown scanner {scanner!r}; known: {known}", file=sys.stderr)
        return 2
    url = cfg["url"]
    out = HERE / "probes" / scanner
    out.mkdir(parents=True, exist_ok=True)
    print(f"open {url}")
    r = agent("open", url, timeout=90)
    if not r.returncode:
        time.sleep(1)
        scan_url = cfg.get("scan_url")
        if scan_url and scan_url != url:
            agent("open", scan_url, timeout=90)
            time.sleep(1)
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return 1
    time.sleep(2)
    agent("wait", "--load", "networkidle", timeout=45)
    snap = agent("snapshot", "-i", timeout=30)
    (out / "snapshot.txt").write_text(snap.stdout or snap.stderr)
    agent("screenshot", str(out / "landing.png"), timeout=30)
    body = agent("eval", "document.body.innerText", timeout=30)
    (out / "body.txt").write_text(body.stdout or "")
    print(f"wrote {out}")
    print((snap.stdout or "")[:2000])
    if cfg.get("public_reports"):
        print(
            f"NOTE: {scanner} may publish reports. Do not upload pasture/ "
            "fixtures until a private toggle is confirmed.",
            file=sys.stderr,
        )
    return 0


# ------------------------------------------------------------ blind stage/score
#
# `zip` above uploads straight from pasture/, so fixture names and canaries
# reach the vendor and results.csv is keyed by entry id. `stage` and `score`
# are the citable path: the vendor sees hashed folder names and stripped
# canaries, the person recording verdicts sees only aliases, and the matrix is
# scored by the same MatrixTally as `goat scan`.

RESULTS_FIELDS = ["alias", "surface", "status", "reported_severity", "findings_count", "notes"]


def _goat():
    sys.path.insert(0, str(REPO / "src"))
    import goat.main as goat  # noqa: PLC0415
    from goat import blind  # noqa: PLC0415
    return goat, blind


def _scanner_cfg(scanner: str) -> dict:
    cfg = DRIVERS["scanners"].get(scanner)
    if not cfg:
        raise SystemExit(f"unknown scanner {scanner!r}; known: {', '.join(DRIVERS['scanners'])}")
    return cfg


def _stage_dir(scanner: str, override: str | None) -> Path:
    return Path(override).resolve() if override else REPO / "evaluations" / scanner / "blind-stage"


def _zip_dir(src: Path, dest: Path) -> None:
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file() and not p.is_symlink():
                zf.write(p, p.relative_to(src))


def cmd_stage(scanner: str, sample: str, ids: str, out: str | None, force: bool) -> int:
    cfg = _scanner_cfg(scanner)
    goat, blind = _goat()
    entries = goat.discover_entries()
    if ids:
        want = {x.strip() for x in ids.split(",") if x.strip()}
    elif sample == "tier1":
        want = set(DRIVERS["tier1"])
    else:
        want = {e["id"] for e in entries}
    entries = [e for e in entries if e["id"] in want]
    missing = want - {e["id"] for e in entries}
    if missing:
        print(f"unknown ids: {sorted(missing)}", file=sys.stderr)
        return 2

    root = _stage_dir(scanner, out)
    if root.exists():
        if not force:
            print(f"{root} exists; its key scores an earlier upload. Pass --force to replace it.",
                  file=sys.stderr)
            return 2
        shutil.rmtree(root)
    session = blind.open_session(entries, None, root=root / "staged", owned=False,
                                 pasture=goat.PASTURE)
    upload = root / "upload"
    upload.mkdir()
    aliases: dict[str, str] = {}
    for e in entries:
        skill = session.atomic[e["id"]]
        alias = skill.parent.name
        aliases[alias] = e["id"]
        _zip_dir(skill, upload / f"{alias}.zip")
        md = skill / "SKILL.md"
        if md.is_file():
            shutil.copy2(md, upload / f"{alias}.SKILL.md")

    # The key maps aliases back to entries. It never goes to the vendor or to
    # whoever records verdicts; keep it outside upload/.
    key = {
        "scanner": scanner,
        "staged_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "sample": "ids" if ids else sample,
        "blind_salt": session.salt,
        "canary_token": session.token,
        "aliases": aliases,
    }
    (root / "key.json").write_text(json.dumps(key, indent=2, sort_keys=True) + "\n")
    surface = cfg.get("default_surface", "directory")
    with (root / "results.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=RESULTS_FIELDS)
        w.writeheader()
        for alias in sorted(aliases):
            w.writerow({"alias": alias, "surface": surface})

    print(f"staged {len(aliases)} entries for {scanner} under {root}")
    print(f"  upload/      {len(aliases)} zips (+ SKILL.md files) — what the vendor gets")
    print("  results.csv  one row per alias; fill `status` with the vendor's verdict word")
    print("  key.json     answer key — keep local, never upload or share with the recorder")
    if cfg.get("public_reports") is not False:
        print(f"WARNING: {scanner} public_reports={cfg.get('public_reports')!r}. Confirm "
              "reports stay private before uploading (PROTOCOL.md).", file=sys.stderr)
    return 0


def cmd_score(scanner: str, stage: str | None, results: str | None, surface: str | None,
              version: str | None, partial: bool, out: str | None) -> int:
    cfg = _scanner_cfg(scanner)
    verdicts = {str(k).lower(): v for k, v in (cfg.get("verdicts") or {}).items()}
    if not verdicts:
        print(f"{scanner} has no `verdicts` map in drivers.yaml; record the vendor's verdict "
              "words there (word: caught|weak|missed) before scoring.", file=sys.stderr)
        return 2
    bad = {k: v for k, v in verdicts.items() if v not in ("caught", "weak", "missed")}
    if bad:
        print(f"verdicts must map to caught|weak|missed: {bad}", file=sys.stderr)
        return 2
    goat, _ = _goat()
    root = _stage_dir(scanner, stage)
    key = json.loads((root / "key.json").read_text())
    aliases: dict[str, str] = key["aliases"]
    surface = surface or cfg.get("default_surface", "directory")

    states: dict[str, tuple[str, str]] = {}
    unknown_words: set[str] = set()
    with Path(results or root / "results.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("surface") or surface) != surface:
                continue
            alias = (row.get("alias") or "").strip()
            if alias not in aliases:
                print(f"results row for unknown alias {alias!r}", file=sys.stderr)
                return 2
            word = (row.get("status") or "").strip().lower()
            if not word:
                continue
            if word not in verdicts and not word.startswith("error"):
                unknown_words.add(word)
                continue
            summary = " ".join(x for x in (word.upper(), row.get("reported_severity") or "",
                                           row.get("notes") or "") if x).strip()
            states[aliases[alias]] = (verdicts.get(word, "error"), summary)
    if unknown_words:
        print(f"verdict words not in drivers.yaml `{scanner}.verdicts`: {sorted(unknown_words)}",
              file=sys.stderr)
        return 2
    pending = sorted(i for i in aliases.values() if i not in states)
    if pending and not partial:
        print(f"{len(pending)} of {len(aliases)} entries have no verdict yet; finish results.csv "
              "or pass --partial (the matrix then says how many were scored).", file=sys.stderr)
        return 2

    tally = goat.MatrixTally(scanner)
    for e in goat.discover_entries():
        if e["id"] not in states:
            continue
        state, summary = states[e["id"]]
        if state == "error":
            tally.error(e, f"ERROR: {summary}")
        else:
            tally.add(e, state, {"caught": 100.0, "weak": 50.0, "missed": 0.0}[state], summary)
    provenance = {
        "blind": True,
        "blind_salt": key["blind_salt"],
        "canary_token": key["canary_token"],
        "staged_atomics": len(aliases),
        "staged_chains": 0,
        "verdict_source": "ui",
        "surface": surface,
        "scored": len(states),
        "pending": len(pending),
    }
    recap = tally.recap(llm_enabled=bool(cfg.get("llm_review")),
                        version=version or str(cfg.get("version") or "unknown"),
                        provenance=provenance)
    outdir = Path(out).resolve() if out else REPO / "evaluations" / scanner
    goat.write_matrix(outdir, recap)
    print(f"[{scanner}] caught={recap['caught']} weak={recap['weak_flagged']} "
          f"bypassed={recap['bypassed']} fp={recap['false_positives']} "
          f"scored={len(states)} pending={len(pending)} → {outdir / 'report.md'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="open vendor UI, snapshot, no upload")
    p.add_argument("scanner")

    z = sub.add_parser("zip", help="zip an entry's skill/ for folder/plugin upload")
    z.add_argument("entry_id")

    s = sub.add_parser("stage", help="blind upload bundle + answer key + results.csv")
    s.add_argument("scanner")
    s.add_argument("--sample", choices=["tier1", "all"], default="tier1")
    s.add_argument("--ids", default="", help="comma-separated entry ids (overrides --sample)")
    s.add_argument("--out", help="stage directory (default evaluations/<scanner>/blind-stage)")
    s.add_argument("--force", action="store_true", help="replace an existing stage and key")

    c = sub.add_parser("score", help="score a filled results.csv into matrix.json/report.md")
    c.add_argument("scanner")
    c.add_argument("--stage", help="stage directory holding key.json")
    c.add_argument("--results", help="results.csv (default <stage>/results.csv)")
    c.add_argument("--surface", help="which surface's rows to score (default from drivers.yaml)")
    c.add_argument("--version", help="vendor build/version seen in the UI")
    c.add_argument("--partial", action="store_true", help="score even if some rows are empty")
    c.add_argument("--out", help="output directory (default evaluations/<scanner>)")

    args = ap.parse_args()
    if args.cmd == "probe":
        return cmd_probe(args.scanner)
    if args.cmd == "zip":
        zip_skill(args.entry_id)
        return 0
    if args.cmd == "stage":
        return cmd_stage(args.scanner, args.sample, args.ids, args.out, args.force)
    if args.cmd == "score":
        return cmd_score(args.scanner, args.stage, args.results, args.surface, args.version,
                         args.partial, args.out)
    return 2


if __name__ == "__main__":
    sys.exit(main())
