from dataclasses import dataclass
from typing import Union


@dataclass
class Ok[T]:
    value: T


@dataclass
class Err[E]:
    error: E


type Result[T, E] = Union[Ok[T], Err[E]]


def fetch_category_offers(category: str, page: int = 1) -> Result[int, str]:
    """
    Fetch offers from a specific category and page.

    Args:
        category (str): The category to fetch offers from.
        page (int): The page number to fetch offers from.

    Returns:
        Result[list[dict], str]: A list of offers or an error message.
    """
    # Placeholder for actual implementation
    return Ok(42)


d = fetch_category_offers("electronics", 1)
match d:
    case Err() as err:
        pass
    case Ok() as res:
        okres = res.value
