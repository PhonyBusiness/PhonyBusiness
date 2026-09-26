"""Do and don't tips for each scenario red flag, based on FTC consumer guidance.
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
    "Threat of arrest over an unpaid tax balance": {
        "do": "Check what you owe by contacting the tax agency through its official website or a number on a letter you received.",
        "dont": "Don't believe a caller who threatens arrest over taxes; tax agencies contact you by mail first.",
    },
    "Demands payment by gift card or wire transfer": {
        "do": "Hang up when a caller says a bill or tax must be paid by gift card or wire transfer.",
        "dont": "Don't buy gift cards or send a wire transfer to pay a debt someone called you about.",
    },
    "Insists you pay during this call": {
        "do": "End the call and look up the company's or agency's real number to check your balance.",
        "dont": "Don't pay anyone who says the money must be sent before you hang up.",
    },
    "Threat of arrest for missing jury duty": {
        "do": "Call the court clerk using the number on the court's official website to check your jury status.",
        "dont": "Don't believe a caller who threatens arrest for missed jury duty; courts don't collect fines by phone.",
    },
    "Asks for your date of birth or Social Security number": {
        "do": "Keep your date of birth and Social Security number private unless you started the contact.",
        "dont": "Don't confirm personal details to a caller claiming to be from a court or law enforcement.",
    },
    "Demands payment by payment app or cryptocurrency": {
        "do": "Treat any demand for payment app transfers or cryptocurrency as a sign of a scam.",
        "dont": "Don't send money through a payment app or cryptocurrency to settle a fine or bill.",
    },
    "Unexpected call about fraud on your account": {
        "do": "Hang up and call your bank using the number on the back of your card or on your statement.",
        "dont": "Don't use a phone number the caller gives you to check whether the call is real.",
    },
    "Asks for a verification code": {
        "do": "Keep verification codes to yourself; they are only for logging in to your own account.",
        "dont": "Don't read a verification code to anyone who calls you, even if they claim to be your bank or phone company.",
    },
    "Tells you to move your money to protect it": {
        "do": "Call your bank on a number you trust if you're worried about your account.",
        "dont": "Don't move, withdraw, or transfer money because a caller says it will keep it safe.",
    },
    "Call about an order you didn't place": {
        "do": "Log in to your account through the store's official app or website to check your orders.",
        "dont": "Don't call back a number or press a button offered by someone calling about an order.",
    },
    "Asks for your full card number and security code": {
        "do": "Only give card details when you started the purchase on a site or number you trust.",
        "dont": "Don't read your card number or security code to someone who called you.",
    },
    "Asks you to repay an accidental refund with gift cards": {
        "do": "Check your account directly with your bank or the store if someone claims you were over-refunded.",
        "dont": "Don't send gift cards or money to 'repay' a refund; real companies never ask for this.",
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
        "dont": "Don't pay a bill with a payment app, gift card, or a barcode someone texts you.",
    },
    "You won a contest you never entered": {
        "do": "Remember that you can't win a contest you never entered, and hang up.",
        "dont": "Don't believe a caller who says you won a big prize out of the blue.",
    },
    "Must pay fees or taxes to collect a prize": {
        "do": "Remember that real prizes are free, and hang up on anyone asking you to pay to collect one.",
        "dont": "Don't pay 'taxes', 'processing fees', or 'shipping' to receive a prize.",
    },
    "Demands payment by gift card": {
        "do": "Treat any request to pay with gift cards as a sure sign of a scam.",
        "dont": "Don't buy gift cards or read their numbers to anyone who called you.",
    },
    "Unexpected call about a new benefits card": {
        "do": "Call the number on your current benefits card if you have questions about a new card.",
        "dont": "Don't trust an unexpected caller who says your benefits card is changing or expiring.",
    },
    "Asks for your member number or Social Security number": {
        "do": "Guard your health plan member number like a credit card number, and only share it with providers you trust.",
        "dont": "Don't give your member number or Social Security number to a caller offering a new card.",
    },
    "Charges a fee for a card that should be free": {
        "do": "Remember that official benefits cards are free, and hang up on anyone who asks for payment.",
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
        "do": "Keep your card numbers private unless you started the call with a company you trust.",
        "dont": "Don't read your credit card numbers to a caller offering a deal.",
    },
    "Guarantees big returns with little risk": {
        "do": "Remember that every real investment carries risk, and only scammers guarantee profits.",
        "dont": "Don't invest with anyone who promises guaranteed or unusually high returns.",
    },
    "Demands payment by wire transfer or cryptocurrency": {
        "do": "Talk to a trusted financial advisor or family member before sending money to invest.",
        "dont": "Don't send a wire transfer or cryptocurrency to someone who cold-called you about an investment.",
    },
    "Pressure to invest before the offer closes": {
        "do": "Take time to research the company and the offer before investing anything.",
        "dont": "Don't let a deadline pressure you into investing on the spot.",
    },
    "Unexpected call about your phone account": {
        "do": "Contact your phone company through the number on your bill or its official app to check your account.",
        "dont": "Don't trust an unexpected caller who says there's a problem or a special offer on your phone account.",
    },
    "Asks for the code texted to your phone": {
        "do": "Treat a code texted to your phone as a password that protects your number, and keep it to yourself.",
        "dont": "Don't read a texted code to a caller; scammers use it to take over your phone number and accounts.",
    },
    "Asks for your account PIN": {
        "do": "Set a PIN on your phone account and keep it private.",
        "dont": "Don't share your account PIN or password with anyone who calls you.",
    },
    "Cheap vacation offer you didn't ask for": {
        "do": "Research the company and read reviews before considering any travel offer.",
        "dont": "Don't trust unexpected calls offering free or deeply discounted vacations.",
    },
    "Must pay fees and taxes up front": {
        "do": "Ask for the full offer in writing, including all fees, before paying anything.",
        "dont": "Don't pay fees or taxes up front for a vacation offered on a cold call.",
    },
    "Won't give specifics like the hotel's name": {
        "do": "Ask for the hotel's name, address, and the cruise or travel company before you commit.",
        "dont": "Don't book a trip if the caller won't give you specific details.",
    },
}
