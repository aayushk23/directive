# 0010: React Question UI

## Status

Accepted

## Date

2026-05-27

## Context

The app already exposes `/ask` for source-supported policy answers. The UI needs
a small internal interface focused on question answering, support status,
citations, refusal reasons, and API errors.

The `/ask` API contract, Postgres-backed retrieval, unsupported-question refusal
behavior, and Docker Compose workflow must remain unchanged.

## Decision

Add a small Vite, React, TypeScript, and Tailwind frontend under `frontend/`.
Run it as the browser UI on `http://127.0.0.1:5173` while FastAPI remains the API
backend on `http://127.0.0.1:8000`.

The React UI calls the existing `/ask` endpoint directly and renders the
response fields already returned by the API: `answer`, `supported`, `citations`,
and `refusal_reason`. FastAPI allows the Vite dev origin through CORS.

The UI uses only the components needed for the current workflow: question entry,
answer status, error handling, and cited source review.

## Consequences

The browser UI has a cleaner component structure and more polished loading,
error, unsupported, and citation states without changing backend behavior.

Local development runs FastAPI and Vite as separate processes. The backend
remains API-only and does not keep a separate plain HTML fallback UI.

## Tradeoffs

This adds a Node frontend workspace and lockfile. The tradeoff is acceptable
because the browser UI now has typed client code and remains decoupled from the
backend API implementation.

The UI remains a single-screen app with no routing, authentication, upload
workflow, dashboard, charting, or admin surface.

## Rejected Alternatives

- Next.js: rejected because the app only needs one client-rendered screen.
- A dashboard layout: rejected because the workflow is a focused question and
  citation view.
- Additional design libraries: rejected because the current UI states are small.
- Expanding API scope: rejected because `/ask` already returns the required
  answer, support, citation, and refusal data.
