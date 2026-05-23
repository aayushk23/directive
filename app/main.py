from typing import Annotated

from fastapi import Body, FastAPI

from app.models.ask import ASK_REQUEST_EXAMPLE, AskRequest, AskResponse, Citation
from app.services.retrieval import REFUSAL_ANSWER, REFUSAL_REASON, retrieve_supported_document


app = FastAPI(
    title="Enterprise Policy Copilot API",
    version="0.1.0",
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
    response_description="A grounded answer with citations or an unsupported refusal.",
    operation_id="answer_policy_question",
)
async def ask(
    request: Annotated[AskRequest, Body(examples=[ASK_REQUEST_EXAMPLE])],
) -> AskResponse:
    retrieval_result = retrieve_supported_document(request.question)

    if not retrieval_result.supported or retrieval_result.document is None:
        return AskResponse(
            answer=REFUSAL_ANSWER,
            supported=False,
            citations=[],
            refusal_reason=REFUSAL_REASON,
        )

    document = retrieval_result.document
    return AskResponse(
        answer=document.answer,
        supported=True,
        citations=[
            Citation(
                document_id=document.document_id,
                title=document.title,
                snippet=document.citation_snippet,
            )
        ],
        refusal_reason=None,
    )
