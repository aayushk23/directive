from psycopg import Connection

from app.data.schema import create_schema


def test_create_schema_creates_document_tables(
    postgres_connection: Connection,
) -> None:
    create_schema(postgres_connection)

    postgres_connection.execute(
        """
        INSERT INTO documents (document_id, title, category, source_file)
        VALUES (%s, %s, %s, %s)
        """,
        ("travel-security-policy", "Travel Security Policy", "security", "travel.pdf"),
    )
    postgres_connection.execute(
        """
        INSERT INTO document_chunks (
            chunk_id,
            document_id,
            chunk_index,
            chunk_text,
            answer,
            citation_snippet,
            keywords
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            "travel-security-policy-device-handling",
            "travel-security-policy",
            0,
            "Employees must keep company laptops with them.",
            "Employees must keep company laptops with them.",
            "Employees must keep company laptops with them.",
            ["employees", "laptops"],
        ),
    )
    postgres_connection.commit()

    document_count = postgres_connection.execute(
        "SELECT count(*) FROM documents"
    ).fetchone()[0]
    chunk_count = postgres_connection.execute(
        "SELECT count(*) FROM document_chunks"
    ).fetchone()[0]

    assert document_count == 1
    assert chunk_count == 1
