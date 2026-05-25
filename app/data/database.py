import os
from collections.abc import Generator

import psycopg
from psycopg import Connection


DATABASE_URL_ENV_VAR = "DATABASE_URL"


def database_url() -> str:
    value = os.environ.get(DATABASE_URL_ENV_VAR)
    if not value:
        raise RuntimeError(f"{DATABASE_URL_ENV_VAR} is required")
    return value


def connect(database_url_value: str | None = None) -> Connection:
    return psycopg.connect(database_url_value or database_url())


def db_session() -> Generator[Connection, None, None]:
    with connect() as connection:
        yield connection
