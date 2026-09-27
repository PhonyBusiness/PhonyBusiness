"""Static MVP scenario configs.
"""

SCENARIOS = [
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
    {
        "name": "tax_debt",
        "display_name": "Tax debt",
        "persona": "Agent Collins from the Federal Revenue Office",
        "ask": "pay an overdue tax balance with gift cards today to avoid arrest",
        "red_flags": [
            "Threat of arrest over an unpaid tax balance",
            "Demands payment by gift card or wire transfer",
            "Insists you pay during this call",
        ],
        "caller_display_name": "Federal Revenue Office",
    },
    {
        "name": "jury_duty_warrant",
        "display_name": "Jury duty warrant",
        "persona": "Sergeant Brennan from the Marlow County Sheriff's Office",
        "ask": "pay a fine by payment app or cryptocurrency to clear a warrant for missed jury duty",
        "red_flags": [
            "Threat of arrest for missing jury duty",
            "Asks for your date of birth or Social Security number",
            "Demands payment by payment app or cryptocurrency",
        ],
        "caller_display_name": "Marlow County Sheriff",
    },
    {
        "name": "bank_fraud_alert",
        "display_name": "Bank fraud alert",
        "persona": "Emily from the Harborline Bank fraud department",
        "ask": "read back the verification code sent to your phone and move your savings to a safe account",
        "red_flags": [
            "Unexpected call about fraud on your account",
            "Asks for a verification code",
            "Tells you to move your money to protect it",
        ],
        "caller_display_name": "Harborline Bank",
    },
    {
        "name": "order_refund",
        "display_name": "Suspicious order",
        "persona": "Jason from Cartwell customer protection",
        "ask": "read your card number and security code to cancel an order you didn't place",
        "red_flags": [
            "Call about an order you didn't place",
            "Asks for your full card number and security code",
            "Asks you to repay an accidental refund with gift cards",
        ],
        "caller_display_name": "Cartwell Orders",
    },
    {
        "name": "utility_shutoff",
        "display_name": "Utility shutoff",
        "persona": "Linda from Crestview Power and Light billing",
        "ask": "pay a past-due bill by payment app right now before your power is shut off",
        "red_flags": [
            "Threat to shut off service within the hour",
            "Demands payment by payment app or store barcode",
            "Insists you pay before a crew arrives",
        ],
        "caller_display_name": "Crestview Power",
    },
    {
        "name": "prize_sweepstakes",
        "display_name": "Sweepstakes prize",
        "persona": "Richard Hayes from Silverline Sweepstakes",
        "ask": "pay taxes and processing fees with gift cards to collect a $250,000 prize",
        "red_flags": [
            "You won a contest you never entered",
            "Must pay fees or taxes to collect a prize",
            "Demands payment by gift card",
        ],
        "caller_display_name": "Silverline Prizes",
    },
    {
        "name": "health_benefits_card",
        "display_name": "Health benefits card",
        "persona": "Maria from the Senior Health Benefits Program",
        "ask": "confirm your member number and Social Security number to receive a new benefits card",
        "red_flags": [
            "Unexpected call about a new benefits card",
            "Asks for your member number or Social Security number",
            "Charges a fee for a card that should be free",
        ],
        "caller_display_name": "Senior Health Benefits",
    },
    {
        "name": "debt_relief",
        "display_name": "Credit card interest",
        "persona": "Tom from Lowbridge Credit Solutions",
        "ask": "read your credit card numbers and pay an upfront fee to lower your interest rate",
        "red_flags": [
            "Unsolicited offer to cut your interest rate to zero",
            "Charges a fee before doing anything",
            "Asks for your credit card numbers",
        ],
        "caller_display_name": "Lowbridge Credit",
    },
    {
        "name": "investment_opportunity",
        "display_name": "Investment opportunity",
        "persona": "Michael Grant, an advisor at Quantaris Capital",
        "ask": "send $5,000 by wire or cryptocurrency to open a guaranteed-return investment account",
        "red_flags": [
            "Guarantees big returns with little risk",
            "Demands payment by wire transfer or cryptocurrency",
            "Pressure to invest before the offer closes",
        ],
        "caller_display_name": "Quantaris Capital",
    },
    {
        "name": "phone_carrier",
        "display_name": "Mobile account",
        "persona": "Chris from Tellura Wireless account security",
        "ask": "read back the verification code texted to you and share your account PIN",
        "red_flags": [
            "Unexpected call about your phone account",
            "Asks for the code texted to your phone",
            "Asks for your account PIN",
        ],
        "caller_display_name": "Tellura Wireless",
    },
    {
        "name": "travel_package",
        "display_name": "Vacation offer",
        "persona": "Ashley from Sunmere Vacation Club",
        "ask": "pay taxes and fees by card today to claim a discounted resort vacation",
        "red_flags": [
            "Cheap vacation offer you didn't ask for",
            "Must pay fees and taxes up front",
            "Won't give specifics like the hotel's name",
        ],
        "caller_display_name": "Sunmere Travel",
    },
]

_SCENARIOS_BY_NAME = {s["name"]: s for s in SCENARIOS}


def get_scenario(name: str) -> dict | None:
    return _SCENARIOS_BY_NAME.get(name)


def list_scenarios() -> list[dict]:
    """Public, spoiler-free listing for the frontend's scenario dropdown."""
    return [{"name": s["name"], "display_name": s["display_name"]} for s in SCENARIOS]
