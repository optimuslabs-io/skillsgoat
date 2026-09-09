"""Detonation HOME override.

Pasture scripts use `$HOME` / `~` (for example `cat >> ~/.zshrc`). Network C2
is inert; those writes are not. Honor SKILLSGOAT_SANDBOX so `./setup --goat`
and a live agent do not dirty the researcher's real home.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_SANDBOX = "SKILLSGOAT_SANDBOX"
DEFAULT_DIRNAME = ".sandbox-home"


def sandbox_home(repo: Path, *, real_home: bool = False) -> Path:
    """Directory used as $HOME for goat links and (when exported) detonation."""
    if real_home:
        return Path.home()
    override = os.environ.get(ENV_SANDBOX, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(repo) / DEFAULT_DIRNAME).resolve()


def sandbox_banner(home: Path, *, real_home: bool) -> str:
    if real_home:
        return (
            "WARNING: --real-home installs into your actual $HOME "
            f"({home}). Pasture scripts that append to ~/.zshrc will "
            "touch this machine. Prefer SKILLSGOAT_SANDBOX instead."
        )
    return (
        f"SKILLSGOAT_SANDBOX={home}\n"
        "Links go here, not your real $HOME.\n"
        "A live agent still uses the process HOME. Detonate with:\n"
        f'  mkdir -p "{home}/tmp"\n'
        f'  HOME="{home}" TMPDIR="{home}/tmp" <your-agent>\n'
        "Pass --real-home only if you intend to write the real profile."
    )
