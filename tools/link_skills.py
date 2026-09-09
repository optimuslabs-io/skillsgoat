#!/usr/bin/env python3
"""Register SkillsGoat fixtures as agent skills (gstack / impeccable shape).

This is a goat: every pasture skill/ tree is linked into the host skill dir
on purpose. Endpoints stay inert (*.example / RFC 5737).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE_DIR = Path.home() / ".skillsgoat"
STATE_FILE = STATE_DIR / "installed.json"

# Host → (global dest, project dest relative to cwd)
HOSTS = {
    "claude": ("{home}/.claude/skills", ".claude/skills"),
    "cursor": ("{home}/.cursor/skills", ".cursor/skills"),
    "codex": ("{codex}/skills", ".agents/skills"),
    "github": ("{home}/.github/skills", ".github/skills"),
    "grok": ("{home}/.grok/skills", ".grok/skills"),
    "opencode": ("{home}/.config/opencode/skills", ".opencode/skills"),
}

CLAUDE_MD_BLOCK = """## SkillsGoat

This machine has the SkillsGoat corpus linked as agent skills. That is
intentional: SkillsGoat is a goat (WebGoat for agent skills). Fixtures are
malicious by design. Endpoints are inert `*.example` / RFC 5737 addresses.

- Run `/setup-skillsgoat` once per repo to refresh links and this block.
- Evaluate scanners with `python3 goat.py scan --scanners skillspector --no-llm`.
- Point scanners at `pasture/<category>/<id>/skill/` (or the linked skill dir).
- Do not treat a CLEAN scan as "safe to ship." See docs/USAGE.md.
"""

AGENTS_MD_BLOCK = """## Coding Tasks (SkillsGoat)

