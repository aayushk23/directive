import re
from dataclasses import dataclass

from psycopg import Connection

from app.data.document_store import load_document_chunks
from app.services.ingestion import DocumentChunk


REFUSAL_ANSWER = "I cannot answer this question from the current document set."
REFUSAL_REASON = "Unsupported by available documents."
MINIMUM_SUPPORT_SCORE = 2


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk | None

    @property
    def supported(self) -> bool:
        return self.chunk is not None


def retrieve_supported_chunk(question: str, connection: Connection) -> RetrievalResult:
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
