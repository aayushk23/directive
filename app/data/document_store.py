from pathlib import Path

from psycopg import Connection

from app.services.embedding_provider import vector_literal
from app.services.ingestion import DocumentChunk, LocalDocument, load_local_document


def replace_document_chunks(
    connection: Connection,
    document_record: LocalDocument,
    document_chunks: tuple[DocumentChunk, ...],
    chunk_embeddings: dict[str, tuple[float, ...]] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO documents (
            document_id,
            title,
            category,
            owner,
            source_date,
            document_version,
            source_file,
            indexed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (document_id) DO UPDATE
        SET title = EXCLUDED.title,
            category = EXCLUDED.category,
            owner = EXCLUDED.owner,
            source_date = EXCLUDED.source_date,
            document_version = EXCLUDED.document_version,
            source_file = EXCLUDED.source_file,
            indexed_at = EXCLUDED.indexed_at
        """,
        (
            document_record.document_id,
            document_record.title,
            document_record.category,
            document_record.owner,
            document_record.source_date,
            document_record.document_version,
            str(document_record.source_file),
        ),
    )
    connection.execute(
        "DELETE FROM document_chunks WHERE document_id = %s",
        (document_record.document_id,),
    )

    for chunk_index, document_chunk in enumerate(document_chunks):
        connection.execute(
            """
            INSERT INTO document_chunks (
                chunk_id,
                document_id,
                chunk_index,
                chunk_text,
                answer,
                citation_snippet,
                keywords,
                chunk_embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
            """,
            (
                document_chunk.chunk_id,
                document_chunk.document_id,
                chunk_index,
                document_chunk.chunk_text,
                document_chunk.answer,
                document_chunk.citation_snippet,
                list(document_chunk.keywords),
                _chunk_embedding_literal(document_chunk, chunk_embeddings),
            ),
        )


def load_document_chunks(connection: Connection) -> tuple[DocumentChunk, ...]:
    rows = connection.execute(
        """
        SELECT
            c.chunk_id,
            d.document_id,
            d.title,
            d.category,
            d.owner,
            d.source_date,
            d.document_version,
            d.source_file,
            c.chunk_text,
            c.answer,
            c.citation_snippet,
            c.keywords
        FROM document_chunks c
        JOIN documents d ON d.document_id = c.document_id
        ORDER BY d.source_file ASC, c.chunk_index ASC
        """
    ).fetchall()

    return tuple(
        document_chunk_from_row(row)
        for row in rows
    )


def document_chunk_from_row(row: tuple) -> DocumentChunk:
    owner = row[4]
    source_date = row[5]
    document_version = row[6]

    if owner is None or source_date is None or document_version is None:
        metadata = _metadata_from_source_file(row[7])
        owner = owner or metadata.owner
        source_date = source_date or metadata.source_date
        document_version = document_version or metadata.document_version

    return DocumentChunk(
        chunk_id=row[0],
        document_id=row[1],
        title=row[2],
        category=row[3],
        owner=owner,
        source_date=source_date,
        document_version=document_version,
        chunk_text=row[8],
        answer=row[9],
        citation_snippet=row[10],
        keywords=tuple(row[11]),
    )


def _metadata_from_source_file(source_file: str) -> LocalDocument:
    try:
        return load_local_document(Path(source_file))
    except (OSError, ValueError):
        return LocalDocument(
            document_id="",
            title="",
            category="",
            owner=None,
            source_date=None,
            document_version=None,
            source_file=Path(source_file),
            text="",
        )


def _chunk_embedding_literal(
    document_chunk: DocumentChunk,
    chunk_embeddings: dict[str, tuple[float, ...]] | None,
) -> str | None:
    if chunk_embeddings is None:
        return None

    chunk_embedding = chunk_embeddings.get(document_chunk.chunk_id)
    if chunk_embedding is None or not any(chunk_embedding):
        return None

    return vector_literal(chunk_embedding)
