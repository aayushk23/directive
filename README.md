# Enterprise Policy & Document Copilot

Small document retrieval API for answering employee questions from an included enterprise document catalog.

The current version provides one FastAPI question-answering endpoint. It answers only from the included document catalog, returns citation snippets for supported answers, and uses consistent refusal behavior when the current document set does not support the question.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## API Contract

### `POST /ask`

Request:

```json
{
  "question": "What is the password rotation policy?"
}
```

Response:

```json
{
  "answer": "string",
  "supported": true,
  "citations": [
    {
      "document_id": "string",
      "title": "string",
      "snippet": "string"
    }
  ],
  "refusal_reason": null
}
```

For unsupported questions, `supported` is `false`, `citations` is an empty list, and `answer` contains the refusal message.

## Supported Response

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the password rotation policy?"}'
```

```json
{
  "answer": "Employees must rotate passwords every 90 days and immediately report suspected account compromise to IT Security.",
  "supported": true,
  "citations": [
    {
      "document_id": "it-password-policy",
      "title": "IT Password Policy",
      "snippet": "Employees must rotate passwords every 90 days. Employees who suspect account compromise must immediately contact IT Security."
    }
  ],
  "refusal_reason": null
}
```

## Refusal Response

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the cafeteria menu today?"}'
```

```json
{
  "answer": "I cannot answer this question from the current document set.",
  "supported": false,
  "citations": [],
  "refusal_reason": "Unsupported by available documents."
}
```

## Current Limitations

- The document catalog is hardcoded in `app/data/document_catalog.py`.
- Retrieval is deterministic keyword matching, not semantic search.
- There are no LLM calls, embeddings, uploads, database, Docker setup, frontend, authentication, access control, audit logs, or cloud deployment.
- Adding or changing included documents requires a code change.

## Development

Run the test suite:

```bash
pytest
```

Run focused endpoint tests:

```bash
pytest tests/test_ask.py
```

## Architecture Decision Records

- [0001: v1 deterministic retrieval](docs/adr/0001-v1-deterministic-retrieval.md)
