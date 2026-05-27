from psycopg import Connection

from app.services.embedding_provider import vector_literal
from app.services.ingestion import DocumentChunk, LocalDocument


def replace_document_chunks(
    connection: Connection,
    document_record: LocalDocument,
    document_chunks: tuple[DocumentChunk, ...],
    chunk_embeddings: dict[str, tuple[float, ...]] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO documents (document_id, title, category, source_file, indexed_at)
        VALUES (%s, %s, %s, %s, now())
        ON CONFLICT (document_id) DO UPDATE
        SET title = EXCLUDED.title,
            category = EXCLUDED.category,
            source_file = EXCLUDED.source_file,
            indexed_at = EXCLUDED.indexed_at
        """,
        (
            document_record.document_id,
            document_record.title,
            document_record.category,
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
        DocumentChunk(
            chunk_id=row[0],
            document_id=row[1],
            title=row[2],
            category=row[3],
            chunk_text=row[4],
            answer=row[5],
            citation_snippet=row[6],
            keywords=tuple(row[7]),
        )
        for row in rows
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
