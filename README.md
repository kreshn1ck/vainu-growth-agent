# Vainu Growth Agent

A small evidence-first account qualification service built around the Vainu Organizations API.

The idea is deliberately simple: **use structured company data to find candidates, then use an LLM only where semantic judgment adds value.** The service retrieves companies from Vainu, evaluates each one against a natural-language Ideal Customer Profile (ICP), and returns a ranked assessment with evidence and explicit unknowns.

## Why this exists

Commercial AI agents should be measurable and grounded. An account-scoring agent that invents company facts is worse than the manual process it replaces. This project separates the workflow into two stages:

1. **Deterministic retrieval** — Vainu filters the candidate set using structured criteria such as country, revenue, employee count, and industry.
2. **Evidence-based assessment** — a scorer evaluates fit against the ICP and returns structured reasons, evidence, and unknowns.

The default mode is fully local and deterministic so the project can be run and tested without credentials. Real Vainu data and AWS Bedrock can be enabled through environment variables.

## Architecture

```text
Client
  |
  v
FastAPI /v1/qualify
  |
  +--> VainuClient
  |      |-- mock dataset (default)
  |      `-- Vainu Organizations API
  |
  `--> Scorer
         |-- deterministic rules (default)
         `-- AWS Bedrock LLM
                |
                v
      Pydantic-validated structured output
```

## What it demonstrates

- Python + FastAPI backend
- Vainu Organizations API integration
- JWT refresh-token handling
- structured firmographic filtering
- optional Amazon Bedrock LLM evaluation
- grounded prompts and structured outputs
- explicit unknowns instead of fabricated evidence
- named regression/evaluation cases that can go red
- Docker and GitHub Actions

## Quick start — no credentials required

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open Swagger at `http://localhost:8000/docs`.

Example request:

```bash
curl -X POST http://localhost:8000/v1/qualify \
  -H 'Content-Type: application/json' \
  -d '{
    "description": "B2B software companies that sell to other businesses and are large enough to have a structured sales team",
    "database": "SE",
    "industry_code": "62",
    "min_revenue": 5000000,
    "max_revenue": 50000000,
    "min_employees": 30,
    "max_employees": 200,
    "limit": 10
  }'
```

## Use the real Vainu API

Vainu's current Organizations API supports structured filtering over company fields. Trial credentials use a refresh token to obtain a short-lived access token.

Set:

```env
USE_MOCK_VAINU=false
VAINU_REFRESH_TOKEN=your-refresh-token
```

The service posts to:

```text
POST https://api.vainu.io/api/v3/organizations/
```

The Vainu token URL is configurable because authentication endpoints can differ by credential setup:

```env
VAINU_TOKEN_URL=https://api.vainu.io/api/token_authentication/refresh/
```

Never commit `.env` or tokens.

## Enable AWS Bedrock scoring

The default `rules` scorer is intentionally deterministic so tests and the demo work anywhere. To use an LLM:

```env
SCORER_MODE=bedrock
AWS_REGION=eu-north-1
BEDROCK_MODEL_ID=<a Bedrock model available in your account>
```

The Bedrock scorer uses the Converse API with temperature `0`, asks for JSON-only output, validates the result with Pydantic, and instructs the model to use only the supplied company facts.

## Evaluation

This repo treats evaluation as a first-class part of the agent.

```bash
pytest -q
python scripts/evaluate.py
```

`evaluation/golden_cases.json` contains named cases with an expected ordering. They are deliberately easy to inspect and extend. A production version would add historical outcomes, reviewer labels, precision/recall by segment, cost/latency tracking, and regression gates in CI.

## What I would build next

1. Add Vainu signals and company-change events as triggers.
2. Add an MCP server so other agents can invoke company search and qualification as tools.
3. Add CRM actions behind an approval boundary: create/update opportunity, write account notes, and propose outreach.
4. Store traces and evaluation results for prompt/model comparisons.
5. Add a customer-health mode combining product usage, CRM history, support conversations, renewal timing, and Vainu signals.

That last step turns this from an ICP qualification service into the broader **renewal and expansion agent** I would prioritize in a commercial organization: evidence in, measurable action out, human escalation when confidence is low or the interaction is high-value.

## API reference used

- Vainu Developer Hub: https://developers.vainu.com/
- Organizations API / filtering: https://developers.vainu.com/docs/filtering-company-data
- API trial: https://developers.vainu.com/docs/vainu-api-trial

## License

MIT
