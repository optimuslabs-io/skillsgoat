"""Blind staging: strip answer-key leaks before a scanner sees the corpus.

`goat lint` still requires GOAT-CANARY-* / GOAT-CHAIN-* in the *source* tree.
`goat scan --blind` copies each fixture into a hashed directory, replaces
those canaries with one neutral UUID, and refuses to hand a scanner any tree
that still contains `expected.yaml`, `chain.yaml`, or a live canary string.

Without this, a scanner can score the corpus by grepping the canary or
reading the sibling key — no analysis required.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yaml

BANNED_NAMES = frozenset({"expected.yaml", "chain.yaml", ".goat-meta", "aibom.yaml"})
CANARY_RE = re.compile(r"GOAT-(?:CANARY|CHAIN)-[A-Za-z0-9_.-]+")
CANARY_BYTES_RE = re.compile(br"GOAT-(?:CANARY|CHAIN)-[A-Za-z0-9_.-]+")
PACKED_SUFFIXES = frozenset({
    ".zip", ".docx", ".pyc", ".dat", ".png", ".jpg", ".jpeg", ".gif",
    ".webp", ".woff", ".pdf", ".so", ".dylib",
})


class BlindLeakError(RuntimeError):
    """Scanner input still contains ground truth or a live canary."""


@dataclass
class BlindSession:
    root: Path
    token: str
    salt: str
    atomic: dict[str, Path] = field(default_factory=dict)
    chains: dict[str, dict] = field(default_factory=dict)
    owned: bool = False

    def recap(self) -> dict:
        return provenance_fields(self)

    def chain_node_dir(self, chain_id: str, nname: str) -> Path:
        return self.chains[chain_id]["nodes"][nname]

    def composite_dest(self, chain_id: str) -> Path:
        return self.root / "composite" / alias_for(f"composite:{chain_id}", self.salt)

    def cleanup(self) -> None:
        if self.owned and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)


def provenance_fields(session: BlindSession | None) -> dict:
    """Always-present keys so a matrix cannot omit whether the run was blind."""
    if session is None:
        return {"blind": False, "blind_salt": None, "canary_token": None}
    return {
        "blind": True,
        "blind_salt": session.salt,
        "canary_token": session.token,
        "staged_atomics": len(session.atomic),
        "staged_chains": len(session.chains),
    }


def new_token() -> str:
    """One UUID used for every canary in a scan run (does not encode verdict)."""
    return str(uuid.uuid4())


def new_salt() -> str:
    return secrets.token_hex(16)


def alias_for(key: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}\0{key}".encode()).hexdigest()[:16]


def strip_canaries_bytes(data: bytes, token: str) -> bytes:
    repl = token.encode("utf-8")
    return CANARY_BYTES_RE.sub(repl, data)


def _ignore_banned(_dir: str, names: list[str]) -> list[str]:
    return [n for n in names if n in BANNED_NAMES]


def _resolve_inside(path: Path, root: Path) -> Path:
    """Resolve path; fail closed if it cannot be read or leaves root."""
    root_r = root.resolve()
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise BlindLeakError(f"unreadable path {path}: {exc}") from exc
    try:
        resolved.relative_to(root_r)
    except ValueError as exc:
        raise BlindLeakError(f"symlink escapes staged tree: {path} -> {resolved}") from exc
    return resolved


def copy_entry_blind(src_entry: Path, dest_entry: Path, token: str) -> None:
    """Copy a fixture directory, dropping answer-key files and rewriting canaries."""
    if dest_entry.exists():
        shutil.rmtree(dest_entry)
    shutil.copytree(src_entry, dest_entry, symlinks=True, ignore=_ignore_banned)
    dest_root = dest_entry.resolve()
    seen: set[str] = set()
    for path in dest_entry.rglob("*"):
        if not path.is_symlink() and not path.is_file():
            continue
        if path.is_symlink():
            target = Path(os.readlink(path))
            if target.is_absolute():
                raise BlindLeakError(f"absolute symlink in staged tree: {path}")
            file_to_edit = _resolve_inside(path, dest_root)
            if not file_to_edit.is_file():
                raise BlindLeakError(f"dangling symlink in staged tree: {path} -> {target}")
        else:
            file_to_edit = path
        key = str(file_to_edit)
        if key in seen:
            continue
        seen.add(key)
        try:
            data = file_to_edit.read_bytes()
        except OSError as exc:
            raise BlindLeakError(f"unreadable staged file {file_to_edit}: {exc}") from exc
        rewritten = strip_canaries_bytes(data, token)
        if rewritten != data:
            file_to_edit.write_bytes(rewritten)


def assert_blind_tree(staged_entry: Path, pasture: Path | None = None) -> None:
    """Fail if the staged tree still contains ground truth or a live canary."""
    staged = staged_entry.resolve()
    if not staged.is_dir():
        raise BlindLeakError(f"staged entry missing: {staged_entry}")
    if pasture is not None:
        try:
            staged.relative_to(Path(pasture).resolve())
        except ValueError:
            pass
        else:
            raise BlindLeakError(f"scanner input still under pasture/: {staged}")

    for path in staged.rglob("*"):
        if path.name in BANNED_NAMES:
            raise BlindLeakError(f"{path.name} leaked into scanner input ({path})")
        if path.is_symlink():
            target = Path(os.readlink(path))
            if target.is_absolute() or (
                ".." in target.parts and _symlink_escapes(path, staged)
            ):
                raise BlindLeakError(f"symlink escapes staged tree: {path} -> {target}")
            check = _resolve_inside(path, staged)
            if not check.is_file():
                raise BlindLeakError(f"dangling symlink in staged tree: {path} -> {target}")
        elif path.is_file():
            check = path
        else:
            continue
        try:
            data = check.read_bytes()
        except OSError as exc:
            raise BlindLeakError(f"unreadable staged file {check}: {exc}") from exc
        if b"GOAT-CANARY" in data or b"GOAT-CHAIN" in data:
            raise BlindLeakError(f"live canary leaked in {check}")


def os_readlink(path: Path) -> str:
    return os.readlink(path)


def _symlink_escapes(link: Path, root: Path) -> bool:
    try:
        resolved = (link.parent / os.readlink(link)).resolve()
        resolved.relative_to(root.resolve())
        return False
    except (ValueError, OSError):
        return True


def plaintext_canary_hits(skill_dir: Path, canary: str) -> list[Path]:
    """Files where `canary` is greppable as UTF-8 bytes, excluding packed artifacts.

    Blind stripping is plaintext-only. A canary that lives only inside a zip/pyc
    would survive staging; lint must reject that unless the entry opts out.
    """
    if not canary or not skill_dir.is_dir():
        return []
    needle = canary.encode("utf-8")
    hits: list[Path] = []
    for path in skill_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() in PACKED_SUFFIXES:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise BlindLeakError(f"unreadable skill file {path}: {exc}") from exc
        if b"\0" in data[:8192]:
            continue
        if needle in data:
            hits.append(path)
    return hits


def stage_atomics(
    entries: list[dict],
    root: Path,
    token: str,
    salt: str,
    pasture: Path | None = None,
) -> dict[str, Path]:
    """Stage atomic fixtures. Returns {entry_id: skill_dir to scan}."""
    mapping: dict[str, Path] = {}
    root.mkdir(parents=True, exist_ok=True)
    for e in entries:
        alias = alias_for(f"atomic:{e['id']}", salt)
        dest = root / alias
        copy_entry_blind(e["entry_dir"], dest, token)
        assert_blind_tree(dest, pasture=pasture)
        skill = dest / "skill"
        if not skill.is_dir():
            raise BlindLeakError(f"{e['id']}: staged skill/ missing")
        mapping[e["id"]] = skill
    return mapping


def stage_chains(
    chains: list[dict],
    root: Path,
    token: str,
    salt: str,
    pasture: Path | None = None,
) -> dict[str, dict]:
    """Stage compound chains. Returns {chain_id: {entry, nodes}}."""
    mapping: dict[str, dict] = {}
    root.mkdir(parents=True, exist_ok=True)
    for c in chains:
        alias = alias_for(f"chain:{c['id']}", salt)
        dest = root / alias
        copy_entry_blind(c["entry_dir"], dest, token)
        assert_blind_tree(dest, pasture=pasture)
        nodes = {}
        for nname in c["nodes"]:
            ndir = dest / "nodes" / nname / "skill"
            if not ndir.is_dir():
                raise BlindLeakError(f"{c['id']}: staged node {nname} missing")
            nodes[nname] = ndir
        mapping[c["id"]] = {"entry": dest, "nodes": nodes}
    return mapping


def open_session(
    entries: list[dict] | None,
    chains: list[dict] | None,
    *,
    root: Path,
    owned: bool,
    pasture: Path | None = None,
    token: str | None = None,
    salt: str | None = None,
) -> BlindSession:
    token = token or new_token()
    salt = salt or new_salt()
    session = BlindSession(root=root, token=token, salt=salt, owned=owned)
    if entries:
        session.atomic = stage_atomics(entries, root / "atomic", token, salt, pasture=pasture)
    if chains:
        session.chains = stage_chains(chains, root / "chains", token, salt, pasture=pasture)
    return session


def cheater_verdict(skill_dir: Path) -> str | None:
    """What a scanner scores if it greps the canary or reads the sibling key.

    Used in tests to prove the source tree leaks and the blind tree does not.
    """
    exp = skill_dir.parent / "expected.yaml"
    if exp.is_file():
        data = yaml.safe_load(exp.read_text()) or {}
        v = data.get("verdict")
        if v in ("malicious", "benign"):
            return v
    blob_parts: list[str] = []
    if not skill_dir.is_dir():
        return None
    for path in skill_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            blob_parts.append(path.read_text(errors="replace"))
        except OSError:
            continue
    blob = "\n".join(blob_parts)
    if "GOAT-CANARY-benign" in blob:
        return "benign"
    if "GOAT-CANARY-" in blob or "GOAT-CHAIN-" in blob:
        return "malicious"
    return None
