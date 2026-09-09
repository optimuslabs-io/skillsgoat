"""Blind staging strips the answer key from scanner input.

Run pytest in a local or cloud sandbox (docs/SAFETY.md). These tests do not
execute pasture scripts.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import goat.main as goat
from goat.blind import (
    BlindLeakError,
    alias_for,
    assert_blind_tree,
    cheater_verdict,
    copy_entry_blind,
    new_salt,
    new_token,
    open_session,
    plaintext_canary_hits,
    provenance_fields,
    strip_canaries_bytes,
)


def _write_entry(root: Path, folder: str, *, verdict: str, canary: str) -> Path:
    entry = root / folder
    skill = entry / "skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {folder}\n---\n\n# demo\n\n<!-- {canary} -->\n"
    )
    expected = {
        "id": folder,
        "name": folder,
        "verdict": verdict,
        "categories": ["calibration"] if verdict == "malicious" else ["benign"],
        "canary": canary,
        "why": "test" if verdict == "malicious" else "",
    }
    if verdict == "benign":
        expected.pop("why", None)
        expected["severity"] = None
    else:
        expected["severity"] = "low"
    (entry / "expected.yaml").write_text(yaml.safe_dump(expected))
    return entry


def test_strip_canaries_neutral_uuid():
    token = "00000000-0000-4000-8000-000000000000"
    raw = b"keep me <!-- GOAT-CANARY-benign-git-hooks-legit --> and GOAT-CHAIN-c12"
    out = strip_canaries_bytes(raw, token)
    assert b"GOAT-CANARY" not in out
    assert b"GOAT-CHAIN" not in out
    assert token.encode() in out
    assert b"keep me" in out


def test_alias_is_hex_and_stable():
    salt = "ab" * 16
    a = alias_for("atomic:000-base64-obvious", salt)
    assert a == alias_for("atomic:000-base64-obvious", salt)
    assert a != alias_for("atomic:000-git-hooks-legit", salt)
    assert all(c in "0123456789abcdef" for c in a)
    assert "obvious" not in a
    assert "benign" not in a


def test_copy_drops_expected_yaml(tmp_path: Path):
    src = _write_entry(
        tmp_path / "src",
        "000-git-hooks-legit",
        verdict="benign",
        canary="GOAT-CANARY-benign-git-hooks-legit",
    )
    dest = tmp_path / "dest" / "aaaa"
    token = new_token()
    copy_entry_blind(src, dest, token)
    assert not (dest / "expected.yaml").exists()
    assert (dest / "skill" / "SKILL.md").is_file()
    text = (dest / "skill" / "SKILL.md").read_text()
    assert "GOAT-CANARY" not in text
    assert token in text
    assert_blind_tree(dest)


def test_assert_rejects_sibling_key(tmp_path: Path):
    staged = tmp_path / "leak"
    (staged / "skill").mkdir(parents=True)
    (staged / "skill" / "SKILL.md").write_text("ok\n")
    (staged / "expected.yaml").write_text("verdict: malicious\n")
    with pytest.raises(BlindLeakError, match="expected.yaml"):
        assert_blind_tree(staged)


def test_assert_rejects_live_canary(tmp_path: Path):
    staged = tmp_path / "leak"
    skill = staged / "skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("<!-- GOAT-CANARY-000-base64-obvious -->\n")
    with pytest.raises(BlindLeakError, match="live canary"):
        assert_blind_tree(staged)


def test_cheater_reads_source_and_fails_blind(tmp_path: Path):
    src = _write_entry(
        tmp_path / "src",
        "000-base64-obvious",
        verdict="malicious",
        canary="GOAT-CANARY-000-base64-obvious",
    )
    assert cheater_verdict(src / "skill") == "malicious"
    dest = tmp_path / "blind" / alias_for("atomic:000-base64-obvious", "salt")
    copy_entry_blind(src, dest, new_token())
    assert cheater_verdict(dest / "skill") is None


def test_cheater_benign_canary_on_source(tmp_path: Path):
    src = _write_entry(
        tmp_path / "src",
        "000-git-hooks-legit",
        verdict="benign",
        canary="GOAT-CANARY-benign-git-hooks-legit",
    )
    assert cheater_verdict(src / "skill") == "benign"
    dest = tmp_path / "blind" / "deadbeefdeadbeef"
    copy_entry_blind(src, dest, new_token())
    assert cheater_verdict(dest / "skill") is None


def test_real_collection_source_leaks_and_blind_does_not(tmp_path: Path):
    entries = goat.discover_entries()
    mal = next(e for e in entries if e["verdict"] == "malicious")
    ben = next(e for e in entries if e["verdict"] == "benign")
    assert cheater_verdict(mal["skill_dir"]) == "malicious"
    assert cheater_verdict(ben["skill_dir"]) == "benign"

    session = open_session(
        [mal, ben],
        None,
        root=tmp_path / "pair",
        owned=True,
        pasture=goat.PASTURE,
    )
    try:
        for e in (mal, ben):
            staged = session.atomic[e["id"]]
            assert cheater_verdict(staged) is None
            assert e["id"] not in staged.parts
            assert "benign" not in staged.parts
            assert "pasture" not in [p.lower() for p in staged.parts]
            assert_blind_tree(staged.parent, pasture=goat.PASTURE)
            assert staged.resolve() != e["skill_dir"].resolve()
    finally:
        session.cleanup()


def test_full_collection_blind_stage_has_no_answer_key(tmp_path: Path):
    """CI leak gate: every atomic + chain stages without expected.yaml / canaries."""
    entries = goat.discover_entries()
    chains = goat.discover_chains()
    assert entries and chains
    session = open_session(
        entries,
        chains,
        root=tmp_path / "blind",
        owned=False,
        pasture=goat.PASTURE,
        token=new_token(),
        salt=new_salt(),
    )
    assert len(session.atomic) == len(entries)
    assert len(session.chains) == len(chains)
    for e in entries:
        skill = session.atomic[e["id"]]
        assert cheater_verdict(skill) is None
        assert not (skill.parent / "expected.yaml").exists()
        assert e["entry_dir"].name not in skill.parts
    for c in chains:
        meta = session.chains[c["id"]]
        assert not (meta["entry"] / "chain.yaml").exists()
        for nname, ndir in meta["nodes"].items():
            assert ndir.is_dir()
            blob = "\n".join(
                p.read_text(errors="replace")
                for p in ndir.rglob("*")
                if p.is_file() and not p.is_symlink()
            )
            assert "GOAT-CANARY" not in blob
            assert "GOAT-CHAIN" not in blob
            assert c["entry_dir"].name not in ndir.parts


def test_provenance_fields_always_present(tmp_path: Path):
    empty = provenance_fields(None)
    assert empty["blind"] is False
    assert empty["blind_salt"] is None
    assert empty["canary_token"] is None
    keys = set(empty)
    session = open_session(None, None, root=tmp_path / "p", owned=False)
    filled = provenance_fields(session)
    assert filled["blind"] is True
    assert filled["canary_token"]
    assert filled["blind_salt"]
    assert keys <= set(filled)


def test_symlink_canary_is_rewritten(tmp_path: Path):
    src = tmp_path / "src" / "000-x"
    skill = src / "skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: x\n---\n# x\n")
    (skill / "notes.md").write_text("<!-- GOAT-CANARY-000-x -->\n")
    (skill / "alias.md").symlink_to("notes.md")
    dest = tmp_path / "dest" / "abcd"
    token = new_token()
    copy_entry_blind(src, dest, token)
    assert_blind_tree(dest)
    text = (dest / "skill" / "notes.md").read_text()
    assert token in text
    assert "GOAT-CANARY" not in text


def test_assert_unreadable_fails_closed(tmp_path: Path):
    staged = tmp_path / "s"
    skill = staged / "skill"
    skill.mkdir(parents=True)
    f = skill / "SKILL.md"
    f.write_text("ok\n")
    f.chmod(0)
    try:
        with pytest.raises(BlindLeakError, match="unreadable"):
            assert_blind_tree(staged)
    finally:
        f.chmod(0o644)


def test_packed_only_canary_is_not_plaintext(tmp_path: Path):
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("no marker here\n")
    (skill / "pack.zip").write_bytes(b"PK\x03\x04 GOAT-CANARY-000-x hidden")
    assert plaintext_canary_hits(skill, "GOAT-CANARY-000-x") == []
    (skill / "SKILL.md").write_text("<!-- GOAT-CANARY-000-x -->\n")
    assert plaintext_canary_hits(skill, "GOAT-CANARY-000-x")
