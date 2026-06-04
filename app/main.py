from typing import Annotated

from fastapi import Body, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Connection

from app.data.database import db_session
from app.models.ask import ASK_REQUEST_EXAMPLE, AskRequest, AskResponse, Citation
from app.services.retrieval import (
    REFUSAL_ANSWER,
    REFUSAL_REASON,
    retrieve_supported_chunk,
)


app = FastAPI(
    title="Enterprise Policy Copilot API",
    version="1.0.0",
    description="Document retrieval API for answering questions from the current enterprise document set.",
    openapi_tags=[
        {
            "name": "Knowledge Retrieval",
            "description": "Source-supported answers from the current document set.",
        },
        {
            "name": "Platform",
            "description": "Operational endpoints for API availability.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get(
    "/health",
    tags=["Platform"],
    summary="Check API health",
    operation_id="check_api_health",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/ask",
    response_model=AskResponse,
    tags=["Knowledge Retrieval"],
    summary="Answer a policy question",
    description=(
        "Returns an answer only when the question is supported by the current "
        "document set. If the document catalog does not contain supporting "
        "evidence, the API returns an unsupported refusal."
    ),
    response_description="An answer with citations or an unsupported refusal.",
    operation_id="answer_policy_question",
)
async def ask(
    request: Annotated[AskRequest, Body(examples=[ASK_REQUEST_EXAMPLE])],
    connection: Annotated[Connection, Depends(db_session)],
) -> AskResponse:
    retrieval_result = retrieve_supported_chunk(request.question, connection)

    if not retrieval_result.supported or retrieval_result.chunk is None:
        return AskResponse(
            answer=REFUSAL_ANSWER,
            supported=False,
            citations=[],
            refusal_reason=REFUSAL_REASON,
        )

    chunk = retrieval_result.chunk
    return AskResponse(
        answer=chunk.answer,
        supported=True,
        citations=[
            Citation(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                category=chunk.category,
                owner=chunk.owner,
                source_date=chunk.source_date,
                document_version=chunk.document_version,
                snippet=chunk.citation_snippet,
            )
        ],
        refusal_reason=None,
    )
