from pathlib import Path

from app.services.ingestion import (
    DEFAULT_DOCUMENTS_PATH,
    chunk_local_document,
    extract_pdf_text,
    load_document_catalog,
    load_local_document,
)
from tests.pdf_fixture import write_readable_pdf


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
owner: People Operations
source_date: 2026-01-15
document_version: 2026.1
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
    assert document_catalog[1].owner == "People Operations"
    assert document_catalog[1].source_date == "2026-01-15"
    assert document_catalog[1].document_version == "2026.1"


def test_default_it_password_policy_includes_citation_metadata() -> None:
    local_document = load_local_document(
        DEFAULT_DOCUMENTS_PATH / "it-password-policy.md"
    )
    document_chunks = chunk_local_document(local_document)

    account_compromise_chunk = next(
        chunk
        for chunk in document_chunks
        if chunk.chunk_id == "it-password-policy-account-compromise"
    )

    assert account_compromise_chunk.owner == "IT Security"
    assert account_compromise_chunk.source_date == "2026-01-15"
    assert account_compromise_chunk.document_version == "2026.1"


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


def test_extract_pdf_text_reads_embedded_text(tmp_path: Path) -> None:
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

    pdf_text = extract_pdf_text(source_file)

    assert "document_id: travel-security-policy" in pdf_text
    assert "Employees must keep company laptops" in pdf_text


def test_chunk_local_document_creates_chunks_from_pdf_text(tmp_path: Path) -> None:
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

    local_document = load_local_document(source_file)
    document_chunks = chunk_local_document(local_document)

    assert local_document.document_id == "travel-security-policy"
    assert local_document.title == "Travel Security Policy"
    assert [chunk.chunk_id for chunk in document_chunks] == [
        "travel-security-policy-device-handling"
    ]
    assert document_chunks[0].citation_snippet == (
        "Employees must keep company laptops with them during business travel."
    )
    assert "laptops" in document_chunks[0].keywords


def test_load_document_catalog_includes_pdf_documents(tmp_path: Path) -> None:
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

    document_catalog = load_document_catalog(tmp_path)

    assert [chunk.document_id for chunk in document_catalog] == [
        "travel-security-policy"
    ]
    assert document_catalog[0].chunk_id == "travel-security-policy-device-handling"
