## Dokumentacja Projektu: Scraper OLX.pl
Zespół w składzie:
- Aleksander Drwal
- Michał Łuszczek

### 1. Opis Projektu

Projekt "OLX Scraper" to narzędzie do automatycznego pobierania danych ofert z serwisu ogłoszeniowego OLX.pl.

Został on zaprojektowany z naciskiem na wykorzystanie paradygmatów programowania funkcyjnego w Pythonie. Scraper umożliwia pozyskiwanie informacji o kategoriach, ofertach, ich cenach, stanie przedmiotu, lokalizacjach oraz zdjęciach, a następnie zapisywanie ich do bazy danych PostgreSQL.

### 2. Struktura Projektu

Projekt jest zorganizowany w następujące moduły:

* **`cli.py`**: Główny moduł interfejsu wiersza poleceń (CLI) dla użytkownika. Definiuje komendy do uruchamiania scrapera, takie jak `auto_pilot` (do scrapowania wielu kategorii równolegle), `category` (do scrapowania pojedynczej kategorii) oraz `update_categories` (do aktualizacji danych kategorii). Wykorzystuje bibliotekę `typer` do budowy CLI.
* **`database/`**: Pakiet odpowiedzialny za interakcję z bazą danych PostgreSQL.
    * **`database.py`**: Zawiera generyczne funkcje do zarządzania połączeniami z bazą danych i wykonywania zapytań i poleceń (np. `exec_query`, `exec_many_query`). Wykorzystuje pulę połączeń (`psycopg2.pool.AbstractConnectionPool`) dla efektywnego zarządzania zasobami.
    * **`categories.py`**: Moduł do operacji CRUD na tabeli `category` w bazie danych. Zawiera funkcje do wstawiania nowych kategorii (`insert_category`), sprawdzania ich istnienia (`category_exists`) oraz pobierania wszystkich ID kategorii (`get_all_categories_ids`).
    * **`crud.py`**: Moduł odpowiedzialny za operacje CRUD na tabelach związanych z ofertami i ich lokalizacjami (`listing`, `city`, `region`, `district`, `listing_photo`). Zawiera funkcje do wstawiania ofert (`insert_offer_into_db`) oraz do ekstrakcji danych (np. ceny, stanu) z parametrów oferty.
* **`endpoints/`**: Pakiet zawierający definicje modeli Pydantic i funkcje do interakcji z API OLX.pl.
    * **`category_offer_listings.py`**: Definiuje model Pydantic dla danych ofert pobieranych z GraphQL API OLX.pl (`CategoryOfferListings`) oraz funkcje do konstruowania zapytań GraphQL i ich wykonywania (`gql_vars_get_offer_listings`, `fetch_category_offers`).
    * **`fetch_categories.py`**: Definiuje modele Pydantic dla danych kategorii i ścieżek (`AllCategoriesResponse`, `BreadCrumbsResponseEntry`) oraz funkcje do pobierania surowych danych kategorii i informacji o hierarchii kategorii z REST API OLX.pl.
* **`scrapers/`**: Pakiet zawierający logikę scrapowania danych.
    * **`scrape_categories.py`**: Zawiera funkcje do scrapowania danych kategorii i ich hierarchii (`scrape_category_data`, `add_categories_w_limit`).
    * **`scrape_by_category.py`**: Implementuje logikę scrapowania ofert w ramach pojedynczych lub wielu kategorii (`scrape_category`, `scrape_many_categories`, `scrape_many_worker_thread`).

### 3. Instrukcja Obsługi

#### Wymagania wstępne

* Python 3.13+
* Zainstalowane zależności `pdm install`
* Docker

#### Konfiguracja bazy danych

W głównym katalogu należy uruchomić bazę w kontenerze poleceniem `docker compose up`.

#### Uruchomienie programu

`python .\src\olx_scraper\cli.py [OPTIONS] COMMAND [ARGS]`

Komendy

- `auto-pilot`  - Scrapowanie ofert ze wszytskich kategorii, które są w bazie danych. Możliwość uruchomienia wielowątkowego (`--threads <count>`).
- `category` - Scrapowanie konkretnej kateogri po ID.
- `update-categories` - Scrapowanie dostępnych kategorii i ich hierarchii z OLXa.
- `[command] --help` - Wyświetlenie dostępnych opcji dla danej komendy.

### 4. Wykorzystane Paradygmaty Funkcyjne

#### Kontener `Result` (`returns.result.Result`)
Kluczowym elementem w obsłudze błędów i przepływu sterowania jest kontener Result z biblioteki returns.

