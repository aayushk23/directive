import pytest
from httpx import ASGITransport, AsyncClient
from psycopg import Connection

from app.commands.index_documents import index_documents
from app.main import app
from app.services.retrieval import REFUSAL_ANSWER, REFUSAL_REASON
from tests.pdf_fixture import write_readable_pdf


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def indexed_default_documents(app_db_session: Connection) -> None:
    index_documents()


async def post_ask(question: str):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        return await client.post("/ask", json={"question": question})


async def test_supported_password_question_returns_answer_with_citation() -> None:
    response = await post_ask("What is the password rotation policy?")

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["answer"] == "Employees must rotate passwords every 90 days."
    assert body["refusal_reason"] is None
    assert body["citations"] == [
        {
            "document_id": "it-password-policy",
            "chunk_id": "it-password-policy-password-rotation",
            "title": "IT Password Policy",
            "category": "information-security",
            "owner": "IT Security",
            "source_date": "2026-01-15",
            "document_version": "2026.1",
            "snippet": "Employees must rotate passwords every 90 days.",
        }
    ]


async def test_supported_account_compromise_question_returns_it_security_citation() -> (
    None
):
    response = await post_ask(
        "What should employees do if they suspect account compromise"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["refusal_reason"] is None
    assert body["answer"] == (
        "Employees who suspect account compromise must immediately contact IT Security."
    )
    assert body["citations"][0]["document_id"] == "it-password-policy"
    assert body["citations"][0]["chunk_id"] == "it-password-policy-account-compromise"
    assert body["citations"][0]["title"] == "IT Password Policy"
    assert body["citations"][0]["owner"] == "IT Security"
    assert body["citations"][0]["source_date"] == "2026-01-15"
    assert body["citations"][0]["document_version"] == "2026.1"
    assert "account compromise" in body["citations"][0]["snippet"]
    assert "contact IT Security" in body["citations"][0]["snippet"]


async def test_supported_remote_work_question_returns_policy_answer() -> None:
    response = await post_ask("Do I need manager approval to work from home?")

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["answer"] == (
        "Recurring remote work arrangements require manager approval before the arrangement begins."
    )
    assert body["citations"][0]["document_id"] == "remote-work-policy"
    assert body["citations"][0]["chunk_id"] == "remote-work-policy-manager-approval"


async def test_supported_pdf_question_returns_answer_with_citation(
    tmp_path,
) -> None:
    source_file = tmp_path / "travel-security-policy.pdf"
    write_readable_pdf(
        source_file,
        [
            "---",
            "document_id: travel-security-policy",
            "title: Travel Security Policy",
            "category: security",
            "---",
            "",
            "## Device Handling",
            "",
            "Employees must keep company laptops with them during business travel.",
        ],
    )
    index_documents(tmp_path)

    response = await post_ask(
        "How should employees handle laptops during business travel?"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["answer"] == (
        "Employees must keep company laptops with them during business travel."
    )
    assert body["refusal_reason"] is None
    assert body["citations"] == [
        {
            "document_id": "travel-security-policy",
            "chunk_id": "travel-security-policy-device-handling",
            "title": "Travel Security Policy",
            "category": "security",
            "owner": None,
            "source_date": None,
            "document_version": None,
            "snippet": (
                "Employees must keep company laptops with them during business travel."
            ),
        }
    ]


async def test_supported_runtime_pdf_question_returns_answer_with_citation() -> None:
    response = await post_ask(
        "What does the document say about security review for contracts?"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["supported"] is True
    assert body["answer"] is not None
    assert body["refusal_reason"] is None
    assert body["citations"]

    citation = body["citations"][0]
    assert citation["document_id"] == "vendor-contract-security-review"
    assert citation["chunk_id"] == (
        "vendor-contract-security-review-contract-security-review"
    )
    assert (
        "security review" in citation["snippet"]
        or "customer data" in citation["snippet"]
    )


async def test_unsupported_question_returns_refusal() -> None:
    response = await post_ask("What is the company cafeteria menu today?")

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == REFUSAL_ANSWER
    assert isinstance(body["answer"], str)
    assert body["answer"]
    assert body["supported"] is False
    assert body["citations"] == []
    assert body["refusal_reason"] == REFUSAL_REASON


@pytest.mark.parametrize(
    "question",
    [
        "Can I use a remote database?",
        "Can I expense a team party?",
        "Is 25 vacation days allowed?",
        "Do compromised vendors need review?",
    ],
)
async def test_near_miss_questions_are_refused(question: str) -> None:
    response = await post_ask(question)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == REFUSAL_ANSWER
    assert body["supported"] is False
    assert body["citations"] == []
    assert body["refusal_reason"] == REFUSAL_REASON


async def test_retrieval_is_deterministic() -> None:
    payload = {"question": "What receipts do I need for expense reimbursement?"}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        responses = [(await client.post("/ask", json=payload)).json() for _ in range(3)]

    assert responses[0] == responses[1] == responses[2]
    assert responses[0]["citations"][0]["document_id"] == "expense-reimbursement-policy"
    assert responses[0]["citations"][0]["chunk_id"] == (
        "expense-reimbursement-policy-receipts"
    )


async def test_response_shape_is_stable() -> None:
    response = await post_ask("What is the password rotation policy?")

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "answer",
        "supported",
        "citations",
        "refusal_reason",
    }
    assert set(response.json()["citations"][0].keys()) == {
        "document_id",
        "chunk_id",
        "title",
        "category",
        "owner",
        "source_date",
        "document_version",
        "snippet",
    }


async def test_blank_question_is_rejected() -> None:
    response = await post_ask("   ")

    assert response.status_code == 422


async def test_openapi_uses_api_title() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_info = response.json()["info"]
    assert openapi_info["title"] == "Enterprise Policy Copilot API"
    assert openapi_info["version"] == "0.9.0"


async def test_openapi_routes_use_explicit_tags() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi = response.json()
    assert openapi["paths"]["/ask"]["post"]["tags"] == ["Knowledge Retrieval"]
    assert openapi["paths"]["/health"]["get"]["tags"] == ["Platform"]

    route_operations = [
        operation
        for path_item in openapi["paths"].values()
        for operation in path_item.values()
    ]
    assert all(
        "default" not in operation.get("tags", []) for operation in route_operations
    )


async def test_openapi_ask_request_schema_has_realistic_example() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    ask_request_schema = response.json()["components"]["schemas"]["AskRequest"]
    assert ask_request_schema["examples"] == [
        {"question": "What should employees do if they suspect account compromise?"}
    ]
