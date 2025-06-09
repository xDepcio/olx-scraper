import concurrent.futures
import functools
import pprint
import threading
import time
from typing import Annotated, Optional
import concurrent
import typer
from gql.transport.requests import RequestsHTTPTransport
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from psycopg2.pool import ThreadedConnectionPool, AbstractConnectionPool
from olx_scraper.database.categories import get_all_categories_ids
from olx_scraper.database.crud import insert_offer_into_db
from olx_scraper.endpoints.category_offer_listings import CategoryOfferListings
from olx_scraper.result import Err, Ok
from olx_scraper.scrapers import scrape_categories
from olx_scraper.scrapers.scrape_by_category import (
    scrape_category,
    scrape_many_categories,
    scrape_many_worker_thread,
)

from returns.result import Result, Success, Failure

from olx_scraper.scrapers.scrape_categories import add_categories_w_limit
from olx_scraper.utils import split_list

GRAPHQL_ENDPOINT = "https://www.olx.pl/apigateway/graphql"
app = typer.Typer()


def on_listings_fetched(
    db_pool: AbstractConnectionPool,
    listings: list[CategoryOfferListings.ListingSuccess.Data],
):
    for listing in listings:
        match insert_offer_into_db(listing, db_pool):
            case Success() as ok:
                print("success:", ok)
                print("Thread", threading.current_thread().ident)
            case Failure() as err:
                print("failure:", err)
                print("Thread", threading.current_thread().ident)


@app.command()
def auto_pilot(
    threads: Annotated[
        int,
        typer.Option("--threads", "-t", help="Number of threads to use for scraping"),
    ] = 1,
):
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        user="admin",
        password="admin",
        host="localhost",
        port="5432",
        database="olx_scraper",
    )
    all_categories_ids = get_all_categories_ids(db_pool).map(
        functools.partial(split_list, num_chunks=threads)
    )

    match all_categories_ids:
        case Success(ids_chunks):
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                results = executor.map(
                    functools.partial(
                        scrape_many_worker_thread,
                        graphql_endpoint=GRAPHQL_ENDPOINT,
                        on_listings_fetched=functools.partial(
                            on_listings_fetched, db_pool
                        ),
                    ),
                    ids_chunks,
                )

            print("Results:")
            pprint.pprint(list(results))


@app.command()
def category(id: Annotated[int, typer.Argument(help="Category ID to scrape")]):
    """Scrape a specific category by its ID."""
    transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT)
    client = Client(transport=transport, fetch_schema_from_transport=False)
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        user="admin",
        password="admin",
        host="localhost",
        port="5432",
        database="olx_scraper",
    )

    scrape_res = scrape_category(
        client, id, functools.partial(on_listings_fetched, db_pool)
    )
    print(scrape_res)


@app.command()
def update_categories(
    limit: Annotated[
        Optional[int],
        typer.Argument(help="Number of most popular categories to scrape and save"),
    ] = None,
):
    db_pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        user="admin",
        password="admin",
        host="localhost",
        port="5432",
        database="olx_scraper",
    )
    print("Limit set at:", limit)
    res = add_categories_w_limit(db_pool, limit=limit)
    pprint.pprint(res)


if __name__ == "__main__":
    app()
