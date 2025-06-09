import functools
import threading
from typing import Callable
from gql import Client
from olx_scraper.endpoints.category_offer_listings import (
    CategoryOfferListings,
    fetch_category_offers,
)
from returns.result import Result, Success, Failure, safe
from gql.transport.requests import RequestsHTTPTransport
from psycopg2.pool import AbstractConnectionPool


def scrape_many_worker_thread(
    ids_chunk: list[int],
    graphql_endpoint: str,
    on_listings_fetched: Callable[
        [list[CategoryOfferListings.ListingSuccess.Data]], None
    ] = lambda x: None,
):
    transport = RequestsHTTPTransport(url=graphql_endpoint)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    scrape_many_categories(
        client,
        ids_chunk,
        on_listings_fetched=on_listings_fetched,
    )


def scrape_many_categories(
    client: Client,
    category_ids: list[int],
    on_listings_fetched: Callable[
        [list[CategoryOfferListings.ListingSuccess.Data]], None
    ] = lambda x: None,
) -> Result[None | CategoryOfferListings.ListingError, Exception]:
    """Scrape offers from multiple categories."""

    for category_id in category_ids:
        print(f"Scraping category {category_id}...", threading.current_thread().name)
        match scrape_category(client, category_id, on_listings_fetched):
            case Failure() as err:
                return err

    return Success(None)


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
