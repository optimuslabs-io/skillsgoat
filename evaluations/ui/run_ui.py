#!/usr/bin/env python3
"""UI-first scanner harness via agent-browser.

Probe a vendor page (no corpus upload) or record evidence for one entry.
Do not submit pasture/ fixtures to scanners that publish public reports
until PROTOCOL.md says the feed is private.

  python evaluations/ui/run_ui.py probe metano
  python evaluations/ui/run_ui.py zip 200-vibe-coded-plugin
"""
from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="open vendor UI, snapshot, no upload")
    p.add_argument("scanner")

    z = sub.add_parser("zip", help="zip an entry's skill/ for folder/plugin upload")
    z.add_argument("entry_id")

    args = ap.parse_args()
    if args.cmd == "probe":
        return cmd_probe(args.scanner)
    if args.cmd == "zip":
        zip_skill(args.entry_id)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
