# Enterprise Policy & Document Copilot

Small FastAPI service for answering employee policy questions from documents stored in Postgres.

The current version indexes local Markdown, text, and readable PDF files from `documents/`
into Postgres tables for document records and document chunks. The `/ask` endpoint
reads stored chunks from Postgres and uses deterministic keyword matching. Supported
answers include a citation with `document_id`, `title`, `chunk_id`, and `snippet`.
Unsupported questions return a refusal response.

## Docker Compose Local Runtime

Start Postgres:

```bash
docker compose up -d postgres_service
```

Create the schema and index local documents into Postgres:

```bash
docker compose run --rm api_service policy-copilot-index-documents --documents-path documents
```

Start the API:

```bash
docker compose up api_service
```

The API runs at `http://127.0.0.1:8000`.

Check health:

```bash
curl -s http://127.0.0.1:8000/health
```

Ask a supported question:

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the password rotation policy?"}'
```

The Compose app container uses:

```text
DATABASE_URL=postgresql://postgres:postgres@postgres_service:5432/policy_copilot
```

Postgres data is stored in the persistent `postgres_data` volume. Re-run the
indexing command after changing files in `documents/`.

Stop the services:

```bash
docker compose down
```

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Local Postgres Setup

Start Postgres, create the local database, and point the app at it:

```bash
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres createdb policy_copilot
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_copilot"
```

Create the schema and index local documents into Postgres:

```bash
python -m app.data.schema
python -m app.commands.index_documents --documents-path documents
```

The installed console command is also available:

```bash
policy-copilot-index-documents --documents-path documents
```

## Running the API

```bash
python -m uvicorn app.main:app --reload
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

Policy files live in `documents/` as `.md`, `.txt`, or `.pdf` files. These files are
indexing input; `/ask` reads the stored chunks from Postgres after indexing.

Each file uses a small metadata header followed by `##` chunk headings:

```md
---
document_id: it-password-policy
title: IT Password Policy
category: information-security
---

## Password Rotation

Employees must rotate passwords every 90 days.
```

Each `##` section becomes one stored document chunk. The chunk citation snippet and
answer come from the first paragraph under that heading. Chunk IDs are derived from
the document ID and heading, such as `it-password-policy-password-rotation`.

PDF files must contain readable embedded text. The extracted PDF text uses the same
metadata and `##` heading format as Markdown and text files.

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

Run the test suite with a test Postgres database:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_copilot_test"
pytest
```

Run focused endpoint tests:

```bash
pytest tests/test_ask.py
```

Postgres-backed tests are skipped when `DATABASE_URL` is not set.

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
- [0006: Postgres document persistence](docs/adr/0006-postgres-document-persistence.md)
- [0007: Docker Compose local runtime](docs/adr/0007-docker-compose-local-runtime.md)
