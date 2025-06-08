from typing import Annotated, Optional
import typer
from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

from psycopg2.pool import ThreadedConnectionPool
from olx_scraper.database.crud import insert_offer_into_db
from olx_scraper.endpoints.category_offer_listings import CategoryOfferListings
from olx_scraper.result import Err, Ok
from olx_scraper.scrapers.scrape_by_category import scrape_category
from olx_scraper.scrapers.scrape_categories import add_categories

GRAPHQL_ENDPOINT = "https://www.olx.pl/apigateway/graphql"
app = typer.Typer()


@app.command()
def auto_pilot():
    pass


@app.command()
def category(id: Annotated[int, typer.Argument(help="Category ID to scrape")]):
    """Scrape a specific category by its ID."""
    transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT, ssl=False)
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

    def on_listings_fetched(listings: list[CategoryOfferListings.ListingSuccess.Data]):
        for listing in listings:
            match insert_offer_into_db(listing, db_pool):
                case Ok() as ok:
                    print("ok:", ok)
                case Err() as err:
                    print("err:", err)

    scrape_res = scrape_category(client, id, on_listings_fetched)
    print(scrape_res)


@app.command()
def update_categories(
    limit: Annotated[
        Optional[int], typer.Argument(help="Number of most popular categories to scrape and save", default=None)
    ],
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
    add_categories(db_pool, limit)


if __name__ == "__main__":
    app()
