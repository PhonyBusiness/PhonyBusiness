# PhonyBusiness

Practice spotting phone scams before a real one catches you off guard.

PhonyBusiness puts you on a realistic simulated phone call with an AI "scammer"
running one of many common scripts — government imposters, tech support scams,
fake family emergencies, and more. If you slip up, the call pauses and coaches
you through what to watch for next time. If you handle it well, you get a recap
of exactly what you did right. No real phone number, no real risk — just practice.

## Features

- Realistic, voice-driven scam call simulations across multiple scenarios and difficulty levels
- Live coaching the moment a red flag is missed, with specific do/don't guidance
- A post-call recap summarizing what happened and what to remember
- A trends dashboard (planned) to see how practice pays off over time

## Tech stack

- **Backend:** FastAPI, MongoDB
- **Voice AI:** ElevenLabs Conversational AI
- **Scoring:** Google Gemini
- **Frontend:** Streamlit

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
  elevenlabs_client.py ElevenLabs integration
  main.py              FastAPI application and routes
  scenarios.py         Scam call scenario configs
  tips.py              Red-flag guidance shown after a call
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

## Environment variables

See `.env.example` for the full list. At minimum you'll need a MongoDB
connection string and ElevenLabs credentials; Gemini is used for post-call
scoring.

Keep real credentials out of version control — `.env` is gitignored.

## Roadmap

- [ ] Post-call transcript scoring via Gemini
- [ ] Trends dashboard
- [ ] Deployed, mobile-friendly build

## Development

Populate `.env`, then run the live integration checks:

```sh
uv sync
RUN_INTEGRATION_TESTS=1 uv run pytest tests/test_integrations.py -v --tb=no
```

These checks confirm your credentials work (MongoDB, ElevenLabs, Gemini) without
placing calls, generating content, or writing data. Normal `uv run pytest` skips
them unless `RUN_INTEGRATION_TESTS=1` is set.

Commit `uv.lock` after `uv sync` picks up a `pyproject.toml` change, so dependency
resolution stays reproducible for everyone on the team.
