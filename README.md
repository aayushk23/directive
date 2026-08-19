# Directive

Local MVP for asking source-supported questions against a small enterprise policy
document set.

The backend indexes local Markdown, text, and readable PDF documents from
`documents/` into Postgres. Stored chunks include deterministic local embedding
vectors for pgvector retrieval, with keyword retrieval as a fallback. The
FastAPI `/ask` endpoint returns an answer only when the indexed document set
supports the question. Unsupported questions return a refusal response.

The frontend in `frontend/` is a Vite, React, TypeScript, and Tailwind UI for
asking questions and reviewing cited source snippets. The app does not generate
answers with an external model.

Current version: `1.0.0`

## Repository Structure

```text
app/                 FastAPI backend, indexing command, data access, retrieval
documents/           Local sample documents used as indexing input
docs/adr/            Architecture decision records
docs/demo-script.md  Short walkthrough for showing the local MVP
frontend/            Vite React frontend
tests/               Backend tests
docker-compose.yml   Local Postgres with pgvector and FastAPI runtime
Dockerfile           Backend container image
pyproject.toml       Python package metadata and dev dependencies
```

## Run With Docker Compose

Docker Compose is the simplest local path because it starts Postgres with
pgvector and the FastAPI backend together.

Build and start the local runtime:

```bash
docker compose up --build
```

In a second terminal, index the local documents into the Compose database:

```bash
docker compose run --rm api_service policy-copilot-index-documents --documents-path documents
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

Ask an unsupported question:

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the cafeteria menu today?"}'
```

Re-run the indexing command after changing files in `documents/`.

Stop the services:

```bash
docker compose down
```

To remove the persisted local database volume:

```bash
docker compose down --volumes
```

## Frontend Development

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the frontend while FastAPI is running on port `8000`:

```bash
npm run dev
```

The Vite dev server runs at `http://127.0.0.1:5173` and proxies `/ask` and
`/health` to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` only if the API is
running somewhere else.

Build static frontend assets:

```bash
npm run build
```

## Python Local Setup

Use this path if you want to run the backend outside Docker. The database still
needs Postgres with pgvector available.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Point the app at a local Postgres database:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/policy_copilot"
```

Create the schema and index local documents:

```bash
python -m app.data.schema
python -m app.commands.index_documents --documents-path documents
```

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

Available endpoints:

- `GET /health`
- `POST /ask`

## Local Documents

Policy files live in `documents/` as `.md`, `.txt`, or readable `.pdf` files.
These files are indexing input. The `/ask` endpoint reads stored chunks from
Postgres after indexing.

Markdown and text files use a small metadata header followed by `##` chunk
headings:

```md
---
document_id: it-password-policy
title: IT Password Policy
category: information-security
owner: IT Security
source_date: 2026-01-15
document_version: 2026.1
---

## Password Rotation

Employees must rotate passwords every 90 days.
```

Each `##` section becomes one stored document chunk. Chunk IDs are derived from
the document ID and heading, such as
`it-password-policy-password-rotation`.

PDF files must contain readable embedded text. Extracted PDF text is parsed with
the same metadata and `##` heading format.

## Quality Checks

Backend checks:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m bandit -q -r app
python -m pip_audit --skip-editable .
```

Frontend check:

```bash
cd frontend
npm run build
```

## Demo

Use [docs/demo-script.md](docs/demo-script.md) for a short local walkthrough with
sample questions and expected outcomes.
