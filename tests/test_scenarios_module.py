"""Format checks for the MVP scenario configs in backend/scenarios.py."""

from backend.scenarios import SCENARIOS, get_scenario, list_scenarios

KEYS = ["name", "display_name", "persona", "ask", "red_flags", "caller_display_name"]


def test_every_scenario_has_exactly_the_agreed_keys_in_order():
    for scenario in SCENARIOS:
        assert list(scenario) == KEYS, scenario["name"]


def test_fields_are_non_empty_strings():
    for scenario in SCENARIOS:
        for key in KEYS:
            if key != "red_flags":
                assert isinstance(scenario[key], str) and scenario[key], (scenario["name"], key)


def test_each_scenario_has_three_red_flags():
    for scenario in SCENARIOS:
        flags = scenario["red_flags"]
        assert len(flags) == 3 and all(isinstance(f, str) and f for f in flags), scenario["name"]


def test_names_are_unique():
    names = [scenario["name"] for scenario in SCENARIOS]
    assert len(names) == len(set(names))


def test_lookup_and_spoiler_free_listing():
    assert get_scenario("benefits_imposter")["caller_display_name"] == "Federal Benefits Office"
    assert get_scenario("unknown") is None
    for item in list_scenarios():
        assert set(item) == {"name", "display_name"}
