# ScamShield

Opt-in voice scam simulation and awareness training.

This initial scaffold contains a Streamlit home page and a FastAPI health endpoint.
It does not enroll residents, store data, place calls, or connect to external services.

## Local setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
uv sync
```

Start the frontend:

```sh
uv run streamlit run app.py
```

In another terminal, start the backend:

```sh
uv run uvicorn backend.main:app --reload
```

- Frontend: http://localhost:8501
- API health: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

The two services run independently in this initial scaffold.

## Files

```text
app.py              Streamlit frontend entry point
backend/
  __init__.py
  main.py           FastAPI application and health endpoint
pyproject.toml      Dependencies and development tooling
.python-version     Default Python version for uv
.env.example        Placeholders for future integration credentials
```

All frontend work belongs in Streamlit. FastAPI will handle backend operations
and provider webhooks. Planned integrations are ElevenLabs, Twilio, Gemini,
and MongoDB Atlas.

The starter does not load environment files yet. When integrations are added,
keep real credentials in an untracked `.env` or deployment secrets.

## Development

Pytest is included for future behavior tests; no tests are needed for this scaffold.
Commit the generated `uv.lock` after the first successful `uv sync` to make
dependency resolution reproducible.
