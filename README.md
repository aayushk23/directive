# Enterprise Policy & Document Copilot

Small FastAPI service for answering employee policy questions from documents stored in Postgres.

The current version indexes local Markdown, text, and readable PDF files from
`documents/` into Postgres tables for document records and document chunks. Each
stored chunk includes a deterministic local embedding vector for pgvector-backed
retrieval. The `/ask` endpoint reads stored chunks from Postgres, uses vector
retrieval with deterministic keyword matching as a fallback, and returns answers
only when the stored document set supports the question.

Supported answers include a citation with `document_id`, `title`, `chunk_id`, and
`snippet`. Unsupported questions return a refusal response. The local embedding
provider is deterministic and dependency-free; it is not an external model
embedding service.

## Docker Compose Local Runtime

Build and start the local runtime:

```bash
docker compose up --build
```

In a second terminal, index local documents into the runtime database:

```bash
docker compose run --rm api_service python -m app.commands.index_documents --documents-path documents
```

The API runs at `http://127.0.0.1:8000`.

Check health:

```bash
curl http://127.0.0.1:8000/health
```

Ask a supported question:

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the password rotation policy?"}'
```

The Compose app container uses the runtime database:

```text
DATABASE_URL=postgresql://postgres:postgres@postgres_service:5432/policy_copilot
```

In v0.8.0, the Compose Postgres service uses a pgvector-enabled image. Postgres
data is stored in the persistent `postgres_data` volume. Re-run the indexing
command after changing files in `documents/`.

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

Start a local Postgres that has pgvector installed, create the local database,
and point the app at it:

```bash
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres createdb policy_copilot
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_copilot"
```

This `DATABASE_URL` is for running the app locally against the runtime database.
The database must have the pgvector extension available because schema creation
enables `vector` and stores `chunk_embedding` values. The Docker Compose runtime
above is the simplest pgvector-enabled local setup.

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

Each `##` section becomes one stored document chunk. The chunk citation snippet
and answer come from the first paragraph under that heading. Chunk IDs are
derived from the document ID and heading, such as
`it-password-policy-password-rotation`. The indexing command also stores a
`chunk_embedding` vector for each chunk.

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

## Quality Checks

Run quick local checks:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m bandit -q -r app
python -m pip_audit --skip-editable
```

`python -m pytest -q` is a quick local check. It may skip database-backed tests
when `DATABASE_URL` is not set.

### Test Database

Run the full database-backed test suite against a dedicated test database:

```bash
docker compose up -d postgres_service
docker compose exec postgres_service dropdb -U postgres --if-exists policy_copilot_test
docker compose exec postgres_service createdb -U postgres policy_copilot_test
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_copilot_test" python -m pytest -q -rs
```

Use `policy_copilot_test` for full database-backed tests. Do not run tests
against the `policy_copilot` runtime database. The Compose `postgres_service`
container includes pgvector for these tests.

## Architecture Decision Records

- [0001: v1 deterministic retrieval](docs/adr/0001-v1-deterministic-retrieval.md)
- [0002: v2 document chunks](docs/adr/0002-v2-document-chunks.md)
- [0003: local document ingestion](docs/adr/0003-local-document-ingestion.md)
- [0004: PDF ingestion](docs/adr/0004-pdf-ingestion.md)
- [0005: quality gates before database work](docs/adr/0005-quality-gates-before-database-work.md)
- [0006: Postgres document persistence](docs/adr/0006-postgres-document-persistence.md)
- [0007: Docker Compose local runtime](docs/adr/0007-docker-compose-local-runtime.md)
- [0008: pgvector semantic retrieval](docs/adr/0008-pgvector-semantic-retrieval.md)
