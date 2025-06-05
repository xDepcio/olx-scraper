# category_endpoint = "https://www.olx.pl/api/v1/offers/metadata/search-categories/?offset=0&limit=40&category_id=1197&filter_refiners=spell_checker&facets=%5B%7B%22field%22%3A%22region%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A30%7D%2C%7B%22field%22%3A%22category_without_exclusions%22%2C%22fetchLabel%22%3Atrue%2C%22fetchUrl%22%3Atrue%2C%22limit%22%3A100%7D%5D"

import requests
from pydantic import BaseModel
from requests import HTTPError, get

from olx_scraper.result import Result, Ok, Err


class Category(BaseModel):
    id: int
    count: int


def fetch_and_format_olx_data() -> Result[list[Category]]:
    url = "https://www.olx.pl/api/v1/offers/metadata/search-categories/"
    params = {
        "offset": 0,
        "limit": 40,
        "category_id": 1197,
        "filter_refiners": "spell_checker",
        "facets": '[{"field":"region","fetchLabel":true,"fetchUrl":true,"limit":30},'
                  '{"field":"category_without_exclusions","fetchLabel":true,"fetchUrl":true,"limit":100}]'
    }

    response = get(url, params=params)
    try:
        response.raise_for_status()
    except HTTPError:
        return Err([])
    scraped_categories = response.json().get("data", {}).get("categories", [])
    if scraped_categories is None:
        return Err([])
    return Ok(list(map(lambda categories: Category(id=categories["id"], count=categories["count"]), scraped_categories)))
