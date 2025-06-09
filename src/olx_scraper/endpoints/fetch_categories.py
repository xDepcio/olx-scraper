# category_endpoint = "https://www.olx.pl/api/v1/offers/metadata/search-categories/?offset=0&limit=40&category_id=1197&filter_refiners=spell_checker&facets=%5B%7B%22field%22%3A%22region%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A30%7D%2C%7B%22field%22%3A%22category_without_exclusions%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A100%7D%5D"

import itertools
import pprint
import sys
from pydantic import BaseModel, ValidationError
from requests import HTTPError, JSONDecodeError, get
from pydantic import BaseModel
from requests import HTTPError, get
from olx_scraper.database.database import exec_query

from olx_scraper.result import Result, Ok, Err
from olx_scraper.endpoints.category_offer_listings import get_dict_value
from typing import Optional, Any
from psycopg2.pool import AbstractConnectionPool
from returns.result import Result as Res, Success, Failure, safe
from returns.pointfree import bind
from returns.pipeline import flow


class AllCategoriesResponse(BaseModel):
    class Data(BaseModel):
        class Category(BaseModel):
            id: int
            count: int

        total_count: int
        categories: list[Category]

    data: Data


class BreadCrumbsResponseEntry(BaseModel):
    class Data(BaseModel):
        class Breadcrumb(BaseModel):
            href: str
            label: str
            categoryId: Optional[int] = None

        breadcrumbs: list[Breadcrumb]

    data: Data


type CategoryData = BreadCrumbsResponseEntry.Data.Breadcrumb


@safe(exceptions=(HTTPError, ValidationError, JSONDecodeError))
def fetch_raw_category_ids() -> AllCategoriesResponse:
    search_url = "https://www.olx.pl/api/v1/offers/metadata/search-categories/"

    params = {
        "offset": 0,
        "limit": 40,
        "category_id": 1197,
        "filter_refiners": "spell_checker",
        "facets": '[{"field":"region","fetchLabel":true,"fetchUrl":true,"limit":30},'
        '{"field":"category_without_exclusions","fetchLabel":true,"fetchUrl":true,"limit":100}]',
    }

    response = get(search_url, params=params)
    response.raise_for_status()
    return AllCategoriesResponse.model_validate(response.json())


@safe(exceptions=(HTTPError, ValidationError, JSONDecodeError))
def fetch_breadcrumb(category_id: int) -> BreadCrumbsResponseEntry:
    breadcrumbs_url = "https://www.olx.pl/api/v1/offers/metadata/breadcrumbs/"
    breadcrumb_res = get(breadcrumbs_url, params={"category_id": category_id})
    breadcrumb_res.raise_for_status()
    return BreadCrumbsResponseEntry.model_validate(breadcrumb_res.json())


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
