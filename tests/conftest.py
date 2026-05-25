import os
from collections.abc import Generator
from urllib.parse import urlparse

import psycopg
import pytest
from psycopg import Connection

from app.data.database import db_session
from app.data.schema import create_schema
from app.main import app


@pytest.fixture
def postgres_connection() -> Generator[Connection, None, None]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for Postgres-backed tests")
    database_name = urlparse(database_url).path.rsplit("/", maxsplit=1)[-1]
    if "test" not in database_name:
        pytest.skip("DATABASE_URL must point to a test database")

    with psycopg.connect(database_url) as connection:
        create_schema(connection)
        _truncate_database(connection)
        yield connection
        _truncate_database(connection)


@pytest.fixture
def app_db_session(
    postgres_connection: Connection,
) -> Generator[Connection, None, None]:
    def override_db_session() -> Generator[Connection, None, None]:
        yield postgres_connection

    app.dependency_overrides[db_session] = override_db_session
    yield postgres_connection
    app.dependency_overrides.clear()


def _truncate_database(connection: Connection) -> None:
    connection.execute(
        "TRUNCATE TABLE document_chunks, documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
