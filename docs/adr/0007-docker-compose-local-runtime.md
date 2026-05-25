# 0007: Docker Compose Local Runtime

## Status

Accepted

## Date

2026-05-25

## Context

The API stores document records and document chunks in Postgres. Local `.md`,
`.txt`, and readable `.pdf` files remain indexing input, while `/ask` reads the
stored chunks from Postgres at query time.

The existing local workflow requires a developer to install, start, and configure
Postgres manually. v0.7.0 needs a consistent local runtime for the API and
Postgres while preserving the non-Docker workflow, deterministic retrieval,
citations, and unsupported-question refusal behavior.

## Decision

Add a Dockerfile for the FastAPI app and a Docker Compose file with an
`api_service`, a `postgres_service`, and a persistent `postgres_data` volume.

The app container receives `DATABASE_URL` pointing at the Compose Postgres
service. The API starts with Uvicorn and continues to read document chunks from
Postgres. Document indexing remains an explicit command run from the app image:

```bash
docker compose run --rm api_service policy-copilot-index-documents --documents-path documents
```

## Consequences

Developers can start local Postgres and the API without manually configuring a
host Postgres service. The stored document index persists across container
restarts through the named volume.

The local non-Docker workflow still works by setting `DATABASE_URL` to a host
Postgres database and running the same indexing command.

## Tradeoffs

Keeping indexing explicit avoids hiding document-index updates inside container
startup. The tradeoff is that developers must run the indexing command after
starting Postgres and after changing local document files.

The Docker setup is intended for local runtime consistency, not production
hardening.

## Rejected Alternatives

- Running indexing automatically before every API start: rejected because it
  makes startup behavior dependent on local files and obscures when the stored
  document index changes.
- Adding pgvector or embeddings: rejected because retrieval remains deterministic
  keyword matching.
- Adding LLM calls: rejected because answers remain source-supported and
  deterministic.
- Adding cloud deployment, Kubernetes, authentication, RBAC, or frontend code:
  rejected because v0.7.0 is limited to a local Docker Compose runtime.
