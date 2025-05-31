from typing import Annotated
import typer
from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

from psycopg2.pool import ThreadedConnectionPool
from olx_scraper.database.database import exec_query, load_schema
from olx_scraper.scrapers.scrape_by_category import scrape_category

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
    res = exec_query(db_pool, "SELECT 1", [])
    print(res)
    load_schema(db_pool, "./database/schema.sql", [])
    res = exec_query(db_pool, "select * from listing;", [])
    print(res)
    return
    scrape_res = scrape_category(client, id)
    print(scrape_res)


if __name__ == "__main__":
    app()
