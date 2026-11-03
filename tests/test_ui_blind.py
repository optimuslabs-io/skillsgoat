"""UI scanners are staged blind and scored with the same tally as `goat scan`.

Run pytest in a local or cloud sandbox (docs/SAFETY.md). These tests stage
fixtures into a temp dir and zip them; they do not execute pasture scripts.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

import goat.main as goat

RUN_UI = Path(goat.REPO) / "evaluations" / "ui" / "run_ui.py"
MALICIOUS = "000-plain-curl-bash"
BENIGN = "ssh-config-reader"


@pytest.fixture(scope="module")
def run_ui():
    spec = importlib.util.spec_from_file_location("run_ui", RUN_UI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def stage(tmp_path, run_ui):
    out = tmp_path / "stage"
    rc = run_ui.cmd_stage("anthropic", "tier1", f"{MALICIOUS},{BENIGN}", str(out), force=False)
    assert rc == 0
    return out


def _fill(stage: Path, by_id: dict[str, str]) -> None:
    key = json.loads((stage / "key.json").read_text())
    path = stage / "results.csv"
    rows = list(csv.DictReader(path.open()))
    for r in rows:
        r["status"] = by_id.get(key["aliases"][r["alias"]], "")
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def test_upload_bundle_leaks_nothing(stage):
    key = json.loads((stage / "key.json").read_text())
    upload = stage / "upload"
    assert not (upload / "key.json").exists()
    assert sorted(key["aliases"].values()) == sorted([MALICIOUS, BENIGN])
    for p in upload.iterdir():
        assert MALICIOUS not in p.name and BENIGN not in p.name
    zips = sorted(upload.glob("*.zip"))
    assert len(zips) == 2
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert not any(n.endswith("expected.yaml") for n in names)
            for n in names:
                blob = zf.read(n)
                assert b"GOAT-CANARY" not in blob and b"GOAT-CHAIN" not in blob
    sheet = (stage / "results.csv").read_text()
    assert MALICIOUS not in sheet and BENIGN not in sheet


def test_stage_refuses_to_overwrite_key(stage, run_ui):
    rc = run_ui.cmd_stage("anthropic", "tier1", MALICIOUS, str(stage), force=False)
    assert rc == 2


def test_score_round_trip(stage, run_ui, tmp_path):
    _fill(stage, {MALICIOUS: "fail", BENIGN: "warn"})
    out = tmp_path / "eval"
    rc = run_ui.cmd_score("anthropic", str(stage), None, None, "test-build", False, str(out))
    assert rc == 0
    m = json.loads((out / "matrix.json").read_text())
    assert (m["caught"], m["false_positives"], m["bypassed"], m["clean_benign"]) == (1, 1, 0, 0)
    assert m["blind"] is True and m["verdict_source"] == "ui"
    assert m["scanner_version"] == "test-build" and m["pending"] == 0
    status = {r["id"]: r["status"] for r in m["rows"]}
    assert status == {MALICIOUS: "CAUGHT", BENIGN: "FP-WEAK"}
    assert (out / "report.md").read_text().startswith("# Evaluation matrix — anthropic")


def test_score_refuses_half_filled_sheet_unless_partial(stage, run_ui, tmp_path):
    _fill(stage, {MALICIOUS: "pass"})
    out = tmp_path / "eval"
    assert run_ui.cmd_score("anthropic", str(stage), None, None, None, False, str(out)) == 2
    assert not (out / "matrix.json").exists()
    assert run_ui.cmd_score("anthropic", str(stage), None, None, None, True, str(out)) == 0
    m = json.loads((out / "matrix.json").read_text())
    assert (m["scored"], m["pending"], m["bypassed"]) == (1, 1, 1)


def test_score_refuses_unknown_verdict_words(stage, run_ui, tmp_path):
    _fill(stage, {MALICIOUS: "fail", BENIGN: "looks fine"})
    assert run_ui.cmd_score("anthropic", str(stage), None, None, None, False,
                            str(tmp_path / "eval")) == 2


def test_score_needs_a_verdict_map(tmp_path, run_ui):
    assert run_ui.cmd_score("air", str(tmp_path), None, None, None, False,
                            str(tmp_path / "eval")) == 2


def test_tally_matches_scan_semantics():
    t = goat.MatrixTally("x")
    mal = {"id": "m", "verdict": "malicious", "categories": ["c"], "lifecycle_stage": "execution"}
    ben = {"id": "b", "verdict": "benign", "attack_vs_posture": "posture"}
    t.add(mal, "weak", 50.0, "s")
    t.add(ben, "caught", 100.0, "s")
    t.error({"id": "e", "verdict": "benign"}, "ERROR: timeout")
    r = t.recap(llm_enabled=False, version="v", provenance={"blind": True})
    assert (r["total"], r["weak_flagged"], r["false_positives"]) == (3, 1, 1)
    assert r["posture_false_positives"] == 1 and r["attack_false_positives"] == 0
    assert r["by_category"] == {"c": {"caught": 0, "weak": 1, "missed": 0}}
    assert r["by_lifecycle_stage"] == {"execution": {"caught": 0, "weak": 1, "missed": 0}}
