"""Shape checks for the scenario configs in content/scenarios."""

import json
import re
from pathlib import Path

import pytest

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "content" / "scenarios"
SCENARIO_FILES = sorted(SCENARIO_DIR.glob("*.json"))

REQUIRED_FIELDS = {
    "id", "version", "family", "title", "contact_method", "caller_id", "persona",
    "pretext", "story", "ask", "red_flags", "stages", "fake_credentials",
    "disclosure_triggers", "pass_signals", "difficulty", "sources",
}
STAGES = {"hook", "build_trust", "ask", "pressure", "close"}
DIFFICULTIES = {"easy", "medium", "hard"}
RED_FLAG_IDS = {
    "unsolicited_call", "authority_claim", "threat", "urgency",
    "sensitive_info_request", "unusual_payment", "secrecy",
    "remote_access_request", "emotional_manipulation", "fishing_for_details",
    "verification_code_request", "too_good_to_be_true", "upfront_fee",
}
FICTIONAL_NUMBER = re.compile(r"\(\d{3}\) 555-01\d{2}")


def test_mvp_scenarios_exist():
    assert {"benefits_imposter", "tech_support", "family_emergency"} <= {
        path.stem for path in SCENARIO_FILES
    }


def test_caller_numbers_are_unique():
    numbers = [json.loads(path.read_text())["caller_id"]["number"] for path in SCENARIO_FILES]
    assert len(numbers) == len(set(numbers))


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda path: path.stem)
def test_scenario_shape(path):
    scenario = json.loads(path.read_text())

    assert set(scenario) == REQUIRED_FIELDS
    assert scenario["id"] == path.stem
    assert scenario["contact_method"] == "phone"
    assert set(scenario["stages"]) == STAGES
    assert set(scenario["difficulty"]) == DIFFICULTIES

    flag_ids = [flag["id"] for flag in scenario["red_flags"]]
    assert len(flag_ids) == len(set(flag_ids))
    assert set(flag_ids) <= RED_FLAG_IDS
    assert all(flag["cue"] for flag in scenario["red_flags"])

    assert scenario["disclosure_triggers"] and scenario["pass_signals"]
    assert FICTIONAL_NUMBER.fullmatch(scenario["caller_id"]["number"])
    assert FICTIONAL_NUMBER.fullmatch(scenario["fake_credentials"]["callback_number"])
    assert scenario["sources"]
    assert all(re.match(r"https://(www\.)?consumer\.ftc\.gov/", url) for url in scenario["sources"])
