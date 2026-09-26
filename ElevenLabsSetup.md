# ElevenLabs Agent Setup Guide

This guide walks through setting up the ElevenLabs voice agent that powers PhonyBusiness, an AI scam call simulator that adapts to what the user says, decides whether they passed or failed, and then coaches them on the red flags.

By the end you will have:

- An ElevenLabs agent that plays a realistic scammer, driven by dynamic variables
- A `record_outcome` server tool that reports pass, fail, caution, or stopped to the backend and gets debrief tips back
- An `end_call` system tool so the agent hangs up after the debrief
- A post-call webhook that sends the full transcript to the backend for re-scoring
- A browser-based call started from the React frontend (no Twilio or phone numbers needed)

## How the pieces fit together

```
Browser (React SDK)
   | starts a session with dynamic variables (persona, ask, red_flags, call_id, ...)
   v
ElevenLabs agent (Gemini LLM + ElevenLabs voice)
   | during the call: calls record_outcome  --->  Backend /tools/record_outcome
   |                                         <---  returns TIPS as plain text
   | after the call: post-call webhook       --->  Backend /webhooks/post-call
   v
Backend stores the outcome, re-scores the transcript with Gemini, feeds the dashboard
```

## Before you start

- An ElevenLabs account. Voice calls use credits quickly (a two-minute test call used roughly 700 credits in our testing, so the free tier covers only about 15 calls). Redeem any hackathon promo code first, and see "Save credits" in the testing section.
- The backend running and reachable from the internet (we used `ngrok http 8000` during development).
- The scenario definitions from `scenarios.py` and the tip bank from the backend, since the agent's red flag names must match the tip bank keys exactly.

## Step 1: Create an API key

1. In ElevenLabs, open **API Keys** and click **Create API key**. Name it something like `phonybusiness`.
2. Set permissions to the minimum the backend needs:

| Permission | Setting | Why |
| --- | --- | --- |
| ElevenAgents | Write | Start sessions, request signed URLs, read conversations |
| Everything else | No Access | The agent's own speech and transcription run inside the agent session, so the key does not need Text to Speech, Speech to Text, Voices, or Voice Generation |

3. Copy the key immediately (it starts with `sk_` and is shown only once) and add it to the backend `.env`. The key must never be sent to the browser.

## Step 2: Create the agent

1. Open **ElevenAgents** and click **Create agent**, then choose **Blank agent**. Name it `PhonyBusiness`.
2. Configure the basics:
   - **Language:** English
   - **LLM:** `gemini-2.5-flash`. We saw truncated replies and slow fallback turns with a newer preview Flash model, and switching to a stable model fixed it. Also make sure there is no low max tokens limit on the LLM.
   - **Voice:** any convincing stock voice from the library. The same voice plays both the scammer and the coach. Do not clone a real person's voice.
3. Save, and copy the agent ID (starts with `agent_`) from the agent page or the URL into `.env` as `ELEVENLABS_AGENT_ID`.

## Step 3: First message

Set the agent's **First message** to:

```
Hello, is this {{first_name}}? This is {{persona}}, calling about an urgent matter on your account.
```

Anything in `{{double_braces}}` is a dynamic variable that the frontend fills in when it starts the session.

## Step 4: Dynamic variables

The agent uses seven dynamic variables. The frontend passes real values for each call; the agent settings hold test values for dashboard testing.

| Variable | What it is | Example test value |
| --- | --- | --- |
| `first_name` | The user's first name | `Anushri` |
| `persona` | Who the scammer claims to be (fictional names only) | `Officer Daniels from the Federal Benefits Office` |
| `ask` | What the scammer wants the user to AGREE to (not to read out) | `agree to verify their Social Security number over the phone to prevent their benefits from being suspended` |
| `red_flags` | Comma-separated red flags, spelled exactly like the tip bank keys | `Urgency or threat of losing benefits, Requests a Social Security number` |
| `difficulty` | 1 (sloppy) to 3 (polished) | `2` |
| `safe_word` | Word that stops the call immediately | `pineapple` |
| `call_id` | Backend call record ID, used to match tool calls and webhooks to the call | `test_123` |

Two rules matter here:

- `ask` must use agreement framing ("agree to verify...") rather than "read out your number." See troubleshooting for why.
- `red_flags` must match the tip bank keys character for character, including capitalization, because the agent copies these names into `record_outcome`.

## Step 5: System prompt

Paste this as the agent's system prompt. It covers the scam simulation, how the agent reads the user each turn, the pass and fail rules, the safe word, and the coach-mode debrief.

