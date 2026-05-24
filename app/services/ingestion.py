import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DOCUMENTS_PATH = Path(__file__).resolve().parents[2] / "documents"
SUPPORTED_DOCUMENT_EXTENSIONS = {".md", ".txt"}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "before",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "must",
    "of",
    "or",
    "over",
    "the",
    "to",
    "who",
}


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    title: str
    category: str
    answer: str
    citation_snippet: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class LocalDocument:
    document_id: str
    title: str
    category: str
    source_file: Path
    text: str


def load_document_catalog(
    documents_path: Path = DEFAULT_DOCUMENTS_PATH,
) -> tuple[DocumentChunk, ...]:
    document_chunks: list[DocumentChunk] = []

    for source_file in _local_document_files(documents_path):
        local_document = load_local_document(source_file)
        document_chunks.extend(chunk_local_document(local_document))

    return tuple(document_chunks)


def load_local_document(source_file: Path) -> LocalDocument:
    metadata, text = _parse_metadata(source_file)
    return LocalDocument(
        document_id=metadata["document_id"],
        title=metadata["title"],
        category=metadata["category"],
        source_file=source_file,
        text=text,
    )


def chunk_local_document(local_document: LocalDocument) -> tuple[DocumentChunk, ...]:
    sections = _split_sections(local_document.text, local_document.source_file)
    document_chunks = []

    for heading, body in sections:
        citation_snippet = _first_paragraph(body)
        chunk_id = f"{local_document.document_id}-{_slugify(heading)}"
        keywords = _keywords_for_chunk(local_document.title, heading, body)
        document_chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=local_document.document_id,
                title=local_document.title,
                category=local_document.category,
                answer=citation_snippet,
                citation_snippet=citation_snippet,
                keywords=keywords,
            )
        )

    return tuple(document_chunks)


def _local_document_files(documents_path: Path) -> tuple[Path, ...]:
    if not documents_path.exists():
        raise ValueError(f"documents directory does not exist: {documents_path}")

    return tuple(
        sorted(
            source_file
            for source_file in documents_path.iterdir()
            if source_file.is_file()
            and source_file.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
        )
    )


def _parse_metadata(source_file: Path) -> tuple[dict[str, str], str]:
    content = source_file.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"document metadata is missing: {source_file}")

    parts = content.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError(f"document metadata is malformed: {source_file}")

    metadata = _metadata_from_lines(parts[1], source_file)
    return metadata, parts[2].strip()


def _metadata_from_lines(metadata_text: str, source_file: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}

    for line in metadata_text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"document metadata line is malformed: {source_file}")
        metadata[key.strip()] = value.strip()

    required_fields = ("document_id", "title", "category")
    missing_fields = [field for field in required_fields if not metadata.get(field)]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"document metadata is missing {missing}: {source_file}")

    return metadata


def _split_sections(text: str, source_file: Path) -> tuple[tuple[str, str], ...]:
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
            continue

        current_lines.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    if not sections:
        raise ValueError(f"document has no chunk headings: {source_file}")

    empty_sections = [heading for heading, body in sections if not body]
    if empty_sections:
        headings = ", ".join(empty_sections)
        raise ValueError(f"document chunks are empty for {headings}: {source_file}")

    return tuple(sections)


def _first_paragraph(text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text)]
    return next(paragraph for paragraph in paragraphs if paragraph)


def _keywords_for_chunk(title: str, heading: str, body: str) -> tuple[str, ...]:
    keyword_text = f"{title} {heading} {body}"
    keywords: list[str] = []

    for term in re.findall(r"\$?\b[a-zA-Z0-9]+\b", keyword_text.lower()):
        if term not in STOP_WORDS and term not in keywords:
            keywords.append(term)

    return tuple(keywords)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-+", "-", slug)
