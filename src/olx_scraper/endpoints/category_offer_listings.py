from typing import Any, Literal, Optional, Union

from olx_scraper.result import Err, Ok, Result as Res
from gql import Client, gql
from pydantic import BaseModel, Field
from returns.result import Result, Success, Failure, safe


OFFER_LISTINGS = """
query ListingSearchQuery(
  $searchParameters: [SearchParameter!] = {key: "", value: ""}
) {
  clientCompatibleListings(searchParameters: $searchParameters) {
    __typename
    ... on ListingSuccess {
      __typename
      data {
        id
        location {
          city {
            id
            name
            normalized_name
            _nodeId
          }
          district {
            id
            name
            normalized_name
            _nodeId
          }
          region {
            id
            name
            normalized_name
            _nodeId
          }
        }
        last_refresh_time
        delivery {
          rock {
            active
            mode
            offer_id
          }
        }
        created_time
        category {
          id
          type
          _nodeId
        }
        contact {
          courier
          chat
          name
          negotiation
          phone
        }
        business
        omnibus_pushup_time
        photos {
          link
          height
          rotation
          width
        }
        promotion {
          highlighted
          top_ad
          options
          premium_ad_page
          urgent
          b2c_ad_page
        }
        protect_phone
        shop {
          subdomain
        }
        title
        status
        url
        user {
          id
          uuid
          _nodeId
          about
          b2c_business_page
          banner_desktop
          banner_mobile
          company_name
          created
          is_online
          last_seen
          logo
          logo_ad_page
          name
          other_ads_enabled
          photo
          seller_type
          social_network_account_type
        }
        offer_type
        params {
          key
          name
          type
          value {
            __typename
            ... on GenericParam {
              key
              label
            }
            ... on CheckboxesParam {
              label
              checkboxParamKey: key
            }
            ... on PriceParam {
              value
              type
              previous_value
              previous_label
              negotiable
              label
              currency
              converted_value
              converted_previous_value
              converted_currency
              arranged
              budget
            }
            ... on SalaryParam {
              from
              to
              arranged
              converted_currency
              converted_from
              converted_to
              currency
              gross
              type
            }
            ... on ErrorParam {
              message
            }
          }
        }
        _nodeId
        description
        external_url
        key_params
        partner {
          code
        }
        map {
          lat
          lon
          radius
          show_detailed
          zoom
        }
        safedeal {
          allowed_quantity
          weight_grams
        }
        valid_to_time
      }
      metadata {
        filter_suggestions {
          category
          label
          name
          type
          unit
          values {
            label
            value
          }
          constraints {
            type
          }
          search_label
        }
        search_id
        total_elements
        visible_total_count
        source
        search_suggestion {
          url
          type
          changes {
            category_id
            city_id
            distance
            district_id
            query
            region_id
            strategy
            excluded_category_id
          }
        }
        facets {
          category {
            id
            count
            label
            url
          }
          category_id_1 {
            count
            id
            label
            url
          }
          category_id_2 {
            count
            id
            label
            url
          }
          category_without_exclusions {
            count
            id
            label
            url
          }
          category_id_3_without_exclusions {
            id
            count
            label
            url
          }
          city {
            count
            id
            label
            url
          }
          district {
            count
            id
            label
            url
          }
          owner_type {
            count
            id
            label
            url
          }
          region {
            id
            count
            label
            url
          }
          scope {
            id
            count
            label
            url
          }
        }
        new
        promoted
      }
      links {
        first {
          href
        }
        next {
          href
        }
        previous {
          href
        }
        self {
          href
        }
      }
    }
    ... on ListingError {
      __typename
      error {
        code
        detail
        status
        title
        validation {
          detail
          field
          title
        }
      }
    }
  }
}

"""


