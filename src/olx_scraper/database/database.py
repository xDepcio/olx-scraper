from contextlib import contextmanager
from typing import Any, Generator

from olx_scraper.result import Err, Ok, Result
from psycopg2.extensions import connection, cursor
from psycopg2.pool import AbstractConnectionPool


@contextmanager
def get_connection(
    pool: AbstractConnectionPool,
) -> Generator[Result[connection, Exception]]:
    conn: connection = pool.getconn()  # type: ignore
    if not isinstance(conn, connection):
        yield Err(Exception("Failed to get a connection from the pool"))
    else:
        yield Ok(conn)
        pool.putconn(conn)  # type: ignore


@contextmanager
def get_cursor_from_connection(
    conn: connection,
) -> Generator[Result[cursor, Exception]]:
    try:
        cursor = conn.cursor()
        yield Ok(cursor)
        cursor.close()
    except Exception as e:
        yield Err(e)


@contextmanager
def get_cursor_from_pool(
    pool: AbstractConnectionPool, commit: bool = False
) -> Generator[Result[cursor, Exception]]:
    with get_connection(pool) as conn_result:
        match conn_result:
            case Ok(conn):
                with get_cursor_from_connection(conn) as cursor:
                    yield cursor
                if commit:
                    conn.commit()
            case Err() as err:
                yield err


def exec_query(
    pool: AbstractConnectionPool, query: str, params: list[Any]
) -> Result[list[tuple[Any, ...]], Exception]:
    with get_cursor_from_pool(pool, commit=True) as cursor:
        match cursor:
            case Ok(c):
                try:
                    c.execute(query, params)
                    return Ok(c.fetchall())
                except Exception as e:
                    return Err(e)
            case Err() as err:
                return err
            case _:
                return Err(f"Unknown cursor object: {cursor}")


def exec_many_query(
    pool: AbstractConnectionPool, query: str, params: list[list[Any]]
) -> Result[None, Exception]:
    with get_cursor_from_pool(pool, commit=True) as cursor:
        match cursor:
            case Ok(c):
                try:
                    c.executemany(query, params)
                    return Ok(None)
                except Exception as e:
                    return Err(e)
            case Err() as err:
                return err
            case _:
                return Err(f"Unknown cursor object: {cursor}")


def load_schema(pool, path, params):
    script = open(path, "r").read()
    return exec_query(pool, script, params, commit=True)
