# Enterprise Policy & Document Copilot

## Project Intent

Build a small document retrieval API for enterprise policy questions. The service answers only when the current document set contains supporting evidence, and supported answers include citation snippets.

Unsupported questions should return a refusal response. They are a normal product outcome, not an exception path.

## Current Scope

- FastAPI backend
- `POST /ask` endpoint
- Hardcoded document catalog
- Deterministic in-process retrieval
- Citation snippets for supported answers
- Consistent refusal response for unsupported questions
- Basic endpoint tests
- README and one architecture decision record

## Repository Layout

```text
.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── data/
│   │   └── document_catalog.py
│   ├── models/
│   │   └── ask.py
│   └── services/
│       └── retrieval.py
├── docs/
│   └── adr/
│       └── 0001-v1-deterministic-retrieval.md
└── tests/
    └── test_ask.py
```

## Development Commands

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Exercise the endpoint:

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the password rotation policy?"}'
```

Run tests:

```bash
pytest
pytest tests/test_ask.py
```

## Coding Standards

- Use FastAPI and Pydantic for API boundaries.
- Keep retrieval deterministic, in-process, and easy to inspect.
- Keep available documents as simple structured Python data.
- Keep routing, request/response models, and retrieval logic separated.
- Prefer explicit response models over ad hoc dictionaries.
- Keep refusal wording consistent and covered by tests.
- Avoid hidden network calls, external services, environment-dependent behavior, and nondeterministic ranking.
- Use domain names such as document catalog, available documents, citations, refusal, retrieval, and evidence.

## Documentation Standards

- Describe the current implementation directly.
- Keep examples accurate and runnable.
- State limitations plainly.
- Keep ADRs focused on decisions, context, tradeoffs, consequences, and rejected alternatives.

## Current Boundaries

Do not add LLM calls, embeddings, vector databases, uploads, Postgres, Docker, frontend code, authentication, RBAC, audit logs, or cloud deployment without an explicit scope change.
