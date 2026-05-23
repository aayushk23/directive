import re
from dataclasses import dataclass

from app.data.document_catalog import DOCUMENT_CATALOG, Document


REFUSAL_ANSWER = "I cannot answer this question from the current document set."
REFUSAL_REASON = "Unsupported by available documents."
MINIMUM_SUPPORT_SCORE = 2


@dataclass(frozen=True)
class RetrievalResult:
    document: Document | None

    @property
    def supported(self) -> bool:
        return self.document is not None


def retrieve_supported_document(question: str) -> RetrievalResult:
    normalized_question = _normalize(question)
    scored_documents = (
        (_score_document(normalized_question, document), index, document)
        for index, document in enumerate(DOCUMENT_CATALOG)
    )

    best_score, _index, best_document = max(
        scored_documents,
        key=lambda item: (item[0], -item[1]),
    )

    if best_score < MINIMUM_SUPPORT_SCORE:
        return RetrievalResult(document=None)

    return RetrievalResult(document=best_document)


def _score_document(normalized_question: str, document: Document) -> int:
    score = 0
    for keyword in document.keywords:
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
