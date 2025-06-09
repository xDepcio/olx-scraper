from typing import Optional
from psycopg2.pool import AbstractConnectionPool
from returns.result import Result as Res, Success, Failure

from olx_scraper.endpoints.fetch_categories import (
    fetch_breadcrumb,
    fetch_raw_category_ids,
    insert_category,
)


def scrape_category_data(
    pool: AbstractConnectionPool, cat_id: int
) -> Res[None, Exception]:

    cat_with_parent = (
        fetch_breadcrumb(cat_id)
        .map(lambda res: res.data.breadcrumbs)
        .map(
            lambda breadcrumbs: list(
                filter(lambda x: x.categoryId is not None, breadcrumbs)
            )
        )
        .map(lambda res: zip(res, [None] + res[:-1]))
    )
    match cat_with_parent:
        case Success(data):
            for cat, parent in data:
                match insert_category(
                    pool=pool,
                    category=cat,
                    parent_id=parent.categoryId if parent else None,
                ):
                    case Failure() as err:
                        return err
                print(f"Inserted category cat: {cat}, parent: {parent}")
        case Failure() as err:
            return err

    return Success(None)


def add_categories_w_limit(
    pool: AbstractConnectionPool, limit: Optional[int] = None
) -> Res[None, Exception]:
    categories = (
        fetch_raw_category_ids()
        .map(lambda res: res.data.categories)
        .map(lambda arr: arr[:limit])
    )
    match categories:
        case Failure() as e:
            return e
        case Success(categories):
            for category in categories:
                match scrape_category_data(pool, category.id):
                    case Failure() as err:
                        return err

    return Success(None)
