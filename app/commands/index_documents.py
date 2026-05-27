import argparse
from pathlib import Path

from app.data.database import connect
from app.data.document_store import replace_document_chunks
from app.data.schema import create_schema
from app.services.ingestion import DEFAULT_DOCUMENTS_PATH, chunk_local_document
from app.services.ingestion import local_document_files
from app.services.ingestion import load_local_document
from app.services.embedding_provider import (
    EmbeddingProvider,
    LocalHashEmbeddingProvider,
    embedding_input_for_chunk,
)


def index_documents(
    documents_path: Path = DEFAULT_DOCUMENTS_PATH,
    database_url: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> tuple[int, int]:
    provider = embedding_provider or LocalHashEmbeddingProvider()

    with connect(database_url) as connection:
        create_schema(connection)
        document_count = 0
        chunk_count = 0

        for source_file in local_document_files(documents_path):
            document_record = load_local_document(source_file)
            document_chunks = chunk_local_document(document_record)
            chunk_embeddings = {
                document_chunk.chunk_id: provider.embed_text(
                    embedding_input_for_chunk(
                        document_chunk.title,
                        document_chunk.chunk_text,
                        document_chunk.keywords,
                    )
                )
                for document_chunk in document_chunks
            }
            replace_document_chunks(
                connection,
                document_record,
                document_chunks,
                chunk_embeddings,
            )
            document_count += 1
            chunk_count += len(document_chunks)

        connection.commit()

    return document_count, chunk_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Index local documents into Postgres.")
    parser.add_argument(
        "--documents-path",
        type=Path,
        default=DEFAULT_DOCUMENTS_PATH,
        help="Directory containing local .md, .txt, and .pdf documents.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Postgres connection URL. Defaults to DATABASE_URL.",
    )
    args = parser.parse_args()

    document_count, chunk_count = index_documents(
        documents_path=args.documents_path,
        database_url=args.database_url,
    )
    print(f"indexed {document_count} documents and {chunk_count} chunks")


if __name__ == "__main__":
    main()
