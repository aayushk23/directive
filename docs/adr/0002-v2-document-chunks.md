# 0002: v2 Document Chunks

## Status

Accepted

## Date

2026-05-23

## Context

The API already returns answers with supporting citation snippets from a hardcoded document catalog. In v1, retrieval searched whole document records, so citations identified the document but not the specific part of the document that supported the answer.

For v2, citations need to identify the specific document chunk used as evidence while keeping the current deterministic behavior and refusal behavior. The project still does not include LLM calls, embeddings, vector storage, document uploads, or a database.

## Decision

The document catalog is represented as chunk-level records. Each `DocumentChunk` includes a `chunk_id`, document metadata, an answer, a citation snippet, and deterministic retrieval keywords.

The retrieval service normalizes the user question, scores each chunk by keyword matches, selects the highest scoring chunk, and uses catalog order as the deterministic tie-breaker. If no chunk receives a qualifying score, the API returns the existing refusal response.

Supported citation responses now include both `document_id` and `chunk_id`.

## Consequences

Supported answers can cite the specific catalog chunk used as evidence while preserving the existing `/ask` response behavior for supported and unsupported questions.

The implementation remains small and inspectable, but chunking is still manual. Adding or changing available documents or chunks requires a code change.

## Tradeoffs

Chunk-level retrieval gives more precise citations than whole-document retrieval without adding infrastructure. It can still miss semantically related questions because matching is keyword-based.

Keeping answers on chunk records avoids a broader document assembly layer. The tradeoff is that related chunks may repeat the same answer when they support the same response.

## Rejected Alternatives

- LLM-generated answers: rejected because current behavior requires deterministic answers with supporting citations and no model calls.
- Embeddings and vector search: rejected because they add infrastructure and ranking behavior outside v2 scope.
- PDF upload pipeline: rejected because uploads are outside the current scope.
- SQL database: rejected because persistence is outside the current scope.
