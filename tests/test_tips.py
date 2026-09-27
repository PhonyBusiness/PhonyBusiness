"""Every scenario red flag has its own tip, and names survive the comma-joined round trip."""

from backend.scenarios import SCENARIOS
from backend.tips import FALLBACK_TIPS, TIP_BANK, get_tips

ALL_FLAGS = [flag for scenario in SCENARIOS for flag in scenario["red_flags"]]


def test_red_flags_are_unique_and_comma_free():
    # The agent receives and returns flags as one comma-separated string.
    assert len(ALL_FLAGS) == len(set(ALL_FLAGS)) == 42
    assert [flag for flag in ALL_FLAGS if "," in flag] == []


def test_every_red_flag_has_its_own_tip():
    assert [flag for flag in ALL_FLAGS if flag not in TIP_BANK] == []
    assert set(TIP_BANK) - set(ALL_FLAGS) == set()


def test_tips_have_do_and_dont():
    for flag, tip in TIP_BANK.items():
        assert list(tip) == ["do", "dont"], flag
        assert tip["do"] and tip["dont"].startswith("Don't"), flag


def test_each_scenario_gets_its_three_tips_not_the_fallback():
    for scenario in SCENARIOS:
        tips = get_tips(scenario["red_flags"])
        assert [tip["label"] for tip in tips] == scenario["red_flags"], scenario["name"]


def test_unknown_flags_fall_back():
    assert get_tips(["Not a real flag"]) == FALLBACK_TIPS
