from olx_scraper.database.database import exec_many_query, exec_query
from olx_scraper.endpoints.category_offer_listings import CategoryOfferListings
from psycopg2.pool import AbstractConnectionPool

from olx_scraper.result import Err, Ok, Result


class DistrictEmptyErr(Exception):
    pass


def insert_offer_into_db(
    offer: CategoryOfferListings.ListingSuccess.Data, pool: AbstractConnectionPool
) -> Result[int, Exception]:

    match insert_region(offer.location, pool):
        case Err() as e:
            return e
        case Ok(region_id):
            pass

    match insert_city_into_db(offer.location, pool):
        case Err() as e:
            return e
        case Ok(city_id):
            pass

    match insert_district(offer.location, pool):
        case Err(DistrictEmptyErr()):
            district_id = None
        case Err() as e:
            return e
        case Ok(district_id):
            pass

    sql = """
        INSERT INTO listing (
            id, title, description, category_id, condition, price, is_free,
            currency, lat, lon, url, district_id, city_id, region_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET -- Or DO NOTHING if listings are immutable once created
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            category_id = EXCLUDED.category_id,
            condition = EXCLUDED.condition,
            price = EXCLUDED.price,
            is_free = EXCLUDED.is_free,
            currency = EXCLUDED.currency,
            lat = EXCLUDED.lat,
            lon = EXCLUDED.lon,
            url = EXCLUDED.url,
            district_id = EXCLUDED.district_id,
            city_id = EXCLUDED.city_id,
            region_id = EXCLUDED.region_id
        RETURNING id;
    """

    match exec_query(
        pool,
        sql,
        params=[
            offer.id,
            offer.title,
            offer.description,
            # offer.category.id,
            None,
            "unknown",
            123,
            False,
            "PLN",
            offer.map.lat,
            offer.map.lon,
            offer.url,
            district_id,
            city_id,
            region_id,
        ],
    ):
        case Ok(val):
            match insert_photos(offer, pool):
                case Err() as e:
                    return e
                case _:
                    pass
            return Ok(val[0][0])

        case Err() as e:
            return e


def insert_city_into_db(
    location: CategoryOfferListings.ListingSuccess.Data.Location,
    pool: AbstractConnectionPool,
) -> Result[int, Exception]:
    sql = """
        INSERT INTO city (id, name, normalized_name, region_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            normalized_name = EXCLUDED.normalized_name,
            region_id = EXCLUDED.region_id
        RETURNING id;
    """
    match exec_query(
        pool,
        query=sql,
        params=[
            location.city.id,
            location.city.name,
            location.city.normalized_name,
            location.region.id,
        ],
    ):
        case Ok(val):
            return Ok(val[0][0])
        case Err() as e:
            return e


def insert_region(
    location: CategoryOfferListings.ListingSuccess.Data.Location,
    pool: AbstractConnectionPool,
) -> Result[int, Exception]:
    sql = """
        INSERT INTO region (id, name, normalized_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            normalized_name = EXCLUDED.normalized_name
        RETURNING id;
    """
    match exec_query(
        pool,
        query=sql,
        params=[
            location.region.id,
            location.region.name,
            location.region.normalized_name,
        ],
    ):
        case Ok(val):
            return Ok(val[0][0])
        case Err() as e:
            return e


def insert_district(
    location: CategoryOfferListings.ListingSuccess.Data.Location,
    pool: AbstractConnectionPool,
) -> Result[int, Exception]:
    if not location.district:
        return Err(DistrictEmptyErr())

    sql = """
        INSERT INTO district (id, name, normalized_name, city_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            normalized_name = EXCLUDED.normalized_name,
            city_id = EXCLUDED.city_id
        RETURNING id;
    """
    match exec_query(
        pool,
        query=sql,
        params=[
            location.district.id,
            location.district.name,
            location.district.normalized_name,
            location.city.id,
        ],
    ):
        case Ok(val):
            return Ok(val[0][0])
        case Err() as e:
            return Err(Exception(e.error))


def insert_photos(
    listing: CategoryOfferListings.ListingSuccess.Data,
    pool: AbstractConnectionPool,
) -> Result[None, Exception]:
    sql = """
        INSERT INTO listing_photo (listing_id, url, width, height)
        VALUES (%s, %s, %s, %s);
    """

    return exec_many_query(
        pool,
        query=sql,
        params=[
            [listing.id, photo.link, photo.width, photo.height]
            for photo in listing.photos
        ],
    )
