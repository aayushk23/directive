from psycopg import Connection

from app.data.database import connect


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    document_id text PRIMARY KEY,
    title text NOT NULL,
    category text NOT NULL,
    source_file text NOT NULL,
    indexed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    chunk_text text NOT NULL,
    answer text NOT NULL,
    citation_snippet text NOT NULL,
    keywords text[] NOT NULL,
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
    ON document_chunks (document_id);

CREATE INDEX IF NOT EXISTS document_chunks_order_idx
    ON document_chunks (document_id, chunk_index);
"""


def create_schema(connection: Connection) -> None:
    connection.execute(SCHEMA_SQL)
    connection.commit()


def main() -> None:
    with connect() as connection:
        create_schema(connection)
    print("database schema is ready")


if __name__ == "__main__":
    main()
