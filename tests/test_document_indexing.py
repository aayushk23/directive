from pathlib import Path

from psycopg import Connection

from app.commands.index_documents import index_documents


def write_document(source_file: Path, text: str) -> None:
    source_file.write_text(text, encoding="utf-8")


def test_index_documents_stores_local_files_as_chunks(
    tmp_path: Path,
    postgres_connection: Connection,
) -> None:
    write_document(
        tmp_path / "remote-work-policy.md",
        """---
document_id: remote-work-policy
title: Remote Work Policy
category: workplace
---

## Manager Approval

Recurring remote work arrangements require manager approval.
""",
    )
    document_count, chunk_count = index_documents(tmp_path)

    stored_document = postgres_connection.execute(
        """
        SELECT document_id, title, category, source_file
        FROM documents
        """
    ).fetchone()
    stored_chunk = postgres_connection.execute(
        """
        SELECT chunk_id, chunk_text, citation_snippet, keywords
        FROM document_chunks
        """
    ).fetchone()

    assert document_count == 1
    assert chunk_count == 1
    assert stored_document[0] == "remote-work-policy"
    assert stored_document[1] == "Remote Work Policy"
    assert stored_document[2] == "workplace"
    assert stored_document[3].endswith("remote-work-policy.md")
    assert stored_chunk[0] == "remote-work-policy-manager-approval"
    assert (
        stored_chunk[1]
        == "Recurring remote work arrangements require manager approval."
    )
    assert (
        stored_chunk[2]
        == "Recurring remote work arrangements require manager approval."
    )
    assert "remote" in stored_chunk[3]
