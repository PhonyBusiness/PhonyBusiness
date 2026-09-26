"""Tip bank: do/don't guidance for each red flag, sourced from FTC consumer guidance.

Keyed by the exact red_flags text used in scenarios.py.
"""

TIP_BANK = {
    "Urgency or threat of losing benefits": {
        "do": "Hang up and call the benefits office using the number on its official website or a letter you trust.",
        "dont": "Don't believe a caller who says your benefits or Social Security number will be suspended; agencies don't call with threats.",
    },
    "Requests a Social Security number": {
        "do": "Share your Social Security number only when you made the call to a number you looked up yourself.",
        "dont": "Don't give your Social Security number to anyone who calls you, even if they say it's to verify you.",
    },
    "Caller ID spoofing a government agency": {
        "do": "Remember caller ID can be faked, so hang up and call the agency back on a number you look up yourself.",
        "dont": "Don't trust a call because the caller ID shows a government agency's name or number.",
    },
    "Unsolicited call about a virus": {
        "do": "Hang up, then have a trusted person or local shop check your computer if you're worried.",
        "dont": "Don't believe a call about a virus; real tech companies never call you about problems on your computer.",
    },
    "Requests remote desktop access": {
        "do": "Give remote access only to a support company you contacted yourself using a number you looked up.",
        "dont": "Don't install software, visit a website, or read a code for someone who called you out of the blue.",
    },
    "Pressure to act immediately": {
        "do": "Hang up and take time to check with someone you trust; a real problem will still be there later.",
        "dont": "Don't let a caller rush you; pressure to act right now is one of the surest signs of a scam.",
    },
    "Claims to be a family member in distress": {
        "do": "Hang up and call your family member, or another relative, on a number you already know.",
        "dont": "Don't trust the voice alone; scammers can fake a loved one's voice with AI.",
    },
    "Asks for secrecy": {
        "do": "Tell someone you trust about the call before you do anything the caller asked.",
        "dont": "Don't keep a call secret because the caller asked; scammers want you isolated so no one can warn you.",
    },
    "Requests money via an unusual payment method": {
        "do": "Hang up if a caller wants gift cards, wire transfers, cryptocurrency, or cash handed to a courier.",
        "dont": "Don't send money in ways that are hard to get back; only scammers demand those payment methods.",
    },
    "Threat of arrest over an unpaid tax balance": {
        "do": "Check your tax account through the tax agency's official website or the number on a letter you received.",
        "dont": "Don't believe a caller who threatens arrest over taxes; tax agencies contact you by mail first.",
    },
    "Demands payment by gift card or wire transfer": {
        "do": "Hang up when anyone says a tax or bill must be paid with gift cards or a wire transfer.",
        "dont": "Don't buy gift cards or wire money to pay a debt; no government agency takes payment that way.",
    },
    "Insists you pay during this call": {
        "do": "End the call and look up the agency's real number to check whether you owe anything.",
        "dont": "Don't pay anyone who says the money must be sent before you hang up.",
    },
    "Threat of arrest for missing jury duty": {
        "do": "Call the court clerk using the number on the court's official website to check your jury status.",
        "dont": "Don't believe a caller who threatens arrest for missed jury duty; courts don't collect fines by phone.",
    },
    "Asks for your date of birth or Social Security number": {
        "do": "Keep your date of birth and Social Security number private on any call you didn't make yourself.",
        "dont": "Don't confirm personal details to a caller; courts never ask potential jurors for them over the phone.",
    },
    "Demands payment by payment app or cryptocurrency": {
        "do": "Hang up when a caller says a fine can only be paid by payment app or cryptocurrency.",
        "dont": "Don't send a payment app transfer or cryptocurrency to clear a fine; only scammers ask for that.",
    },
    "Unexpected call about fraud on your account": {
        "do": "Hang up and call your bank using the number on the back of your card or on your statement.",
        "dont": "Don't call back a number the caller gives you; it goes straight to the scammer.",
    },
    "Asks for a verification code": {
        "do": "Keep verification codes to yourself; they are only for you to log in to your own account.",
        "dont": "Don't read a verification code to anyone who calls; your bank's fraud department will never ask for it.",
    },
    "Tells you to move your money to protect it": {
        "do": "Call your bank on a number you trust and tell them someone asked you to move your money.",
        "dont": "Don't move, withdraw, or transfer money to 'protect it'; anyone who tells you to is a scammer.",
    },
    "Call about an order you didn't place": {
        "do": "Check your orders by logging in to the store's official app or website yourself.",
        "dont": "Don't press a button or call a number offered by someone calling about an order.",
    },
    "Asks for your full card number and security code": {
        "do": "Give card details only when you started the purchase on a website or number you trust.",
        "dont": "Don't read your card number or security code to someone who called you, even to 'cancel' an order.",
    },
    "Asks you to repay an accidental refund with gift cards": {
        "do": "Check your account balance directly with your bank if someone says you were refunded too much.",
        "dont": "Don't send gift cards or money to repay a refund; real companies never ask for this.",
    },
    "Threat to shut off service within the hour": {
        "do": "Call your utility using the number on your bill or its official website to check your account.",
        "dont": "Don't let a threat of an immediate shutoff rush you into paying on the phone.",
    },
    "Insists you pay before a crew arrives": {
        "do": "Hang up and call the number on your utility bill to ask whether a shutoff is really scheduled.",
        "dont": "Don't pay on the phone because a caller says a crew is on the way to cut your service.",
    },
    "Demands payment by payment app, gift card, or store barcode": {
        "do": "Pay utility bills only through the methods listed on your bill or the utility's official website.",
        "dont": "Don't pay a bill with a payment app, gift card, or a barcode someone texts you; utilities don't ask for that.",
    },
    "You won a contest you never entered": {
        "do": "Remember that you can't win a contest you never entered, and hang up.",
        "dont": "Don't believe a caller who says you won a big prize out of the blue.",
    },
    "Must pay fees or taxes to collect a prize": {
        "do": "Remember that real prizes are free, and hang up on anyone who asks you to pay to collect one.",
        "dont": "Don't pay taxes, processing fees, or shipping charges to receive a prize.",
    },
    "Demands payment by gift card": {
        "do": "Treat any request to pay with gift cards as a sure sign of a scam, and hang up.",
        "dont": "Don't buy gift cards or read their numbers to anyone who called you.",
    },
    "Unexpected call about a new benefits card": {
        "do": "Call the number on the back of your current benefits card if you have questions about a new card.",
        "dont": "Don't trust an unexpected caller who says your benefits card is changing or about to stop working.",
    },
    "Asks for your member number or Social Security number": {
        "do": "Guard your health plan member number like a credit card, and share it only with doctors and providers you trust.",
        "dont": "Don't give your member number or Social Security number to a caller offering a new card or free supplies.",
    },
    "Charges a fee for a card that should be free": {
        "do": "Remember that official benefits cards are free, and hang up on anyone who asks you to pay.",
        "dont": "Don't pay an activation or processing fee for a benefits card.",
    },
    "Unsolicited offer to cut your interest rate to zero": {
        "do": "Call the number on the back of your credit card to ask your card company about your rate.",
        "dont": "Don't trust unexpected calls or recorded messages promising to lower your interest rate.",
    },
    "Charges a fee before doing anything": {
        "do": "Remember that it's illegal for debt relief companies to charge you before they settle or reduce your debt.",
        "dont": "Don't pay an upfront fee for debt relief or a lower interest rate.",
    },
    "Asks for your credit card numbers": {
        "do": "Keep your card numbers private unless you called a company you trust on a number you looked up.",
        "dont": "Don't read your credit card numbers to a caller offering a deal.",
    },
    "Guarantees big returns with little risk": {
        "do": "Remember that every real investment carries risk, and only scammers guarantee profits.",
        "dont": "Don't invest with anyone who promises guaranteed or unusually high returns.",
    },
    "Demands payment by wire transfer or cryptocurrency": {
        "do": "Talk to a trusted financial advisor or family member before sending money to invest.",
        "dont": "Don't wire money or send cryptocurrency to someone who cold-called you; it's nearly impossible to get back.",
    },
    "Pressure to invest before the offer closes": {
        "do": "Take time to research the company and talk to someone you trust before investing anything.",
        "dont": "Don't let a deadline pressure you into investing on the spot; real opportunities don't vanish in an hour.",
    },
    "Unexpected call about your phone account": {
        "do": "Check your account through the number on your phone bill or your carrier's official app.",
        "dont": "Don't trust an unexpected caller who says there's a problem or a special offer on your phone account.",
    },
    "Asks for the code texted to your phone": {
        "do": "Treat a code texted to your phone like a password, and keep it to yourself.",
        "dont": "Don't read a texted code to a caller; scammers use it to take over your phone number and accounts.",
    },
    "Asks for your account PIN": {
        "do": "Set a PIN on your phone account and keep it private, so no one can move your number without you.",
        "dont": "Don't share your account PIN or password with anyone who calls you.",
    },
    "Cheap vacation offer you didn't ask for": {
        "do": "Look up the company and read reviews before considering any travel offer.",
        "dont": "Don't trust unexpected calls offering free or deeply discounted vacations.",
    },
    "Must pay fees and taxes up front": {
        "do": "Ask for the full offer in writing, including every fee, before paying anything.",
        "dont": "Don't pay fees or taxes up front for a vacation offered on a cold call; that 'free' trip isn't free.",
    },
    "Won't give specifics like the hotel's name": {
        "do": "Ask for the hotel's name and address and the travel company's name before you commit.",
        "dont": "Don't book a trip if the caller won't give you specific details.",
    },
}


def get_tips(flags: list[str]) -> list[dict]:
    """Look up tips for the given flags, silently skipping any that don't match."""
    return [TIP_BANK[flag] | {"label": flag} for flag in flags if flag in TIP_BANK]
