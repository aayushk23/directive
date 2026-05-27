import hashlib
import math
import re
from typing import Protocol


EMBEDDING_DIMENSIONS = 64
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "before",
    "by",
    "do",
    "for",
    "from",
    "how",
    "if",
    "in",
    "is",
    "must",
    "of",
    "or",
    "over",
    "should",
    "the",
    "to",
    "what",
    "when",
    "who",
    "with",
}


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> tuple[float, ...]:
        pass


class LocalHashEmbeddingProvider:
    dimensions = EMBEDDING_DIMENSIONS

    def embed_text(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimensions

        for token in _tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0.0:
            return tuple(vector)

        return tuple(value / magnitude for value in vector)


def embedding_input_for_chunk(
    title: str, chunk_text: str, keywords: tuple[str, ...]
) -> str:
    return " ".join((title, chunk_text, " ".join(keywords)))


def vector_literal(vector: tuple[float, ...]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _tokens(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw_token in re.findall(r"\$?\b[a-zA-Z0-9]+\b", text.lower()):
        token = _normalize_token(raw_token)
        if token and token not in STOP_WORDS:
            tokens.append(token)

    return tuple(tokens)


def _normalize_token(token: str) -> str:
    if token.startswith("$"):
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token
