from pathlib import Path

from app.services.ingestion import (
    chunk_local_document,
    load_document_catalog,
    load_local_document,
)


def write_document(source_file: Path, text: str) -> None:
    source_file.write_text(text, encoding="utf-8")


def test_load_document_catalog_reads_local_markdown_and_text_documents(
    tmp_path: Path,
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
    write_document(
        tmp_path / "expense-reimbursement-policy.txt",
        """---
document_id: expense-reimbursement-policy
title: Expense Reimbursement Policy
category: finance
---

## Receipts

Employees must provide receipts for reimbursable expenses over $25.
""",
    )

    document_catalog = load_document_catalog(tmp_path)

    assert [chunk.document_id for chunk in document_catalog] == [
        "expense-reimbursement-policy",
        "remote-work-policy",
    ]
    assert document_catalog[0].title == "Expense Reimbursement Policy"
    assert document_catalog[0].category == "finance"
    assert document_catalog[0].chunk_id == "expense-reimbursement-policy-receipts"
    assert document_catalog[1].chunk_id == "remote-work-policy-manager-approval"


def test_chunk_local_document_creates_chunks_from_headings(tmp_path: Path) -> None:
    source_file = tmp_path / "it-password-policy.md"
    write_document(
        source_file,
        """---
document_id: it-password-policy
title: IT Password Policy
category: information-security
---

## Password Rotation

Employees must rotate passwords every 90 days.

## Account Compromise

Employees who suspect account compromise must immediately contact IT Security.
""",
    )

    local_document = load_local_document(source_file)
    document_chunks = chunk_local_document(local_document)

    assert [chunk.chunk_id for chunk in document_chunks] == [
        "it-password-policy-password-rotation",
        "it-password-policy-account-compromise",
    ]
    assert document_chunks[0].citation_snippet == (
        "Employees must rotate passwords every 90 days."
    )
    assert document_chunks[1].citation_snippet == (
        "Employees who suspect account compromise must immediately contact IT Security."
    )
    assert "passwords" in document_chunks[0].keywords
