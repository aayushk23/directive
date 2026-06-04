from app.data.document_store import document_chunk_from_row
from app.services.ingestion import DEFAULT_DOCUMENTS_PATH


def test_document_chunk_from_row_restores_missing_source_metadata() -> None:
    row = (
        "it-password-policy-password-rotation",
        "it-password-policy",
        "IT Password Policy",
        "information-security",
        None,
        None,
        None,
        str(DEFAULT_DOCUMENTS_PATH / "it-password-policy.md"),
        "Employees must rotate passwords every 90 days.",
        "Employees must rotate passwords every 90 days.",
        "Employees must rotate passwords every 90 days.",
        ["passwords", "rotation"],
    )

    document_chunk = document_chunk_from_row(row)

    assert document_chunk.owner == "IT Security"
    assert document_chunk.source_date == "2026-01-15"
    assert document_chunk.document_version == "2026.1"
