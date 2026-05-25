# 0006: Postgres Document Persistence

## Status

Accepted

## Date

2026-05-24

## Context

The API loads local `.md`, `.txt`, and readable `.pdf` files, converts them into
chunks, retrieves at chunk level, returns citations with `document_id`, `title`,
`chunk_id`, and `snippet`, and refuses questions outside the available document
set.

Loading the local files at API startup keeps the implementation small, but it ties
runtime availability to local file ingestion. For v0.6.0, document records and
document chunks need to be stored in Postgres while preserving deterministic
retrieval and the existing `/ask` response contract.

pgvector, embeddings, LLM calls, frontend code, authentication, RBAC, cloud
deployment, upload workflows, and Docker Compose are outside this scope.

## Decision

Store document records in a `documents` table and chunk records in a
`document_chunks` table. The schema is created by a small idempotent SQL function.

Add an indexing command that reads local `.md`, `.txt`, and readable `.pdf` files
from the documents directory, reuses the existing parser and chunker, and writes
the resulting document records and chunks to Postgres. Local files remain indexing
input, not the runtime source for `/ask`.

Update retrieval so `/ask` loads stored chunks from Postgres, scores them with the
existing deterministic keyword matcher, and returns the same supported response or
unsupported refusal shape as before.

## Consequences

The API no longer depends on loading local documents into an in-memory catalog at
startup. Document changes become a database indexing operation, and `/ask` reads
the current stored chunk set.

The retrieval behavior remains lexical and deterministic. Citations still identify
the source document and supporting chunk. If no stored chunk meets the support
threshold, the API returns the existing refusal response.

## Tradeoffs

Using direct `psycopg` calls keeps v0.6.0 small and avoids an ORM or migration
framework for a single initial schema. The tradeoff is that future schema changes
will need either explicit SQL updates or a migration tool.

Indexing local files into Postgres is operationally simple and keeps uploads out
of scope. The tradeoff is that documents are still managed outside the API.

## Rejected Alternatives

- Continuing startup-only local file ingestion: rejected because v0.6.0 stores
  document records and chunks in Postgres.
- Adding pgvector or embeddings: rejected because retrieval remains deterministic
  keyword matching.
- Adding LLM calls: rejected because answers remain source-supported and
  deterministic.
- Adding upload endpoints: rejected because local file indexing is the current
  document update path.
- Adding SQLAlchemy and Alembic: rejected because a small direct Postgres layer is
  sufficient for the initial schema.
- Adding Docker Compose: rejected because CI can use a Postgres service and local
  testing only requires an existing Postgres database.
