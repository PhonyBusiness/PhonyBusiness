"""Tip bank: do/don't guidance for each red flag, sourced from FTC consumer guidance.

Keyed by the exact red_flags text used in scenarios.py.
"""

TIP_BANK = {
    "Urgency or threat of losing benefits": {
        "do": "Hang up and contact the agency directly using a number from its official website.",
        "dont": "Don't let urgency or fear of losing benefits rush you into acting on the call.",
    },
    "Requests a Social Security number": {
        "do": "Only share your Social Security number through channels you initiated yourself.",
        "dont": "Don't give out your Social Security number to anyone who calls you unprompted.",
    },
    "Caller ID spoofing a government agency": {
        "do": "Remember caller ID can be faked; verify by calling the agency back on a known number.",
        "dont": "Don't trust a call just because the caller ID shows a government agency's name.",
    },
    "Unsolicited call about a virus": {
        "do": "Hang up and run a scan using security software you installed yourself, if concerned.",
        "dont": "Don't believe an unsolicited caller who claims to have detected a virus on your computer.",
    },
    "Requests remote desktop access": {
        "do": "Only grant remote access to your computer to support you contacted yourself.",
        "dont": "Don't install remote access software for someone who called you out of the blue.",
    },
    "Pressure to act immediately": {
        "do": "Take time to verify independently before acting, no matter how urgent it sounds.",
        "dont": "Don't let pressure to act immediately stop you from thinking it through.",
    },
    "Claims to be a family member in distress": {
        "do": "Hang up and call that family member directly on their known number to confirm.",
        "dont": "Don't assume a caller is who they claim to be, even if they sound like a relative.",
    },
    "Asks for secrecy": {
        "do": "Talk to another trusted family member before doing anything the caller asked.",
        "dont": "Don't keep a call secret just because the caller asked you not to tell anyone.",
    },
    "Requests money via an unusual payment method": {
        "do": "Treat requests for gift cards, wire transfers, or crypto as a major warning sign.",
        "dont": "Don't send money via gift cards, wire transfer, or crypto based on a phone call alone.",
    },
}


FALLBACK_TIPS = [
    {
        "label": "General advice",
        "do": "Hang up, then contact the person or organization directly using a number or method you already know and trust, not one the caller gave you.",
        "dont": "Don't share personal details, codes, or payment information on a call you didn't start.",
    },
]


def get_tips(flags: list[str] | None) -> list[dict]:
    """Look up tips for the given flags. Falls back to general guidance if none match."""
    matched = [TIP_BANK[flag] | {"label": flag} for flag in (flags or []) if flag in TIP_BANK]
    return matched or FALLBACK_TIPS


def format_tips(result: str, flags: list[str] | None) -> str:
    """Structured plain-text reply for the agent to read aloud in coach mode."""
    lines = [f"RESULT: {result}", "TIPS:"]
    for tip in get_tips(flags):
        lines.append(f"•  Red flag: {tip['label']}")
        lines.append(f"  Do: {tip['do']}")
        lines.append(f"  Don't: {tip['dont']}")
    return "\n".join(lines)
