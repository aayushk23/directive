from pathlib import Path

from psycopg import Connection

from app.commands.index_documents import index_documents
from app.services.retrieval import REFUSAL_REASON, retrieve_supported_chunk


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
