# Enterprise Policy & Document Copilot

Small document retrieval API for answering employee questions from included local policy documents.

The API provides one FastAPI question-answering endpoint. It loads local Markdown, text, or readable PDF files from `documents/`, converts them into chunks, searches chunks with deterministic keyword matching, returns citation snippets with chunk identifiers for supported answers, and uses consistent refusal behavior when the current document set does not support the question.

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
  "answer": "Employees must rotate passwords every 90 days.",
  "supported": true,
  "citations": [
    {
      "document_id": "it-password-policy",
      "chunk_id": "it-password-policy-password-rotation",
      "title": "IT Password Policy",
      "snippet": "Employees must rotate passwords every 90 days."
    }
  ],
  "refusal_reason": null
}
```

For unsupported questions, `supported` is `false`, `citations` is an empty list, and `answer` contains the refusal message.

## Local Documents

Policy files live in `documents/` as `.md`, `.txt`, or `.pdf` files. Each file uses a small metadata header followed by `##` chunk headings:

```md
---
document_id: it-password-policy
title: IT Password Policy
category: information-security
---

## Password Rotation

Employees must rotate passwords every 90 days.
```

Each `##` section becomes one document chunk. The chunk citation snippet and answer come from the first paragraph under that heading. Chunk IDs are derived from the document ID and heading, such as `it-password-policy-password-rotation`.

PDF files must contain readable embedded text. The extracted PDF text uses the same metadata and `##` heading format as Markdown and text files. Scanned PDFs without extractable text are not supported.

## Supported Response

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the password rotation policy?"}'
```

```json
{
  "answer": "Employees must rotate passwords every 90 days.",
  "supported": true,
  "citations": [
    {
      "document_id": "it-password-policy",
      "chunk_id": "it-password-policy-password-rotation",
      "title": "IT Password Policy",
      "snippet": "Employees must rotate passwords every 90 days."
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

- The document catalog is loaded from local `.md`, `.txt`, and readable `.pdf` files in `documents/`.
- Local documents must include `document_id`, `title`, and `category` metadata and `##` chunk headings.
- PDF ingestion extracts embedded text only; there is no OCR for scanned PDFs.
- Retrieval is deterministic keyword matching over chunks, not semantic search.
- There are no LLM calls, embeddings, uploads, database, Docker setup, frontend, authentication, access control, audit logs, or cloud deployment.
- There is no file upload endpoint.

## Development

Run the test suite:

```bash
pytest
```

Run focused endpoint tests:

```bash
pytest tests/test_ask.py
```

## Quality Checks

Run the same checks used by CI:

```bash
ruff check .
ruff format --check .
python -m pytest -q
bandit -r app/
pip-audit
```

## Architecture Decision Records

- [0001: v1 deterministic retrieval](docs/adr/0001-v1-deterministic-retrieval.md)
- [0002: v2 document chunks](docs/adr/0002-v2-document-chunks.md)
- [0003: local document ingestion](docs/adr/0003-local-document-ingestion.md)
- [0004: PDF ingestion](docs/adr/0004-pdf-ingestion.md)
- [0005: quality gates before database work](docs/adr/0005-quality-gates-before-database-work.md)
