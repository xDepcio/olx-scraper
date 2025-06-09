from typing import Optional
from olx_scraper.database.database import exec_query

from psycopg2.pool import AbstractConnectionPool
from returns.result import Result as Res, Success

from olx_scraper.endpoints.fetch_categories import CategoryData


def insert_category(
    pool: AbstractConnectionPool,
    category: CategoryData,
    parent_id: Optional[int] = None,
) -> Res[None, Exception]:
    query = """
        INSERT INTO category (id, type, name, parent_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            type = EXCLUDED.type,
            name = EXCLUDED.name,
            parent_id = EXCLUDED.parent_id
        RETURNING id;
    """
    return exec_query(
        pool,
        query=query,
        params=[category.categoryId, "goods", category.label, parent_id],
    ).bind(lambda x: Success(None))


def category_exists(
    pool: AbstractConnectionPool, category_id: int
) -> Res[bool, Exception]:
    query = "SELECT EXISTS(SELECT 1 FROM category WHERE id = %s);"
    return exec_query(pool, query=query, params=[category_id]).bind(
        lambda val: Success(val[0][0])
    )


def get_all_categories_ids(
    pool: AbstractConnectionPool,
) -> Res[list[int], Exception]:
    query = "SELECT id FROM category;"
    return exec_query(pool, query=query, params=[]).bind(
        lambda val: Success([row[0] for row in val])
    )
