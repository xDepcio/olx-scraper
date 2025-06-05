from contextlib import contextmanager
from typing import Any, Generator

from olx_scraper.result import Err, Ok, Result
from psycopg2.extensions import connection, cursor
from psycopg2.pool import AbstractConnectionPool


@contextmanager
def get_connection(pool: AbstractConnectionPool) -> Generator[Result[connection, str]]:
    conn: connection = pool.getconn()  # type: ignore
    if not isinstance(conn, connection):
        yield Err("Failed to get a connection from the pool")
    else:
        yield Ok(conn)
        pool.putconn(conn)  # type: ignore


@contextmanager
def get_cursor_from_connection(conn: connection) -> Generator[Result[cursor, str]]:
    try:
        cursor = conn.cursor()
        yield Ok(cursor)
        cursor.close()
    except Exception as e:
        yield Err(f"Error creating cursor: {e}")


@contextmanager
def get_cursor_from_pool(
        pool: AbstractConnectionPool,
        commit: bool = False
) -> Generator[Result[cursor, str]]:
    with get_connection(pool) as conn_result:
        match conn_result:
            case Ok(conn):
                with get_cursor_from_connection(conn) as cursor:
                    yield cursor
                if commit:
                    conn.commit()
            case Err(error):
                yield Err(f"Error getting connection: {error}")


def exec_query(
        pool: AbstractConnectionPool, query: str, params: list[Any], commit=False
) -> Result[list[Any], str]:
    with get_cursor_from_pool(pool, commit=commit) as cursor:
        match cursor:
            case Ok(c):
                try:
                    c.execute(query, params)
                    return Ok(c.fetchall())
                except Exception as e:
                    return Err(f"Error executing query: {e}")
            case Err() as err:
                return err
            case _:
                return Err(f"Unknown cursor object: {cursor}")


def load_schema(pool: AbstractConnectionPool, path: str, params: list[Any]):
    script = open(path, "r").read()
    return exec_query(pool, script, params, commit=True)
