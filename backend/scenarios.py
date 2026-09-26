"""Static MVP scenario configs.
"""

SCENARIOS = [
    {
        "name": "benefits_imposter",
        "display_name": "Benefits imposter",
        "persona": "Officer Daniels from the Federal Benefits Office",
        "ask": "verify your Social Security number to avoid losing your benefits",
        "red_flags": [
            "Urgency or threat of losing benefits",
            "Requests a Social Security number",
            "Caller ID spoofing a government agency",
        ],
        "caller_display_name": "Federal Benefits Office",
    },
    {
        "name": "tech_support",
        "display_name": "Tech support",
        "persona": "a support technician from SecureTech Support",
        "ask": "remote into your computer to fix a virus that was detected",
        "red_flags": [
            "Unsolicited call about a virus",
            "Requests remote desktop access",
            "Pressure to act immediately",
        ],
        "caller_display_name": "SecureTech Support",
    },
    {
        "name": "family_emergency",
        "display_name": "Family emergency",
        "persona": "your grandson, in trouble and scared",
        "ask": "send bail money right away, before he can call anyone else",
        "red_flags": [
            "Claims to be a family member in distress",
            "Asks for secrecy",
            "Requests money via an unusual payment method",
        ],
        "caller_display_name": "Unknown Caller",
    },
]

_SCENARIOS_BY_NAME = {s["name"]: s for s in SCENARIOS}


def get_scenario(name: str) -> dict | None:
    return _SCENARIOS_BY_NAME.get(name)


def list_scenarios() -> list[dict]:
    """Public, spoiler-free listing for the frontend's scenario dropdown."""
    return [{"name": s["name"], "display_name": s["display_name"]} for s in SCENARIOS]
