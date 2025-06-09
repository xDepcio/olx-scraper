# category_endpoint = "https://www.olx.pl/api/v1/offers/metadata/search-categories/?offset=0&limit=40&category_id=1197&filter_refiners=spell_checker&facets=%5B%7B%22field%22%3A%22region%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A30%7D%2C%7B%22field%22%3A%22category_without_exclusions%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A100%7D%5D"

from pydantic import BaseModel, ValidationError
from requests import HTTPError, JSONDecodeError, get
from pydantic import BaseModel
from requests import HTTPError, get

from typing import Optional
from returns.result import safe


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
