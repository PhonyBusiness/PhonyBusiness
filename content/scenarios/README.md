# Scenarios

Reference content for later features. The MVP backend uses the smaller
configs in `backend/scenarios.py`; these files hold the FTC-based detail
(red flag ids, difficulty, stages, sources) to fold in once the basic loop works.

One JSON file per practice-call scenario. Every agency, company, person, and
phone number is fictional. Phone numbers use the 555-0100 to 555-0199 range
reserved for fiction. Scripts follow what the FTC documents about each scam:
the claims, the ask, and the payment methods scammers demand.

## Fields

| Field | Used by | Purpose |
| --- | --- | --- |
| `id` | Backend, dashboard | Stable key, matches the file name |
| `version` | Backend | Bump when the content changes |
| `family` | Dashboard | Groups scenarios for "fail rate by scenario family" |
| `title` | Start page | Name shown when choosing a scenario |
| `contact_method` | Dashboard | Always `phone` for the MVP |
| `caller_id` | Incoming call screen | `name` and `number` shown while ringing |
| `persona` | Agent (`{{persona}}`) | Who the scammer claims to be |
| `pretext` | Agent (`{{pretext}}`) | Finishes the first message: "calling about ..." |
| `story` | Agent prompt | Background the scammer stays consistent with |
| `ask` | Agent (`{{ask}}`) | What the scammer is trying to get |
| `red_flags` | Agent (`{{red_flags}}`), tip bank, `record_outcome` | Tactics this call uses; `id` is shared with the tip bank and the outcome's `flags` |
| `stages` | Agent prompt | What to do at each stage: hook, build_trust, ask, pressure, close |
| `fake_credentials` | Agent prompt | Details to offer a skeptical resident |
| `disclosure_triggers` | Agent prompt | Any of these means fail: interrupt and call `record_outcome` |
| `pass_signals` | Agent prompt, re-scoring | Behaviors that count as a pass |
| `difficulty` | Agent (`{{difficulty}}`) | How the scammer behaves at `easy`, `medium`, and `hard` |
| `sources` | Team, pitch | FTC consumer guidance the script is based on |

The backend sends the text for the chosen difficulty level as `{{difficulty}}`,
not just the level name.

## Scenarios

All scenarios are phone calls. The MVP three are marked.

| Id | Family | FTC category |
| --- | --- | --- |
| `benefits_imposter` (MVP) | `government_imposter` | Imposter scams |
| `tax_debt` | `government_imposter` | Imposter scams |
| `jury_duty_warrant` | `government_imposter` | Imposter scams |
| `bank_fraud_alert` | `business_imposter` | Imposter scams |
| `order_refund` | `business_imposter` | Imposter scams |
| `utility_shutoff` | `business_imposter` | Imposter scams |
| `tech_support` (MVP) | `tech_support_imposter` | Imposter scams |
| `family_emergency` (MVP) | `family_imposter` | Imposter scams |
| `prize_sweepstakes` | `prize_scam` | Prizes, sweepstakes and lotteries |
| `health_benefits_card` | `health_care` | Health care |
| `debt_relief` | `debt_relief` | Mortgage foreclosure relief and debt management |
| `investment_opportunity` | `investment` | Investment related |
| `phone_carrier` | `telephone_services` | Telephone and mobile services |
| `travel_package` | `travel` | Travel, vacations and timeshare plans |

## Red flag ids

`unsolicited_call`, `authority_claim`, `threat`, `urgency`,
`sensitive_info_request`, `verification_code_request`, `unusual_payment`,
`upfront_fee`, `too_good_to_be_true`, `secrecy`, `remote_access_request`,
`emotional_manipulation`, `fishing_for_details`
