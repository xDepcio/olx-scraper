from typing import Optional

from psycopg2.pool import AbstractConnectionPool

from olx_scraper.database.database import exec_query
from olx_scraper.endpoints.fetch_categories import Category, fetch_olx_categories, fetch_raw_category_ids, \
    complete_category
from olx_scraper.result import Result, Err, Ok


def make_insert_query_from_category(c: Category) -> str:
    query = (
        f"INSERT INTO category (id, type, name, parent_id) VALUES ({c.id}, '{c.type}', '{c.name}', {c.parent if c.parent is not None else "NULL"})"
        f" ON CONFLICT (id) DO UPDATE SET type = '{c.type}', name = '{c.name}', parent_id = {c.parent if c.parent is not None else "NULL"};"
    )
    return query


def make_select_query_from_category_id(cat_id) -> str:
    query = (
        f"SELECT * FROM category where id = {cat_id})"
    )
    return query


def exec_multiple_queries(
        pool: AbstractConnectionPool, queries: list[Result[str, str]]
) -> Result[None, str]:
    for query in queries:
        match query:
            case Err() as err:
                return Err(err.error)
            case Ok():
                exec_query(pool, query.value, [])
    return Ok(None)


def check_if_exists(pool: AbstractConnectionPool, cat_id: int) -> Result[bool, str]:
        select_query = make_select_query_from_category_id(cat_id)
        res = exec_query(pool, select_query, [])
        match res:
            case Ok() as ok:
                if len(ok.value) > 0:
                    return Ok(False)
                return Ok(True)
            case _ as e:
                return e


def add_from_id(pool: AbstractConnectionPool, cat_id: int) -> Result[None, str]:
    if check_if_exists(pool, cat_id):
        return Ok(None)

    complete = complete_category(cat_id)
    match complete:
        case Ok():
            insert_query = make_insert_query_from_category(complete.value)
            result = exec_query(pool, insert_query, [])
        case Err() as e:
            return Err(e.error)
        case _ as e:
            return Err(str(e))
    match result:
        case Ok():
            return Ok(None)
        case Err() as e:
            return e
        case _ as e:
            return Err(str(e))


def add_categories(pool: AbstractConnectionPool, limit: Optional[int] = None) -> Result[None, str]:
    categories: Result[list[int], str] = fetch_raw_category_ids()
    match categories:
        case Err() as err:
            return err
        case Ok() as ok:
            covered = 0
            for cat_id in ok.value:
                add_from_id(pool, cat_id)
                if limit is not None and covered > limit:
                    break

    return Ok(None)
