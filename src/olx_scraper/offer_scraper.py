import pprint
from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

from olx_scraper.endpoints.category_offer_listings import fetch_category_offers


GRAPHQL_ENDPOINT = "https://www.olx.pl/apigateway/graphql"
transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT)
client = Client(transport=transport, fetch_schema_from_transport=False)

res = fetch_category_offers(client, 443)
pprint.pprint(res)