```
You are the caller in a scam awareness training simulation called PhonyBusiness.
The person has chosen to take a practice scam call. Your job is to act like a
realistic phone scammer so they can practice spotting red flags.

YOUR ROLE
You are: {{persona}}
Your goal: get the person to {{ask}}
Red flags to show naturally during the call: {{red_flags}}
Difficulty: {{difficulty}}
- 1: pushy and a little sloppy, vague details, easy to spot
- 2: confident and believable, some pressure
- 3: calm, polished, uses their name, offers "proof" when doubted

HOW THE CALL FLOWS (your stage)
1. Hook: introduce yourself and the "problem."
2. Build trust: sound official, use reference or case numbers.
3. The ask: get their AGREEMENT to your goal, e.g. "Are you able to verify
   your ID with me right now?" or "Can you get your card in front of you?"
   Never ask them to actually read out a number, code, password, or detail.
4. Pressure: add urgency or consequences if they stall.
5. Close: push for immediate agreement.
Only move to the next stage when the person engages.

READ THE PERSON EVERY TURN (their stance)
- Compliant (going along): move toward the ask.
- Hesitant ("I'm not sure"): reassure them, say it's routine and quick.
- Skeptical ("How do I know you're real?"): offer a fake badge number,
  case number, or callback number.
- Refusing ("No," "I'll call the office myself"): push back at most
  twice, politely. After that, accept it.

STYLE
- This is a phone call. Keep every reply to one or two short sentences.
- Sound natural: small pauses, "okay," "I understand," "ma'am" or "sir."
- Never use real government agency, bank, or company names. Only use the
  names given in your persona.
- Never threaten violence, arrest by force, or harm to family. Never insult.

DECIDING THE OUTCOME
PASS: the person clearly refuses after your pushback, says it's a scam,
says they will call the official number themselves, or asks whether this
is an AI or a practice call.

FAIL: the person agrees to your ask ("yes," "okay," "hold on, let me get
it"), OR starts saying any number, code, password, or card detail, OR
agrees to pay, buy gift cards, send money, install software, or keep the
call secret.
On FAIL, immediately say: "Let me stop you right there. Don't share
anything else." Then call record_outcome.

CAUTION: the person has spoken 8 times without clearly refusing or
agreeing. Call record_outcome with caution.

SAFE WORD
The person's safe word is: {{safe_word}}
If the person says the safe word at any point, even mid-sentence or
mid-scenario, stop immediately. This overrides every other rule.
1. Say: "No problem, we'll stop here. This was a PhonyBusiness practice call."
2. Call record_outcome with result "stopped".
3. Do NOT give the debrief or any lesson. Just say: "You can try another
   practice call whenever you're ready. Take care." Then use the end_call
   tool.

WHEN AN OUTCOME IS REACHED
Before calling record_outcome on a PASS or CAUTION, say: "Okay, one moment."
Call record_outcome right away with the result, the flags, and the turn
number. Do not continue the scam after that.
For flags, copy the red flag names EXACTLY as written here, character for
character, separated by commas: {{red_flags}}
Do not shorten, reword, or invent flag names. If unsure, send all of them.
If the person asked whether this is an AI or a practice call, first say
honestly: "Yes, this is a PhonyBusiness practice call."

COACH MODE (starts immediately after record_outcome returns, except when
the result is "stopped")
Do not wait for the person to respond. In the same reply, drop the scammer
persona completely and speak warmly and a little slower. Say, in order:
1. Reveal: "This was a PhonyBusiness practice call. Nothing you said was
   saved or shared."
2. Result:
   - PASS: praise the specific thing they did right.
   - FAIL: reassure them first ("Lots of people respond the same way,
     that's why we practice"), then name the moment they slipped.
   - CAUTION: say they didn't fall for it, but staying on the line gave
     the scammer more chances.
3. Red flags: name two or three red flags from THIS call and when they
   happened.
4. What to do: hang up, look up the official number yourself, and call
   back. Talk to someone you trust first.
5. What not to do: never share codes, ID numbers, or card details on a
   call you didn't start, and never pay with gift cards, wire transfers,
   or crypto because a caller asked.
record_outcome returns TIPS. Use those tips for steps 3 to 5, in your own
warm words. They take priority over the general advice above.
Only describe things that actually happened in this call.
Keep the whole debrief under 45 seconds of speech.
Then ask: "Do you have any questions?" Answer briefly, then say goodbye
and use the end_call tool.
```

## Step 6: The `record_outcome` server tool

