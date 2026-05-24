# 0004: PDF Ingestion

## Status

Accepted

## Date

2026-05-24

## Context

The API loads local documents, converts them into chunks, retrieves at chunk level, and returns citations with `document_id`, `title`, `chunk_id`, and `snippet`. In v3, local ingestion supports `.md` and `.txt` files only.

The current scope is local PDF ingestion. The service still needs deterministic in-process retrieval, the existing `/ask` response contract, chunk-level citations, and the same refusal behavior for unsupported questions. Uploads, LLM calls, embeddings, vector databases, Postgres, Docker, frontend code, authentication, RBAC, audit logs, and cloud deployment remain outside scope.

## Decision

Local `.pdf` files are included in the document catalog alongside `.md` and `.txt` files. PDF text is extracted with `pypdf`, then parsed with the same metadata and `##` heading format used by existing local documents.

The extracted PDF text is converted into the existing `DocumentChunk` model. Chunk IDs, citation snippets, answers, and keywords are derived the same way for PDF-backed documents as they are for Markdown and text documents.

The `/ask` endpoint response shape is unchanged. Retrieval remains deterministic keyword matching over chunks, and unsupported questions return the existing refusal response.

## Consequences

PDF-backed policy documents can now participate in the local document catalog without adding external services or changing API responses.

PDF ingestion depends on readable embedded text. Scanned PDFs without extractable text are not supported, and malformed PDF-backed documents fail during catalog loading like malformed Markdown or text documents.

## Tradeoffs

Using `pypdf` keeps the implementation local and small. The tradeoff is that extraction quality depends on the PDF text layer and does not attempt layout reconstruction or OCR.

Reusing the existing metadata and heading format keeps chunking consistent across file types. The tradeoff is that PDFs must be authored with this simple text structure to become usable catalog documents.

## Rejected Alternatives

- OCR for scanned PDFs: rejected because image extraction and OCR are outside v4 scope.
- File upload endpoint: rejected because v4 only adds local PDF ingestion.
- LLM-based PDF parsing: rejected because current behavior requires deterministic local processing and no model calls.
- Embeddings and vector search: rejected because they add ranking behavior and infrastructure outside v4 scope.
- SQL database storage: rejected because persistence outside local files is outside scope.
