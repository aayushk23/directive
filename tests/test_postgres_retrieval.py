from pathlib import Path

from psycopg import Connection

from app.commands.index_documents import index_documents
from app.services.embedding_provider import EMBEDDING_DIMENSIONS
from app.services.retrieval import REFUSAL_REASON, retrieve_supported_chunk


class TestEmbeddingProvider:
    def embed_text(self, text: str) -> tuple[float, ...]:
        if text == "Which applies?":
            return _unit_vector(0)
        if "company laptops" in text:
            return _unit_vector(0)
        if "approved hotels" in text:
            return _unit_vector(1)
        return _unit_vector(2)


def test_retrieve_supported_answer_from_stored_chunks(
    tmp_path: Path,
    postgres_connection: Connection,
) -> None:
    _write_remote_work_policy(tmp_path)
    index_documents(tmp_path)

    result = retrieve_supported_chunk(
        "Do I need manager approval to work from home?",
        postgres_connection,
    )

    assert result.supported is True
    assert result.chunk is not None
    assert result.chunk.document_id == "remote-work-policy"
    assert result.chunk.title == "Remote Work Policy"
    assert result.chunk.chunk_id == "remote-work-policy-manager-approval"
    assert result.chunk.citation_snippet == (
        "Recurring remote work arrangements require manager approval before the arrangement begins."
    )


def test_semantic_retrieval_returns_expected_stored_chunk(
    tmp_path: Path,
    postgres_connection: Connection,
) -> None:
    (tmp_path / "travel-security-policy.md").write_text(
        """---
document_id: travel-security-policy
title: Travel Security Policy
category: security
---

## Device Handling

Employees must keep company laptops with them during business travel.

## Hotel Check-In

Employees may check into approved hotels after 3 p.m.
""",
        encoding="utf-8",
    )
    embedding_provider = TestEmbeddingProvider()
    index_documents(tmp_path, embedding_provider=embedding_provider)

    result = retrieve_supported_chunk(
        "Which applies?",
        postgres_connection,
        embedding_provider=embedding_provider,
    )

    assert result.supported is True
    assert result.chunk is not None
    assert result.chunk.chunk_id == "travel-security-policy-device-handling"


def test_unsupported_question_returns_no_stored_chunk(
    tmp_path: Path,
    postgres_connection: Connection,
) -> None:
    _write_remote_work_policy(tmp_path)
    index_documents(tmp_path)

    result = retrieve_supported_chunk(
        "What is the cafeteria menu today?",
        postgres_connection,
    )

    assert result.supported is False
    assert result.chunk is None
    assert REFUSAL_REASON == "Unsupported by available documents."


def _write_remote_work_policy(documents_path: Path) -> None:
    (documents_path / "remote-work-policy.md").write_text(
        """---
document_id: remote-work-policy
title: Remote Work Policy
category: workplace
---

## Manager Approval

Recurring remote work arrangements require manager approval before the arrangement begins.
""",
        encoding="utf-8",
    )


def _unit_vector(index: int) -> tuple[float, ...]:
    return tuple(
        1.0 if dimension == index else 0.0 for dimension in range(EMBEDDING_DIMENSIONS)
    )
