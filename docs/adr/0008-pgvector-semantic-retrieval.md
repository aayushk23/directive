# 0008: pgvector Semantic Retrieval

## Status

Accepted

## Date

2026-05-26

## Context

The API stores document records and document chunks in Postgres. The `/ask`
endpoint returns the existing response shape, including source citations with
`document_id`, `title`, `chunk_id`, and `snippet`, and refuses questions that are
unsupported by the current document set.

Retrieval has been deterministic keyword matching. That behavior is simple and
auditable, but it is lexical and can miss related wording. v0.8.0 needs
pgvector-backed semantic retrieval over stored chunks while preserving the
existing answer contract, citation fields, and refusal behavior.

## Decision

Enable the pgvector extension in the schema and add a nullable
`chunk_embedding vector(64)` column to `document_chunks`.

The local indexing command computes and stores one `chunk_embedding` for each
document chunk. The embedding provider is a small deterministic local hash-based
provider. It does not call an external embedding API and does not represent a
production model embedding service.

Retrieval embeds the incoming question with the same provider, queries
`document_chunks` using pgvector cosine distance, and returns the best chunk only
when the vector similarity clears the support threshold. If vector retrieval
does not find a supported chunk, retrieval falls back to the existing
deterministic keyword scorer. If neither path finds support, `/ask` returns the
existing refusal response.

Docker Compose uses a pgvector-enabled Postgres image so local schema creation
can enable the `vector` extension.

The current dataset is small, so vector retrieval uses exact pgvector ordering
without an approximate vector index.

## Consequences

Stored chunks now carry vector data that can be queried directly in Postgres.
The `/ask` response remains unchanged, and citations still point to the stored
supporting chunk.

The deterministic keyword path remains available as a fallback and keeps current
unsupported-question behavior from depending only on vector similarity.

The local embedding provider keeps v0.8.0 small and dependency-free. Its
tradeoff is that retrieval is not equivalent to using a trained embedding model.

## Tradeoffs

Using direct SQL with `psycopg` keeps the data layer consistent with the rest of
the repository and avoids adding an ORM, migration framework, or pgvector Python
adapter for this small change.

Keeping `chunk_embedding` nullable allows older chunk rows to exist until they
are reindexed. Vector retrieval ignores rows without embeddings, and keyword
retrieval remains available.

Deferring an approximate vector index avoids tuning index parameters before the
dataset needs them.

## Rejected Alternatives

- Calling an external embedding API during indexing: rejected because v0.8.0
  should stay small, local, and honest about what capability is present.
- Generating answers with an LLM: rejected because answers continue to come from
  stored chunk content and must preserve the existing `/ask` contract.
- Removing deterministic keyword retrieval: rejected because it is still useful
  as a fallback and comparison path.
- Adding non-retrieval product or deployment features: rejected because those are
  outside the v0.8.0 retrieval scope.
