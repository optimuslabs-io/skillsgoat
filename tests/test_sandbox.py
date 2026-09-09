"""SKILLSGOAT_SANDBOX / HOME override."""

from __future__ import annotations

from pathlib import Path

from goat.sandbox import sandbox_home


def test_sandbox_default_is_repo_dir(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SKILLSGOAT_SANDBOX", raising=False)
    home = sandbox_home(tmp_path, real_home=False)
    assert home == (tmp_path / ".sandbox-home").resolve()
    assert home != Path.home()


def test_sandbox_env_override(tmp_path: Path, monkeypatch):
    dest = tmp_path / "jail"
    dest.mkdir()
    monkeypatch.setenv("SKILLSGOAT_SANDBOX", str(dest))
    assert sandbox_home(tmp_path, real_home=False) == dest.resolve()


def test_real_home_flag(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SKILLSGOAT_SANDBOX", str(tmp_path / "jail"))
    assert sandbox_home(tmp_path, real_home=True) == Path.home()
