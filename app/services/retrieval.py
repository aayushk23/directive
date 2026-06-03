import math
import re
from dataclasses import dataclass

from psycopg import Connection

from app.data.document_store import load_document_chunks
from app.services.embedding_provider import (
    EmbeddingProvider,
    LocalHashEmbeddingProvider,
    vector_literal,
)
from app.services.ingestion import DocumentChunk


REFUSAL_ANSWER = "I cannot answer this question from the current document set."
REFUSAL_REASON = "Unsupported by available documents."
MINIMUM_SUPPORT_SCORE = 2
MINIMUM_VECTOR_SIMILARITY = 0.50


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk | None

    @property
    def supported(self) -> bool:
        return self.chunk is not None


def retrieve_supported_chunk(
    question: str,
    connection: Connection,
    embedding_provider: EmbeddingProvider | None = None,
) -> RetrievalResult:
    provider = embedding_provider or LocalHashEmbeddingProvider()
    vector_result = _retrieve_vector_supported_chunk(question, connection, provider)
    if vector_result.supported:
        return vector_result

    return _retrieve_keyword_supported_chunk(question, connection)


def _retrieve_keyword_supported_chunk(
    question: str,
    connection: Connection,
) -> RetrievalResult:
    normalized_question = _normalize(question)
    document_chunks = load_document_chunks(connection)
    if not document_chunks:
        return RetrievalResult(chunk=None)

    scored_chunks = (
        (_score_chunk(normalized_question, chunk), index, chunk)
        for index, chunk in enumerate(document_chunks)
    )

    best_score, _index, best_chunk = max(
        scored_chunks,
        key=lambda item: (item[0], -item[1]),
    )

    if best_score < MINIMUM_SUPPORT_SCORE:
        return RetrievalResult(chunk=None)

    return RetrievalResult(chunk=best_chunk)


def _retrieve_vector_supported_chunk(
    question: str,
    connection: Connection,
    embedding_provider: EmbeddingProvider,
) -> RetrievalResult:
    query_embedding = embedding_provider.embed_text(question)
    if not any(query_embedding):
        return RetrievalResult(chunk=None)

    row = connection.execute(
        """
        SELECT
            c.chunk_id,
            d.document_id,
            d.title,
            d.category,
            d.owner,
            d.source_date,
            d.document_version,
            c.chunk_text,
            c.answer,
            c.citation_snippet,
            c.keywords,
            1 - (c.chunk_embedding <=> %s::vector) AS vector_similarity
        FROM document_chunks c
        JOIN documents d ON d.document_id = c.document_id
        WHERE c.chunk_embedding IS NOT NULL
        ORDER BY c.chunk_embedding <=> %s::vector ASC,
            d.source_file ASC,
            c.chunk_index ASC
        LIMIT 1
        """,
        (
            vector_literal(query_embedding),
            vector_literal(query_embedding),
        ),
    ).fetchone()

    if row is None or not math.isfinite(row[11]) or row[11] < MINIMUM_VECTOR_SIMILARITY:
        return RetrievalResult(chunk=None)

    return RetrievalResult(
        chunk=DocumentChunk(
            chunk_id=row[0],
            document_id=row[1],
            title=row[2],
            category=row[3],
            owner=row[4],
            source_date=row[5],
            document_version=row[6],
            chunk_text=row[7],
            answer=row[8],
            citation_snippet=row[9],
            keywords=tuple(row[10]),
        )
    )


def _score_chunk(normalized_question: str, chunk: DocumentChunk) -> int:
    score = 0
    for keyword in chunk.keywords:
        normalized_keyword = _normalize(keyword)
        if " " in normalized_keyword:
            if normalized_keyword in normalized_question:
                score += 2
        elif re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized_question):
            score += 1
    return score


def _normalize(value: str) -> str:
    lowered = value.lower()
    without_punctuation = re.sub(r"[^a-z0-9$]+", " ", lowered)
    return re.sub(r"\s+", " ", without_punctuation).strip()
