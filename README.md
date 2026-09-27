# PhonyBusiness

Practice spotting phone scams before a real one catches you off guard.

PhonyBusiness puts you on a realistic simulated phone call with an AI "scammer"
running one of many common scripts — government imposters, tech support scams,
fake family emergencies, and more. If you slip up, the call pauses and coaches
you through what to watch for next time. If you handle it well, you get a recap
of exactly what you did right. No real phone number, no real risk, just practice.

## Features

- Realistic, voice-driven scam call simulations across 14 phone scam scenarios and multiple difficulty levels
- Live coaching the moment a red flag is missed, with specific do/don't guidance
- A post-call recap summarizing what happened and what to remember
- Dashboard analytics built from each finished call: per-call results plus overview, trends, risk, wellbeing, and operations views
- Privacy by design: we keep results, not conversations (no transcripts or names are stored)

## Tech stack

- **Backend:** FastAPI, MongoDB
- **Voice AI:** ElevenLabs Conversational AI
- **Scoring:** Google Gemini
- **Frontend:** Streamlit

## Scenarios

Every scenario is a phone call, grounded in FTC consumer guidance, and uses only
fictional agencies, companies, and people. They cover the FTC's top fraud
categories where a phone call is a common first contact:

| Scenario | FTC category |
| --- | --- |
| Benefits imposter, tax debt, jury duty warrant | Government imposter |
| Bank fraud alert, suspicious order, utility shutoff | Business imposter |
| Tech support | Tech support imposter |
| Family emergency | Family imposter |
| Sweepstakes prize | Prizes, sweepstakes and lotteries |
| Health benefits card | Health care |
| Credit card interest | Debt relief |
| Investment opportunity | Investment |
| Mobile account | Telephone and mobile services |
| Vacation offer | Travel |

Configs live in `backend/scenarios.py`; each has a persona, the scammer's ask,
three red flags, and the caller name shown on the incoming call screen.

## Getting started

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv sync
```

Copy `.env.example` to `.env` and fill in your own credentials, then start the backend:

```sh
uv run uvicorn backend.main:app --reload
```

In another terminal, start the frontend:

```sh
uv run streamlit run app.py
```

- Frontend: http://localhost:8501
- API health: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

## Project layout

```text
app.py              Streamlit frontend entry point
backend/
  config.py            Environment-backed settings
  database.py          MongoDB client and call-record operations
  deps.py              Shared settings/database instances used across routes
  elevenlabs_client.py ElevenLabs integration
  main.py              FastAPI application setup and router registration
  post_call.py         Turns the post-call webhook into a stored, privacy-safe record
  analytics.py         Dashboard queries (MongoDB aggregation pipelines)
  routers/
    calls.py           Scenario listing and call lifecycle routes
    tools.py           Live in-call agent tool routes
    webhooks.py        ElevenLabs post-call webhook
    analytics.py       Dashboard analytics routes
  scenarios.py         Scam call scenario configs
  tips.py              Red-flag guidance shown after a call
tests/                 Unit tests (in-memory MongoDB) and live integration checks
pyproject.toml      Dependencies
uv.lock              Locked dependency versions
.env.example         Required environment variables
```

## Backend API

| Method & path | Purpose |
| --- | --- |
| `GET /health` | Service and database health check |
| `GET /scenarios` | List available scam scenarios |
| `POST /calls/start` | Start a new practice call |
| `POST /calls/{call_id}/session` | Link an active call session for tracking |
| `POST /calls/{call_id}/hangup` | End a call |
| `POST /tools/record_outcome` | Record how a call went and surface relevant tips |
| `GET /calls/{call_id}` | Retrieve a call's outcome, score, and tips |
| `POST /webhooks/post-call` | Receive ElevenLabs' post-call webhook and store the call's analytics |

### Dashboard analytics

Each dashboard tab has its own endpoint. All data comes from the post-call webhook.

| Method & path | Tab | Returns |
| --- | --- | --- |
| `GET /analytics/conversations?limit=20` | Recent calls | Scenario, result, red flags, and time for recent calls |
| `GET /analytics/conversations/{conversation_id}` | Call detail | Outcome, when the resident decided, tips, frustration over the call, latency, cost |
| `GET /analytics/overview` | Overview | Call counts, pass/fail/stop rates, average decision time, average cost |
| `GET /analytics/trends?days=30` | Trends | Daily calls, pass rate, decision time, and frustration |
| `GET /analytics/risk` | Risk | Fail rate by scenario and difficulty; red flags ranked by failed calls |
| `GET /analytics/wellbeing` | Wellbeing | Safe-word stop rate, peak-frustration distribution, how calls ended |
| `GET /analytics/operations` | Operations | Cost per call, voice minutes, response latency, model fallbacks |

Pass rate counts only calls the resident decided (pass or fail); safe-word stops
are reported separately. Risk breakdowns with fewer than `ANALYTICS_MIN_GROUP_SIZE`
calls return `{"suppressed": true}` instead of numbers, so no resident can be singled out.

## Post-call webhook and privacy

Point the ElevenLabs agent's post-call webhook at `/webhooks/post-call`. When
`ELEVENLABS_WEBHOOK_SECRET` is set, requests without a valid `ElevenLabs-Signature`
are rejected; leave it unset only for local development.

Each finished call becomes one document in the `conversations` collection
(retries update it instead of duplicating it). We store timing, the outcome the
agent recorded, per-turn sentiment and frustration scores, latency, and cost.
We never store transcript text, the resident's name, the conversation history,
or the call summary. The matching call record is marked `ended`.


## Environment variables

See `.env.example` for the full list. At minimum you'll need a MongoDB
connection string and ElevenLabs credentials. Gemini is used for post-call
scoring.

| Variable | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string; uses the `phonybusiness` database if the URI names none |
| `ELEVENLABS_WEBHOOK_SECRET` | Verifies post-call webhook signatures |
| `ANALYTICS_MIN_GROUP_SIZE` | Smallest group the Risk tab will report (default 5) |


## Development

Run the unit tests (no credentials needed; MongoDB is replaced with an in-memory mock):

```sh
uv run pytest -v
```

To run the live integration checks, populate `.env` first:

```sh
uv sync
RUN_INTEGRATION_TESTS=1 uv run pytest tests/test_integrations.py -v --tb=no
```

These checks confirm your credentials work (MongoDB, ElevenLabs, Gemini) without
placing calls, generating content, or writing data. Normal `uv run pytest` skips
them unless `RUN_INTEGRATION_TESTS=1` is set.

Commit `uv.lock` after `uv sync` picks up a `pyproject.toml` change, so dependency
resolution stays reproducible for everyone on the team.
