from typing import Callable
from gql import Client
from olx_scraper.endpoints.category_offer_listings import (
    CategoryOfferListings,
    fetch_category_offers,
)
from returns.result import Result, Success, Failure, safe


def scrape_category(
    client: Client,
    category_id: int,
    on_listings_fetched: Callable[
        [list[CategoryOfferListings.ListingSuccess.Data]], None
    ] = lambda x: None,
) -> Result[None | CategoryOfferListings.ListingError, Exception]:
    """Scrape offers from a specific category."""

    finish = False
    offset = 0
    limit = 50
    while not finish:
        res = fetch_category_offers(client, category_id, offset, limit)
        match res:
            case Success(
                CategoryOfferListings(
                    clientCompatibleListings=CategoryOfferListings.ListingSuccess() as listings
                )
            ):
                on_listings_fetched(listings.data)
                offset += limit
                if len(listings.data) == 0:
                    finish = True
            case Success(
                CategoryOfferListings(
                    clientCompatibleListings=CategoryOfferListings.ListingError() as gql_error
                )
            ):
                return Success(gql_error)
            case _:
                return Failure(Exception(f"Unexpected value: {res}"))

    return Success(None)
