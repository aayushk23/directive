# 0003: Local Document Ingestion

## Status

Accepted

## Date

2026-05-24

## Context

The API answers only when the available document set contains supporting evidence. In v2, the document catalog was represented as hardcoded Python chunk records. That kept retrieval deterministic and easy to inspect, but adding or changing policy text required editing application code.

For v3, the current scope is local document ingestion only. The service still needs deterministic in-process retrieval, chunk-level citations, and the existing refusal behavior. PDF parsing, uploads, LLM calls, embeddings, vector databases, Postgres, Docker, frontend code, authentication, RBAC, audit logs, and cloud deployment remain outside scope.

## Decision

Policy documents are stored as local `.md` or `.txt` files in `documents/`. Each file has required metadata for `document_id`, `title`, and `category`, followed by `##` headings. Each heading section becomes one `DocumentChunk`.

At import time, `app/data/document_catalog.py` loads the local files through the ingestion service and exposes `DOCUMENT_CATALOG` for retrieval. Files are sorted by filename, chunk IDs are derived from the document ID and heading, and keyword terms are derived deterministically from the loaded title, heading, and chunk body.

The `/ask` endpoint response shape is unchanged. Supported answers return citations with `document_id`, `title`, `chunk_id`, and `snippet`. Unsupported questions return the existing refusal response.

## Consequences

Policy text now lives in local document files instead of hardcoded Python records. The implementation remains small and inspectable, and tests can exercise loading and chunk creation without external services.

The retrieval quality is still limited to deterministic keyword matching. Document files must follow the local metadata and heading format, and malformed local documents fail during catalog loading.

## Tradeoffs

Local document ingestion makes document updates clearer while avoiding new infrastructure. The tradeoff is that this is not a general document management system: there is no upload flow, PDF parser, database, or semantic ranking.

Deriving keywords from document text keeps the catalog free of manual keyword records. The tradeoff is that matching remains lexical and can miss questions that use different wording.

## Rejected Alternatives

- Keeping hardcoded Python records: rejected because v3 moves policy text into local documents.
- LLM-generated answers: rejected because current behavior requires deterministic answers with supporting citations and no model calls.
- Embeddings and vector search: rejected because they add infrastructure and ranking behavior outside v3 scope.
- PDF parsing and upload endpoints: rejected because local `.md` and `.txt` ingestion is the current scope.
- SQL database: rejected because persistence outside local files is outside scope.