Przewiduje 2 wartości sukces (Success), albo błąd (Failure), eliminując potrzebę tradycyjnych bloków try-except w wielu miejscach, pozwalając na deklaratywną obsługę błędów dzięki posiadanym pomocniczym metodom (`.bind`, `.map`), które zapewniają, że kolejne operacje są wykonywane tylko w przypadku sukcesu poprzedniej.

Przykłady użycia można znaleźć w niemal każdej funkcji, która może zakończyć się błędem (np. `exec_query`, `fetch_category_offers`, `insert_offer_into_db`).

```Python

# Przykład z database.py
def exec_query(...) -> Result[list[tuple[Any, ...]], Exception]:
    with get_cursor_from_pool(pool, commit=True) as cursor:
        match cursor:
            case Success(c):
                try:
                    c.execute(query, params)
                    return Success(c.fetchall())
                except Exception as e:
                    return Failure(e)
            case Failure() as err:
                return err
            case _:
                return Failure(Exception(f"Unknown cursor object: {cursor}"))

```
```Python

# Przykład z scrape_categories.py:16
cat_with_parent = (
    fetch_breadcrumb(cat_id)
    .map(lambda res: res.data.breadcrumbs)
    .map(
        lambda breadcrumbs: list(
            filter(lambda x: x.categoryId is not None, breadcrumbs)
        )
    )
    .map(lambda res: zip(res, [None] + res[:-1]))
)
```

#### Dekorator @safe
Dekorator `@safe` z biblioteki returns pozwala na proste przekształcenie funkcj wykorzystującej kod rzucający wyjątki w funkcję zwracającą Result, dzięki czemu nie potrzebny jest impteratywny kod try-except przekształacjący wyjątki w Result.

```python
# fetch_categories.py
@safe(exceptions=(HTTPError, ValidationError, JSONDecodeError))
def fetch_breadcrumb(category_id: int) -> BreadCrumbsResponseEntry:
    breadcrumbs_url = "https://www.olx.pl/api/v1/offers/metadata/breadcrumbs/"
    breadcrumb_res = get(breadcrumbs_url, params={"category_id": category_id})
    breadcrumb_res.raise_for_status()
    return BreadCrumbsResponseEntry.model_validate(breadcrumb_res.json())

```

#### Pattern Matching
Pythonowy match/case jest szeroko stosowany do obsługi różnych wyników operacji zwracanych przez typ Result. Zapewnia on zwięzły i czytelny sposób na reagowanie na Success lub Failure (oraz różne typy wartości wewnątrz nich).

```Python

# Przykład z scrape_by_category.py
match res:
    case Success(
        CategoryOfferListings(
            clientCompatibleListings=CategoryOfferListings.ListingSuccess() as listings
        )
    ):
        ...
    case Success(
        CategoryOfferListings(
            clientCompatibleListings=CategoryOfferListings.ListingError() as gql_error
        )
    ):
        ...
    case _:
        ...

```

#### **Funkcje Anonimowe (Lambdy)**
Proste, jednowierszowe funkcje są często definiowane jako lambdy, gdy potrzebne jest przekazanie prostej logiki jako argumentu do innej funkcji

```python
# categories.py:35
return exec_query(pool, query=query, params=[category_id]).bind(
    lambda val: Success(val[0][0])
)
```

#### Pythonowa bilbioteka standardowa np. `functools`, `map`, `filter`


**`functools.partial`**: Używany jest do tworzenia nowych funkcji z już częściowo zastosowanymi argumentami. Pozwala to na
bardziej "funkcyjne" przekazywanie funkcji zwrotnych (callbacks) z predefiniowanymi argumentami, co jest widoczne w `cli.py` przy przekazywaniu `on_listings_fetched` do wątków. Takie rozwiązanie pozwala na obsługę wielowątkowości bez mocno imperatywnego kodu ze stanem globalnym.
```Python

# Przykład z cli.py
all_categories_ids = get_all_categories_ids(db_pool).map(
    functools.partial(split_list, num_chunks=threads) # Mapowanie z częściowym zastosowaniem funkcji
)

# ...
scrape_many_worker_thread,
graphql_endpoint=GRAPHQL_ENDPOINT,
on_listings_fetched=functools.partial(
    on_listings_fetched, db_pool # Częściowe zastosowanie on_listings_fetched
)
```
```python
# utils.py
return list(map(lambda x: x.tolist(), np.array_split(data, num_chunks)))
```

Kompozycja Funkcji: Funkcje są często komponowane z mniejszych, wyspecjalizowanych funkcji, co widać w łańcuchowaniu metod .map() i .bind() na obiektach Result.