This tool is how the agent reports the outcome mid-call and gets debrief tips back from the backend.

1. In the agent, open **Tools**, click **Add tool**, and choose **Webhook**.
2. Configure it:
   - **Name:** `record_outcome`
   - **Description:** `Call this the moment the call reaches an outcome: the person passes, fails, is in a cautious middle state, or says the safe word. Returns debrief tips.`
   - **Method:** POST
   - **URL:** `https://<your-backend>/tools/record_outcome`
3. Add four body properties:

| Identifier | Data type | Required | Value type | Notes |
| --- | --- | --- | --- | --- |
| `result` | String | Yes | LLM Prompt | Enum values: `pass`, `fail`, `caution`, `stopped` |
| `flags` | String | Yes | LLM Prompt | Comma-separated; the backend splits it into a list |
| `turn` | Number | Yes | LLM Prompt | How many times the person has spoken |
| `call_id` | String | Yes | Dynamic Variable | Variable name `call_id`. The LLM never fills this in, so it cannot be mangled |

4. Set the body description (the field passed to the LLM) to:

```
Send the outcome of the practice scam call as soon as it is decided.

result: one of pass, fail, caution, or stopped.
- pass: the person clearly refused, said it was a scam, hung up, said they
  would call the official number themselves, or asked if this is an AI or
  a practice call.
- fail: the person agreed to the ask, started to share a number, code,
  password, card detail, or ID, or agreed to pay, buy gift cards, send
  money, install software, or keep the call secret.
- caution: the person stayed on the line and answered questions but did
  not comply or clearly refuse.
- stopped: the person said the safe word.

flags: the red flags you showed during the call, copied EXACTLY from this
list and separated by commas: {{red_flags}}

turn: the number of times the person has spoken so far in the call.
```

5. Save the tool.

**What the agent sends:**

```json
{
  "call_id": "6ab824da6d4fe2d2cfb0103c",
  "result": "fail",
  "flags": "Urgency or threat of losing benefits, Requests a Social Security number",
  "turn": 4
}
```

**What the backend returns** (plain text, which the agent reads straight into the debrief):

```
RESULT: fail
TIPS:
- Red flag: Urgency or threat of losing benefits
  Do: Hang up and contact the agency directly using a number from its official website.
  Don't: Don't let urgency or fear of losing benefits rush you into acting on the call.
- Red flag: Requests a Social Security number
  Do: Only share your Social Security number through channels you initiated yourself.
  Don't: Don't give out your Social Security number to anyone who calls you unprompted.
```

The backend should never return an empty response. If no flags match the tip bank, it falls back to general tips; otherwise the agent improvises and can describe things that did not happen.

## Step 7: The `end_call` system tool

1. In the agent, open **Tools**, then **System tools**.
2. Turn on **End call** and save.

The prompt already tells the agent to use `end_call` after the goodbye. In the post-call payload you will see `termination_reason: "end_call tool was called."` when it works.

## Step 8: Post-call webhook

This sends the full transcript to the backend after every call.

