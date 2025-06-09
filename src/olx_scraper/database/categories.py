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
