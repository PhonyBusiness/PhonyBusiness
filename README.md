# PhonyBusiness

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

Populate `.env` using the keys in `.env.example`, then run the live integration checks:

```sh
uv sync
RUN_INTEGRATION_TESTS=1 uv run pytest tests/test_integrations.py -v --tb=no
```

The seven checks cover MongoDB connectivity, Twilio account status, phone number
ownership and voice/SMS capabilities, Twilio Verify service access, ElevenLabs
user and agent access, and Gemini model listing. Missing values fail their checks.
Shell environment variables override `.env` values.

These checks do not place calls, send messages, generate content, or write data.
They do not prove end-to-end call routing, model generation quota, or database
read/write permissions. Restricted ElevenLabs keys need user-read and agent-read
access for both checks to pass. Provider response bodies and credentials are not
printed; avoid pytest `--showlocals` when working with secrets.

Normal `uv run pytest` skips live checks unless `RUN_INTEGRATION_TESTS=1` is set.

Commit the generated `uv.lock` after the first successful `uv sync` to make
dependency resolution reproducible.