class CategoryOfferListings(BaseModel):

    class ListingSuccess(BaseModel):
        class Data(BaseModel):
            class Location(BaseModel):
                class District(BaseModel):
                    id: int
                    name: str
                    normalized_name: str | None

                class City(BaseModel):
                    id: int
                    name: str
                    normalized_name: str

                class Region(BaseModel):
                    id: int
                    name: str
                    normalized_name: str

                district: District | None
                city: City
                region: Region

            id: int
            location: Location

            last_refresh_time: str
            created_time: str

            class Category(BaseModel):
                id: int
                type: str

            category: Category

            class Photo(BaseModel):
                link: str
                height: int
                rotation: int
                width: int

            photos: list[Photo]
            title: str
            status: str
            url: str
            offer_type: str

            class Param(BaseModel):
                class GenericParamValue(BaseModel):
                    typename: Literal["GenericParam"] = Field(alias="__typename")
                    key: str
                    label: str

                class CheckboxesParamValue(BaseModel):
                    typename: Literal["CheckboxesParam"] = Field(alias="__typename")
                    label: str
                    checkboxParamKey: str

                class PriceParamValue(BaseModel):
                    typename: Literal["PriceParam"] = Field(alias="__typename")
                    value: float
                    type: str
                    previous_value: Optional[float] = None
                    previous_label: Optional[str] = None
                    negotiable: bool
                    label: str
                    currency: str
                    converted_value: Optional[float] = None
                    converted_previous_value: Optional[float] = None
                    converted_currency: Optional[str] = None
                    arranged: bool
                    budget: bool

                class SalaryParamValue(BaseModel):
                    typename: Literal["SalaryParam"] = Field(alias="__typename")
                    from_val: Optional[float] = Field(None, alias="from")
                    to: Optional[float] = None
                    arranged: Optional[bool] = None
                    converted_currency: Optional[str] = None
                    converted_from: Optional[float] = None
                    converted_to: Optional[float] = None
                    currency: Optional[str] = None
                    gross: Optional[bool] = None
                    type: Optional[str] = None

                class ErrorParamValue(BaseModel):
                    typename: Literal["ErrorParam"] = Field(alias="__typename")
                    message: str

                type ParamValueUnion = Union[
                    GenericParamValue,
                    CheckboxesParamValue,
                    PriceParamValue,
                    SalaryParamValue,
                    ErrorParamValue,
                ]
                key: str
                name: str
                type: str
                value: ParamValueUnion = Field(..., discriminator="typename")

            class Map(BaseModel):
                lat: float
                lon: float

            map: Map
            params: list[Param]
            description: str
            external_url: Optional[str] = None
            valid_to_time: str

        typename: Literal["ListingSuccess"] = Field(alias="__typename")
        data: list[Data]

    class ListingError(BaseModel):
        class Error(BaseModel):
            code: int
            detail: str
            status: int
            title: str

        error: Error
        typename: Literal["ListingError"] = Field(alias="__typename")

    clientCompatibleListings: Union[ListingSuccess, ListingError] = Field(
        discriminator="typename",
    )


def gql_vars_get_offer_listings(
    offset: int, limit: int, category_id: int
) -> tuple[str, dict[str, Any]]:
    return (
        OFFER_LISTINGS,
        {
            "searchParameters": [
                {"key": "category_id", "value": str(category_id)},
                {"key": "offset", "value": str(offset)},
                {"key": "limit", "value": str(limit)},
            ]
        },
    )


@safe
def execute_gql_query(
    client: Client, query: str, variables: dict[str, Any]
) -> dict[str, Any]:
    # try:
    response = client.execute(gql(query), variable_values=variables)  # type: ignore
    return response


# except Exception as e:
# return Err(str(e))


@safe
def validate_pydantic_model[T: BaseModel](model: type[T], data: dict[str, Any]) -> T:
    # try:
    return model.model_validate(data)
    #     return Success(validated_model)
    # except Exception as e:
    #     return Failure(Exception(str(e)))


def get_dict_value(path: list[str], data: dict[str, Any]) -> Res[Any, str]:
    """Get a value from a nested dictionary using a list of keys."""
    new_d = data
    for key in path:
        if not isinstance(new_d, dict):
            return Err(
                f"Expected a dictionary at key '{key}', but got {type(data).__name__}."
            )
        if (new_d := new_d.get(key)) is None:  # type: ignore
            return Err(f"Key '{key}' not found in data.")

    return Ok(new_d)  # type: ignore


def fetch_category_offers(client: Client, category_id: int, offset: int, limit: int):
    query, variables = gql_vars_get_offer_listings(offset, limit, category_id)
    return execute_gql_query(client, query, variables).bind(
        lambda x: validate_pydantic_model(CategoryOfferListings, x)
    )
    # match res:
    #     case Err() as err:
    #         return Err(err.error)
    #     case Ok() as ok:
    #         return validate_pydantic_model(CategoryOfferListings, ok.value)
