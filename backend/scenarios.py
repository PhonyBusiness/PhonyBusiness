"""Static MVP scenario configs.

`ask` is phrased as what the caller wants the person to AGREE to, never to read out,
so the agent asks for willingness instead of digits. `opening_line` is the agent's
first message; `{first_name}` is filled in by POST /calls/start.
"""

SCENARIOS = [
    {
        "name": "family_emergency",
        "display_name": "Family emergency",
        "persona": "your grandson calling from jail after a car accident",
        "ask": "agree to send bail money right away and keep it a secret from the rest of the family",
        "red_flags": [
            "Claims to be a family member in distress",
            "Asks for secrecy",
            "Requests money via an unusual payment method",
        ],
        "caller_display_name": "Unknown Caller",
        "opening_line": "Hey... it's me. Please don't hang up, I'm in really big trouble.",
    },
    {
        "name": "benefits_imposter",
        "display_name": "Benefits imposter",
        "persona": "Officer Daniels from the Federal Benefits Office",
        "ask": "agree to verify their Social Security number over the phone to avoid losing their benefits",
        "red_flags": [
            "Urgency or threat of losing benefits",
            "Requests a Social Security number",
            "Caller ID spoofing a government agency",
        ],
        "caller_display_name": "Federal Benefits Office",
        "opening_line": "Hello, is this {first_name}? This is Officer Daniels with the Federal Benefits Office, calling about your monthly benefits.",
    },
    {
        "name": "tech_support",
        "display_name": "Tech support",
        "persona": "a support technician from SecureTech Support",
        "ask": "agree to let you remote into their computer to fix a virus that was detected",
        "red_flags": [
            "Unsolicited call about a virus",
            "Requests remote desktop access",
            "Pressure to act immediately",
        ],
        "caller_display_name": "SecureTech Support",
        "opening_line": "Hi, is this {first_name}? This is SecureTech Support. Our system just flagged a serious problem on your computer.",
    },
    {
        "name": "tax_debt",
        "display_name": "Tax debt",
        "persona": "Agent Collins from the Federal Revenue Office",
        "ask": "agree to pay an overdue tax balance with gift cards today to avoid arrest",
        "red_flags": [
            "Threat of arrest over an unpaid tax balance",
            "Demands payment by gift card or wire transfer",
            "Insists you pay during this call",
        ],
        "caller_display_name": "Federal Revenue Office",
        "opening_line": "Is this {first_name}? This is Agent Collins with the Federal Revenue Office. I'm calling about an overdue balance in your name.",
    },
    {
        "name": "jury_duty_warrant",
        "display_name": "Jury duty warrant",
        "persona": "Sergeant Brennan from the Marlow County Sheriff's Office",
        "ask": "agree to pay a fine by payment app or cryptocurrency to clear a warrant for missed jury duty",
        "red_flags": [
            "Threat of arrest for missing jury duty",
            "Asks for your date of birth or Social Security number",
            "Demands payment by payment app or cryptocurrency",
        ],
        "caller_display_name": "Marlow County Sheriff",
        "opening_line": "{first_name}? This is Sergeant Brennan with the Marlow County Sheriff's Office. We need to talk about a missed jury duty date.",
    },
    {
        "name": "bank_fraud_alert",
        "display_name": "Bank fraud alert",
        "persona": "Emily from the Harborline Bank fraud department",
        "ask": "agree to share the verification code sent to their phone and move their savings to a \"safe\" account",
        "red_flags": [
            "Unexpected call about fraud on your account",
            "Asks for a verification code",
            "Tells you to move your money to protect it",
        ],
        "caller_display_name": "Harborline Bank",
        "opening_line": "Hi, is this {first_name}? This is Emily from the Harborline Bank fraud department. We've spotted some unusual activity on your account.",
    },
    {
        "name": "order_refund",
        "display_name": "Suspicious order",
        "persona": "Jason from Cartwell customer protection",
        "ask": "agree to confirm their card details over the phone to cancel an order they didn't place",
        "red_flags": [
            "Call about an order you didn't place",
            "Asks for your full card number and security code",
            "Asks you to repay an accidental refund with gift cards",
        ],
        "caller_display_name": "Cartwell Orders",
        "opening_line": "Hey, is this {first_name}? It's Jason with Cartwell customer protection, calling about a large order on your account.",
    },
    {
        "name": "utility_shutoff",
        "display_name": "Utility shutoff",
        "persona": "Linda from Crestview Power and Light billing",
        "ask": "agree to pay a past-due bill by payment app right now before their power is shut off",
        "red_flags": [
            "Threat to shut off service within the hour",
            "Demands payment by payment app or store barcode",
            "Insists you pay before a crew arrives",
        ],
        "caller_display_name": "Crestview Power",
        "opening_line": "Hello, {first_name}? This is Linda from Crestview Power and Light billing, about your account balance.",
    },
    {
        "name": "prize_sweepstakes",
        "display_name": "Sweepstakes prize",
        "persona": "Richard Hayes from Silverline Sweepstakes",
        "ask": "agree to pay taxes and processing fees with gift cards to collect a $250,000 prize",
        "red_flags": [
            "You won a contest you never entered",
            "Must pay fees or taxes to collect a prize",
            "Demands payment by gift card",
        ],
        "caller_display_name": "Silverline Prizes",
        "opening_line": "Hello, is this {first_name}? This is Richard Hayes from Silverline Sweepstakes, and have I got good news for you!",
    },
    {
        "name": "health_benefits_card",
        "display_name": "Health benefits card",
        "persona": "Maria from the Senior Health Benefits Program",
        "ask": "agree to confirm their member number and Social Security number over the phone to receive a new benefits card",
        "red_flags": [
            "Unexpected call about a new benefits card",
            "Asks for your member number or Social Security number",
            "Charges a fee for a card that should be free",
        ],
        "caller_display_name": "Senior Health Benefits",
        "opening_line": "Hi, is this {first_name}? This is Maria from the Senior Health Benefits Program, calling about your new member card.",
    },
    {
        "name": "debt_relief",
        "display_name": "Credit card interest",
        "persona": "Tom from Lowbridge Credit Solutions",
        "ask": "agree to share their credit card details and pay an upfront fee to lower their interest rate",
        "red_flags": [
            "Unsolicited offer to cut your interest rate to zero",
            "Charges a fee before doing anything",
            "Asks for your credit card numbers",
        ],
        "caller_display_name": "Lowbridge Credit",
        "opening_line": "Hi {first_name}, it's Tom from Lowbridge Credit Solutions. Got a quick minute? It's about your credit card interest rate.",
    },
    {
        "name": "investment_opportunity",
        "display_name": "Investment opportunity",
        "persona": "Michael Grant, an advisor at Quantaris Capital",
        "ask": "agree to send $5,000 by wire or cryptocurrency to open a guaranteed-return investment account",
        "red_flags": [
            "Guarantees big returns with little risk",
            "Demands payment by wire transfer or cryptocurrency",
            "Pressure to invest before the offer closes",
        ],
        "caller_display_name": "Quantaris Capital",
        "opening_line": "Hi there, is this {first_name}? Michael Grant here, an advisor with Quantaris Capital.",
    },
    {
        "name": "phone_carrier",
        "display_name": "Mobile account",
        "persona": "Chris from Tellura Wireless account security",
        "ask": "agree to share the verification code texted to them and their account PIN",
        "red_flags": [
            "Unexpected call about your phone account",
            "Asks for the code texted to your phone",
            "Asks for your account PIN",
        ],
        "caller_display_name": "Tellura Wireless",
        "opening_line": "Hi, is this {first_name}? This is Chris from Tellura Wireless account security. We noticed something odd on your line.",
    },
    {
        "name": "travel_package",
        "display_name": "Vacation offer",
        "persona": "Ashley from Sunmere Vacation Club",
        "ask": "agree to pay taxes and fees by card today to claim a discounted resort vacation",
        "red_flags": [
            "Cheap vacation offer you didn't ask for",
            "Must pay fees and taxes up front",
            "Won't give specifics like the hotel's name",
        ],
        "caller_display_name": "Sunmere Travel",
        "opening_line": "Hi, is this {first_name}? This is Ashley from Sunmere Vacation Club, and you've been selected for something exciting!",
    },
]

_SCENARIOS_BY_NAME = {s["name"]: s for s in SCENARIOS}


def get_scenario(name: str) -> dict | None:
    return _SCENARIOS_BY_NAME.get(name)


def list_scenarios() -> list[dict]:
    """Public, spoiler-free listing for the frontend's scenario dropdown."""
    return [{"name": s["name"], "display_name": s["display_name"]} for s in SCENARIOS]