# 0001: v1 Deterministic Retrieval

## Status

Accepted

## Date

2026-05-23

## Context

Enterprise Policy & Document Copilot must answer employee questions only from the v1 document set. The current version needs a clear response contract: source-supported answers include citations, and unsupported questions receive refusal responses.

The project is not ready for embeddings, vector storage, document ingestion, authentication, or model-generated answers. Those choices add infrastructure and operational behavior before the response contract is stable.

## Decision

The current version uses in-process deterministic keyword retrieval over a hardcoded document catalog.

Each document defines an answer, citation snippet, and a small set of keywords. The retrieval service normalizes the user question, scores each document by keyword matches, selects the highest scoring document, and uses catalog order as the deterministic tie-breaker. If no document receives a qualifying score, the API returns a refusal response.

## Consequences

Supported answers are stable, testable, and directly tied to the document catalog. Unsupported questions refuse consistently instead of guessing.

The retrieval implementation is intentionally limited. It will miss some semantically related questions and does not support document uploads, access control, or personalized permissions.

## Tradeoffs

Deterministic keyword retrieval is less flexible than semantic search, but it is easier to evaluate and audit. For v1, explainability and stable policy boundaries are more important than broad recall.

The hardcoded catalog keeps the implementation small and transparent. The tradeoff is that adding or changing included documents requires a code change.

## Rejected Alternatives

- LLM-generated answers: rejected because the current version requires source-grounded deterministic behavior without model calls.
- Embeddings and vector search: rejected because they add infrastructure and nondeterministic ranking before the API contract is proven.
- PDF upload pipeline: rejected because uploads are outside the current scope.
- SQL database: rejected because persistence is outside the current scope.
- External search service: rejected because the service should avoid hidden network calls and external operational dependencies.
