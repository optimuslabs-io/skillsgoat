"""goat scan is static-only unless --llm is passed."""

from __future__ import annotations

import pytest

import goat.main as goat


def test_scan_default_is_static():
    ns = goat._build_parser().parse_args(["scan"])
    assert ns.llm is False
    assert goat._scan_use_llm(ns) is False


def test_scan_llm_opt_in():
    ns = goat._build_parser().parse_args(["scan", "--llm"])
    assert ns.llm is True
    assert goat._scan_use_llm(ns) is True


def test_scan_no_llm_still_accepted():
    ns = goat._build_parser().parse_args(["scan", "--no-llm"])
    assert goat._scan_use_llm(ns) is False


def test_scan_llm_and_no_llm_mutex():
    with pytest.raises(SystemExit) as exc:
        goat._build_parser().parse_args(["scan", "--llm", "--no-llm"])
    assert exc.value.code == 2
