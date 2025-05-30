from typing import Annotated
import typer
from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

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

    scrape_res = scrape_category(client, id)
    print(scrape_res)


if __name__ == "__main__":
    app()
