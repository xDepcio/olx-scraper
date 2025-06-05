# category_endpoint = "https://www.olx.pl/api/v1/offers/metadata/search-categories/?offset=0&limit=40&category_id=1197&filter_refiners=spell_checker&facets=%5B%7B%22field%22%3A%22region%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A30%7D%2C%7B%22field%22%3A%22category_without_exclusions%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A100%7D%5D"

import requests
from pydantic import BaseModel
from requests import HTTPError, get
from pydantic import BaseModel
from requests import HTTPError, get
from olx_scraper.result import Result, Ok, Err
from olx_scraper.endpoints.category_offer_listings import validate_pydantic_model
from typing import Optional, Any


class Category(BaseModel):
    id: int
    type: str
    name: str
    parent: Optional[int]


def fetch_raw_category_ids() -> Result[list[int], str]:
    search_url = "https://www.olx.pl/api/v1/offers/metadata/search-categories/"

    params = {
        "offset": 0,
        "limit": 40,
        "category_id": 1197,
        "filter_refiners": "spell_checker",
        "facets": '[{"field":"region","fetchLabel":true,"fetchUrl":true,"limit":30},'
                  '{"field":"category_without_exclusions","fetchLabel":true,"fetchUrl":true,"limit":100}]'
    }

    try:
        response = get(search_url, params=params)
        response.raise_for_status()
        raw_categories = response.json().get("data", {}).get("categories", [])
        if not raw_categories:
            print("raw empty")
            return Err([])
    except HTTPError as e:
        return Err(str(e))
    return Ok(list(map(lambda x: x['id'], raw_categories)))



def fetch_olx_categories() -> Result[list[Category], str]:
    raw_categories = fetch_raw_category_ids()
    match raw_categories:
        case Err() as err:
            return Err(err.error)
        case Ok() as ok:
            return complete_categories(ok.value)
    return Err([])

def fetch_breadcrumb(category_id: int) -> Result[list[dict[str, Any]], str]:
    breadcrumbs_url = "https://www.olx.pl/api/v1/offers/metadata/breadcrumbs/"
    try:
        breadcrumb_res = get(breadcrumbs_url, params={"category_id": category_id})
        breadcrumb_res.raise_for_status()
        breadcrumbs = breadcrumb_res.json().get("data", {}).get("breadcrumbs", [])
    except HTTPError as e:
        return Err(str(e))
    return Ok(breadcrumbs)

def extract_category_name(breadcrumbs: list[dict[str, Any]]) -> str:
    if len(breadcrumbs) >= 2:
        return breadcrumbs[-1]["label"]
    return ""

def extract_category_parent_id(breadcrumbs: list[dict[str, Any]]) -> Optional[str]:
    if len(breadcrumbs) >= 3:
        return breadcrumbs[-2]["categoryId"]
    return None

def complete_categories(ids: list[int]) -> Result[list[Category], str]:
    result: list[Category] = []
    for cat_id in ids[:15]:
        breadcrumbs = fetch_breadcrumb(cat_id)
        match breadcrumbs:
            case Err() as err:
                print(f"Could not resolve breadcrumbs for category: {cat_id}")
                continue
            case Ok() as ok:
                category = Category(
                    id=cat_id,
                    type="goods",
                    name=extract_category_name(ok.value),
                    parent=extract_category_parent_id(ok.value),
                )
                result.append(category)
    return Ok(result)



