# 0005: Quality Gates Before Database Work

## Status

Accepted

## Date

2026-05-24

## Context

The API loads local `.md`, `.txt`, and readable `.pdf` documents, converts them into chunks, retrieves at chunk level, returns citations with `chunk_id`, and refuses questions outside the available document set.

The next likely infrastructure step is database-backed storage or retrieval. Before adding that complexity, the project needs a small CI quality gate that verifies style, formatting, tests, basic application security checks, and dependency vulnerability status.

Postgres, pgvector, embeddings, LLM calls, frontend code, authentication, Docker, cloud deployment, and API behavior changes remain outside this scope.

## Decision

Add a GitHub Actions CI workflow that runs on pull requests and pushes to `main`.

The workflow installs the project with development dependencies, then runs Ruff linting, Ruff format checking, the pytest suite, Bandit over `app/`, and pip-audit for dependency vulnerability scanning.

Add Dependabot updates for Python dependencies and GitHub Actions so the project receives small, regular dependency maintenance.

## Consequences

Pull requests and changes to `main` will have a consistent quality gate before database work begins.

The checks remain local to the current Python application and do not require external services, databases, containers, or cloud infrastructure.

## Tradeoffs

Adding security and dependency scans can fail builds for issues outside the application code, such as newly disclosed dependency vulnerabilities. That is acceptable because the project should surface those risks before adding more infrastructure.

Keeping the workflow small avoids a broader release pipeline. The tradeoff is that packaging, coverage thresholds, deployment validation, and service integration checks are still outside scope.

## Rejected Alternatives

- Adding database integration checks: rejected because database work is not in the current scope.
- Adding Docker-based CI: rejected because Docker is outside the current scope.
- Adding coverage thresholds: rejected because the current goal is a small baseline quality gate.
- Adding deployment checks: rejected because cloud deployment is outside the current scope.