1. Open the **ElevenAgents settings page** (workspace level, not inside the agent's tools).
2. In the **Post-call webhook** section, create a webhook with the URL `https://<your-backend>/webhooks/post-call` and choose the **transcription** type (not audio).
3. Copy the HMAC secret shown on creation and add it to the backend `.env` as `ELEVENLABS_WEBHOOK_SECRET`. The backend can verify the `ElevenLabs-Signature` header with it.
4. Save.

The endpoint must return HTTP 200 quickly. Do the Gemini re-scoring after responding, since webhooks that keep failing can be auto-disabled.

**Fields the backend uses:**

| Field | Path in payload |
| --- | --- |
| Conversation ID | `data.conversation_id` |
| Our call ID | `data.conversation_initiation_client_data.dynamic_variables.call_id` |
| Scenario info | same `dynamic_variables` object: `persona`, `ask`, `difficulty` |
| Transcript | `data.transcript[]`, using `role` and `message` |
| Live outcome | the transcript entry whose `tool_calls[].tool_name` is `record_outcome`; its `params_as_json` is a JSON string and must be parsed |
| Duration | `data.metadata.call_duration_secs` |
| Summary | `data.analysis.transcript_summary` |
| Call status | `data.status` (`done` or `failed`) and `data.error` |

Webhooks still arrive for failed calls (for example, when credits run out). Store the outcome if `record_outcome` fired, and mark the call incomplete instead of crashing.

## Step 9: Start the call from the browser

The frontend starts a voice session with the ElevenLabs React SDK and passes the dynamic variables for that call. The `call_id` comes from the backend's `POST /calls/start`.

```javascript
await conversation.startSession({
  signedUrl,               // from the backend once authentication is on; use agentId before that
  dynamicVariables: {
    call_id: call.id,
    first_name,
    persona,
    ask,
    red_flags,
    difficulty,
    safe_word,
  },
});
```

## Step 10: Turn on authentication (last)

Once the backend's `POST /calls/start` returns a signed URL (or conversation token) created with the API key, enable authentication in the agent's security settings. After that, only sessions started through your backend can use the agent.

Do this last. With authentication on, the frontend cannot start sessions using the agent ID alone, which blocks testing until the backend piece exists.

## Environment variables

| Variable | Where it comes from | Used by |
| --- | --- | --- |
| `ELEVENLABS_API_KEY` | Step 1 | Backend only |
| `ELEVENLABS_AGENT_ID` | Step 2 | Backend and frontend |
| `ELEVENLABS_WEBHOOK_SECRET` | Step 8 | Backend only |

Keep `.env` in `.gitignore` and commit a `.env.example` with empty values.

## Testing

### Test during development without a backend

Before the backend exists, point the `record_outcome` tool and the post-call webhook at two separate [webhook.site](https://webhook.site) URLs. You can see exactly what the agent sends. On the tool's URL, use **Edit** to set a default response body with sample tips; otherwise the agent receives "This URL has no default content configured" and improvises the debrief.

### Test matrix

Run each case and confirm the backend logs show the right `call_id`, `result`, and exact flag names, and that the debrief uses the returned tips.

| Case | What to say | Expected result |
| --- | --- | --- |
| Pass | Refuse firmly, or "I'll call the official number myself" | `pass`, then praise and debrief |
| Fail | "Okay, let me get it" | Agent says "Let me stop you right there," `fail`, then a reassuring debrief |
| Caution | Keep asking questions without agreeing or refusing | `caution` after about 8 turns |
| Safe word | "Pineapple" at any point | `stopped`, no lesson, call ends |
| Honesty | "Is this an AI?" | Agent admits it, `pass` |

Repeat a pass and a fail for each scenario in `scenarios.py`.

### Save credits

Use the agent's text-mode test in the dashboard for logic tests (outcomes, safe word, flags). It skips speech costs. Save voice calls for checking tone and latency, and keep a buffer of at least 10 full voice calls for demo rehearsals.

## Troubleshooting (lessons learned)

**The agent does not stop the user mid-number.** A voice agent can only respond once the user pauses, so someone reading a number in one breath gets heard in full. The fix is in the design: the scammer asks for agreement first ("Are you able to verify your ID right now?"), agreement itself counts as a fail, and the agent never asks for the actual digits. Keep transcript redaction on the backend as a safety net.

**The flags do not match the tip bank.** The agent reworded them (for example, "urgency, ID request"). Putting the exact-copy instruction in the system prompt, not only in the tool description, fixed it. The backend should still fall back to case-insensitive or keyword matching, then general tips.

**The debrief waits for the user to speak.** Tell the agent explicitly to start coach mode in the same reply after the tool returns, with no waiting.

**The debrief describes things that did not happen.** This happened when the tool returned no tips. Make the backend always return tips, and keep the "Only describe things that actually happened in this call" line in the prompt.

**Replies get cut off mid-sentence ("We..." then silence).** If those turns show `"interrupted": false` in the payload, the model produced truncated text; the user did not interrupt. Switch to a stable model such as `gemini-2.5-flash` and check for a low max tokens limit.

**Long silence before the debrief.** Generating the tool call can take a few seconds. The "Okay, one moment" line fills the gap.

**"Dynamic variable cannot be empty" on a tool property.** When the value type is Dynamic Variable, type the variable name (for example `call_id`, without braces) in the Variable Name field.

**The call ends with a quota error.** The payload shows `status: "failed"` and an error like "This request exceeds your quota." You are out of credits. Redeem promo codes or upgrade, and use text mode for logic tests.

**The tool or webhook stops working after a restart.** Free ngrok URLs change each time ngrok restarts. Update both the `record_outcome` URL and the post-call webhook URL.

## Safety notes

- Scenarios use fictional agencies, banks, and companies only.
- The agent never asks users to read out real numbers, and the backend redacts digit sequences from transcripts.
- The safe word ends any call immediately with no lesson.
- If a user asks whether they are talking to an AI, the agent says yes.
- Use only stock or designed voices, never clones of real people.