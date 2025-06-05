from typing import Callable
from gql import Client
from olx_scraper.endpoints.category_offer_listings import (
    CategoryOfferListings,
    fetch_category_offers,
)
from olx_scraper.result import Err, Ok, Result


def scrape_category(
    client: Client,
    category_id: int,
    on_listings_fetched: Callable[
        [list[CategoryOfferListings.ListingSuccess.Data]], None
    ] = lambda x: None,
) -> Result[None | CategoryOfferListings.ListingError, str]:
    """Scrape offers from a specific category."""

    finish = False
    offset = 0
    limit = 50
    while not finish:
        res = fetch_category_offers(client, category_id, offset, limit)
        match res:
            case Ok(
                value=CategoryOfferListings(
                    clientCompatibleListings=CategoryOfferListings.ListingSuccess() as listings
                )
            ):
                on_listings_fetched(listings.data)
                offset += limit
                if len(listings.data) == 0:
                    finish = True
            case Ok(
                value=CategoryOfferListings(
                    clientCompatibleListings=CategoryOfferListings.ListingError() as gql_error
                )
            ):
                return Ok(gql_error)
            case _ as res:
                return Err(f"Unexpected value: {res}")

    return Ok(None)
