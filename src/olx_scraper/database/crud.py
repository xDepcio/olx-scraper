from olx_scraper.database.categories import category_exists
from olx_scraper.database.database import exec_many_query, exec_query
from olx_scraper.endpoints.category_offer_listings import CategoryOfferListings
from psycopg2.pool import AbstractConnectionPool
from olx_scraper.result import Err, Ok, Result as Res
from returns.result import Result, Success, Failure, safe
from olx_scraper.scrapers.scrape_categories import scrape_category_data


def pull_price_from_params(
    params: list[CategoryOfferListings.ListingSuccess.Data.Param],
) -> Result[tuple[float, str], Exception]:
    for param in params:
        match param.value:
            case CategoryOfferListings.ListingSuccess.Data.Param.PriceParamValue() as v:
                return Success((v.value, v.currency))
            case _:
                pass

    return Failure(Exception("couldn't pull price from params:", params))


def pull_condition_from_params(
    params: list[CategoryOfferListings.ListingSuccess.Data.Param],
) -> Result[str, Exception]:
    for param in params:
        match param.value:
            case (
                CategoryOfferListings.ListingSuccess.Data.Param.GenericParamValue() as v
            ):
                if param.key == "state":
                    return Success(v.key)
            case _:
                pass

    return Failure(Exception("couldn't pull condition from params:", params))


class DistrictEmptyErr(Exception):
    pass


def insert_offer_into_db(
    offer: CategoryOfferListings.ListingSuccess.Data, pool: AbstractConnectionPool
) -> Result[int, Exception]:

    match insert_region(offer.location, pool):
        case Failure() as e:
            return e
        case Success(region_id):
            pass

    match insert_city_into_db(offer.location, pool):
        case Failure() as e:
            return e
        case Success(city_id):
            pass

    match insert_district(offer.location, pool):
        case Failure(DistrictEmptyErr()):
            district_id = None
        case Failure() as e:
            return e
        case Success(district_id):
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

    match pull_price_from_params(offer.params):
        case Success((price, currency)):
            pass
        case Failure() as e:
            return e

    match pull_condition_from_params(offer.params):
        case Success(condition):
            pass
        case Failure() as e:
            condition = "unknown"
            # return e

    match category_exists(pool, offer.category.id):
        case Success(False):
            match scrape_category_data(pool, offer.category.id):
                case Failure() as e:
                    return e
        case Failure() as e:
            return e

    return exec_query(
        pool,
        query=sql,
        params=[
            offer.id,
            offer.title,
            offer.description,
            offer.category.id,
            condition,
            price,
            False,  # is_free is not provided in the data
            currency,
            offer.map.lat,
            offer.map.lon,
            offer.url,
            district_id,
            city_id,
            region_id,
        ],
    ).bind(lambda val: insert_photos(offer, pool).bind(lambda _: Success(val[0][0])))


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
    return exec_query(
        pool,
        query=sql,
        params=[
            location.city.id,
            location.city.name,
            location.city.normalized_name,
            location.region.id,
        ],
    ).bind(lambda val: Success(val[0][0]))


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
    return exec_query(
        pool,
        query=sql,
        params=[
            location.region.id,
            location.region.name,
            location.region.normalized_name,
        ],
    ).bind(lambda val: Success(val[0][0]))


def insert_district(
    location: CategoryOfferListings.ListingSuccess.Data.Location,
    pool: AbstractConnectionPool,
) -> Result[int, Exception]:
    if not location.district:
        return Failure(DistrictEmptyErr())

    sql = """
        INSERT INTO district (id, name, normalized_name, city_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            normalized_name = EXCLUDED.normalized_name,
            city_id = EXCLUDED.city_id
        RETURNING id;
    """
    return exec_query(
        pool,
        query=sql,
        params=[
            location.district.id,
            location.district.name,
            location.district.normalized_name,
            location.city.id,
        ],
    ).bind(lambda val: Success(val[0][0]))


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