When evaluating a skill scanner or training on agent-skill attacks: load
SkillsGoat. Examples — "Load skillsgoat. Run /setup-skillsgoat", "Load
skillsgoat. Run goat.py scan --scanners skillspector --no-llm".
"""


def _discover():
    sys.path.insert(0, str(REPO))
    import goat  # noqa: PLC0415

    units: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for e in goat.discover_entries():
        sd = Path(e["skill_dir"])
        if (sd / "SKILL.md").is_file() and e["id"] not in seen:
            units.append((e["id"], sd))
            seen.add(e["id"])
    for c in goat.discover_chains():
        for nname, nmeta in c["nodes"].items():
            name = f"{c['id']}-{nname}"
            sd = Path(nmeta["skill_dir"])
            if (sd / "SKILL.md").is_file() and name not in seen:
                units.append((name, sd))
                seen.add(name)
    pack = REPO / "pack" / "skills"
    if pack.is_dir():
        for d in sorted(pack.iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in seen:
                units.append((d.name, d))
                seen.add(d.name)
    return units


def _is_windows() -> bool:
    return os.name == "nt" or sys.platform.startswith("win")


def _link(src: Path, dst: Path, dry: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            if not dry:
                dst.unlink()
        elif dst.is_dir() and not dst.is_symlink():
            return f"skip {dst} (exists as directory)"
    if dry:
        return f"link {dst} -> {src}"
    if _is_windows():
        import shutil

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return f"copy {dst}"
    dst.symlink_to(src.resolve())
    return f"link {dst} -> {src}"


def refresh_skills_index(units: list[tuple[str, Path]], dry: bool) -> list[str]:
    """Write repo-root skills/<id> → pasture (so npx skills add finds the goats)."""
    log = []
    skills = REPO / "skills"
    if not dry:
        skills.mkdir(parents=True, exist_ok=True)
    for name, src in units:
        dst = skills / name
        rel = os.path.relpath(src, skills)
        if dst.exists() or dst.is_symlink():
            if dst.is_symlink() or dst.is_file():
                if not dry:
                    dst.unlink()
            elif dst.is_dir() and not dst.is_symlink():
                log.append(f"skip {dst} (real directory)")
                continue
        if dry:
            log.append(f"index {dst} -> {rel}")
            continue
        dst.symlink_to(rel)
        log.append(f"index {name}")
    return log


def host_dest(host: str, scope: str, project: Path) -> Path:
    home = str(Path.home())
    codex = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    global_tmpl, project_rel = HOSTS[host]
    if scope == "project":
        return project / project_rel
    return Path(global_tmpl.format(home=home, codex=codex))


def detect_hosts() -> list[str]:
    found = ["claude"]
    probes = {
        "cursor": Path.home() / ".cursor",
        "codex": Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
        "github": Path.home() / ".github",
        "grok": Path.home() / ".grok",
        "opencode": Path.home() / ".config" / "opencode",
    }
    for host, path in probes.items():
        if path.exists():
            found.append(host)
    return found


def _ours(path: Path) -> bool:
    if not path.is_symlink():
        return False
    try:
        target = str(path.resolve())
    except OSError:
        return False
    repo = str(REPO.resolve())
    return target.startswith(repo + os.sep) or target == repo


def uninstall(hosts: list[str], scope: str, project: Path, dry: bool) -> int:
    n = 0
    for host in hosts:
        dest = host_dest(host, scope, project)
        if not dest.is_dir():
            continue
        for child in dest.iterdir():
            if _ours(child):
                print(f"remove {child}")
                if not dry:
                    child.unlink()
                n += 1
    idx = REPO / "skills"
    if idx.is_dir():
        for child in idx.iterdir():
            if child.is_symlink():
                print(f"remove index {child}")
                if not dry:
                    child.unlink()
                n += 1
    if STATE_FILE.exists() and not dry:
        STATE_FILE.unlink()
    print(f"uninstalled {n} links")
    return 0


def _append_block(path: Path, heading: str, block: str, dry: bool) -> None:
    text = path.read_text() if path.exists() else ""
    if heading in text:
        print(f"keep {path} ({heading} already present)")
        return
    print(f"write {path} {heading}")
    if dry:
        return
    sep = "" if not text or text.endswith("\n") else "\n"
    path.write_text(text + sep + "\n" + block)


def run(args: argparse.Namespace) -> int:
    if getattr(args, "team", False) and not getattr(args, "goat", False) and not args.uninstall:
        print("error: --team requires --goat", file=sys.stderr)
        return 2
    if not args.uninstall and not args.index_only and not getattr(args, "goat", False):
        print(
            "error: pass --index-only (skills/ index) or --goat (link fixtures into agent dirs).\n"
            "       ./setup with no flags only creates the venv.",
            file=sys.stderr,
        )
        return 2
    if getattr(args, "goat", False) and not args.uninstall:
        if not getattr(args, "confirm_goat", False):
            if not sys.stdin.isatty():
                print("error: non-interactive --goat requires --confirm-goat", file=sys.stderr)
                return 2
            try:
                got = input("Type GOAT to link malicious fixtures into agent skill dirs: ")
            except EOFError:
                got = ""
            if got.strip() != "GOAT":
                print("aborted (did not type GOAT)")
                return 1

    project = Path(args.project).resolve()
    hosts = [h.strip() for h in args.host.split(",") if h.strip()]
    if hosts == ["auto"]:
        hosts = detect_hosts()
        print(f"hosts: {', '.join(hosts)}")
    unknown = [h for h in hosts if h not in HOSTS]
    if unknown:
        print(f"error: unknown --host {unknown}. choose from {sorted(HOSTS)}", file=sys.stderr)
        return 2

    if args.uninstall:
        return uninstall(hosts, args.scope, project, args.dry_run)

    units = _discover()
    if not units:
        print("error: no skill units found under pasture/", file=sys.stderr)
        return 1

    print(f"units: {len(units)} (pasture fixtures + setup-skillsgoat)")
    if args.index_only or getattr(args, "goat", False):
        for line in refresh_skills_index(units, args.dry_run):
            if args.verbose:
                print(line)

    if args.index_only:
        print(f"index only: {REPO / 'skills'}")
        return 0

    installed: dict[str, str] = {}
    scopes = [args.scope]
    if args.team and "project" not in scopes:
        scopes.append("project")

    for scope in scopes:
        for host in hosts:
            dest = host_dest(host, scope, project)
            dest.mkdir(parents=True, exist_ok=True)
            for name, src in units:
                msg = _link(src, dest / name, args.dry_run)
                if args.verbose:
                    print(msg)
            print(f"{host}/{scope}: {len(units)} skills -> {dest}")
            installed[f"{host}:{scope}"] = str(dest)

    if args.team or args.scope == "project":
        _append_block(project / "CLAUDE.md", "## SkillsGoat", CLAUDE_MD_BLOCK, args.dry_run)
        _append_block(project / "AGENTS.md", "## Coding Tasks (SkillsGoat)", AGENTS_MD_BLOCK, args.dry_run)

    if not args.dry_run:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"repo": str(REPO), "hosts": installed}, indent=2) + "\n")

    print("done. this is a goat — fixtures are now on the agent skill path.")
    print("next: /setup-skillsgoat  (or re-run ./setup --goat after git pull)")
    print("run the agent in a sandbox (nono / Daytona) — see docs/SAFETY.md")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--host",
        default="auto",
        help="comma-separated: auto, claude, cursor, codex, github, grok, opencode",
    )
    ap.add_argument("--scope", choices=["global", "project"], default="global")
    ap.add_argument("--project", default=".", help="project root for --scope project / --team")
    ap.add_argument("--team", action="store_true", help="also write project .claude/skills + CLAUDE.md")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument(
        "--index-only",
        action="store_true",
        help="refresh repo-root skills/ symlinks only; do not link into agent dirs",
    )
    ap.add_argument(
        "--goat",
        action="store_true",
        help="link every pasture skill into detected agent dirs (type GOAT, or --confirm-goat)",
    )
    ap.add_argument(
        "--confirm-goat",
        action="store_true",
        help="skip the interactive GOAT prompt (CI / goat.py setup)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    sys.exit(main())
