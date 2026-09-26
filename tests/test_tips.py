"""Checks that every scenario red flag has a do and don't tip."""

from backend.scenarios import SCENARIOS
from backend.tips import TIP_BANK


def test_red_flags_are_unique_across_scenarios():
    flags = [flag for s in SCENARIOS for flag in s["red_flags"]]
    assert len(flags) == len(set(flags)) == len(TIP_BANK) == 42


def test_every_red_flag_has_a_tip():
    missing = [flag for s in SCENARIOS for flag in s["red_flags"] if flag not in TIP_BANK]
    assert missing == []


def test_every_tip_is_used_by_a_scenario():
    used = {flag for s in SCENARIOS for flag in s["red_flags"]}
    assert set(TIP_BANK) - used == set()


def test_tips_have_exactly_do_and_dont():
    for flag, tip in TIP_BANK.items():
        assert list(tip) == ["do", "dont"], flag
        assert tip["do"] and tip["dont"], flag
        assert tip["dont"].startswith("Don't"), flag
