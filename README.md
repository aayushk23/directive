# Enterprise Policy & Document Copilot

Small FastAPI service for answering employee policy questions from local documents.

The current version loads Markdown, text, and readable PDF files from `documents/`,
splits them into `##` sections, and answers `/ask` requests when a matching
document chunk is found. Retrieval is deterministic keyword matching. Supported
answers include a citation with the source document and chunk ID. Unsupported
questions return a refusal response.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Running the API

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

Available endpoints:

- `GET /health`
- `POST /ask`

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

Each `##` section becomes one document chunk. The chunk citation snippet and
answer come from the first paragraph under that heading. Chunk IDs are derived
from the document ID and heading, such as
`it-password-policy-password-rotation`.

PDF files must contain readable embedded text. The extracted PDF text uses the
same metadata and `##` heading format as Markdown and text files.

## Example `/ask` Requests

Supported question:

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

Unsupported question:

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

## Tests

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

## Current Limitations

- The document catalog is loaded from local files in `documents/`.
- Documents must include `document_id`, `title`, and `category` metadata.
- Documents must use `##` headings for chunks.
- PDF ingestion extracts embedded text only; scanned PDFs are not supported.
- Retrieval is keyword based and does not use semantic search.
- There is no file upload endpoint, database, Docker setup, frontend,
  authentication, access control, audit logging, or cloud deployment setup.

## ADRs

- [0001: v1 deterministic retrieval](docs/adr/0001-v1-deterministic-retrieval.md)
- [0002: v2 document chunks](docs/adr/0002-v2-document-chunks.md)
- [0003: local document ingestion](docs/adr/0003-local-document-ingestion.md)
- [0004: PDF ingestion](docs/adr/0004-pdf-ingestion.md)
- [0005: quality gates before database work](docs/adr/0005-quality-gates-before-database-work.md)
