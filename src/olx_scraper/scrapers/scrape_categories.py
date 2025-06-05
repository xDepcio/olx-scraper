from psycopg2.pool import AbstractConnectionPool

from olx_scraper.database.database import exec_query
from olx_scraper.endpoints.fetch_categories import Category, fetch_olx_categories
from olx_scraper.result import Result, Err, Ok


def make_insert_query_from_category(c: Category) -> Result[str, str]:
    query = (
        f"INSERT INTO category (id, type, name, parent_id) VALUES ({c.id}, '{c.type}', '{c.name}', {c.parent if c.parent is not None else "NULL"})"
        f" ON CONFLICT (id) DO UPDATE SET type = '{c.type}', name = '{c.name}', parent_id = {c.parent if c.parent is not None else "NULL"};")
    return Ok(query)


def exec_multiple_queries(pool: AbstractConnectionPool, queries: list[Result[str, str]]) -> Result[None, str]:
    for query in queries:
        match query:
            case Err() as err:
                return Err(err.error)
            case Ok():
                exec_query(pool, query.value, [], True)
    return Ok(None)


def add_categories(pool: AbstractConnectionPool, limit: int = 100) -> Result[None, str]:
    categories: Result = fetch_olx_categories(limit)
    match categories:
        case Err() as err:
            return err
        case Ok() as ok:
            queries = list(map(make_insert_query_from_category, ok.value))
            exec_multiple_queries(pool, queries)
    return Ok(None)
