DO
$$
    BEGIN
        -- Enum for item condition
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'item_condition') THEN
            CREATE TYPE item_condition AS ENUM ('new', 'used', 'damaged', 'unknown');
        END IF;

        -- Enum for currency codes
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'currency_code') THEN
            CREATE TYPE currency_code AS ENUM ('PLN', 'USD', 'EUR');
        END IF;
    END
$$;


-- LOCATION TABLES
CREATE TABLE if not Exists region
(
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    normalized_name TEXT
);

CREATE TABLE if not Exists city
(
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    normalized_name TEXT,
    region_id       INTEGER REFERENCES region (id)
);

CREATE TABLE if not Exists district
(
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    normalized_name TEXT,
    city_id         INTEGER REFERENCES city (id)
);

CREATE TABLE if not Exists category
(
    id        INTEGER PRIMARY KEY,
    type      TEXT NOT NULL,                   -- e.g., 'goods', 'services', etc.
    name      TEXT,                            -- optional, if you plan to store/display a human-readable name
    parent_id INTEGER REFERENCES category (id) -- optional: support category hierarchies
);

-- LISTINGS TABLE
CREATE TABLE if not Exists listing
(
    id          BIGINT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    category_id INTEGER references category (id),
    condition   item_condition,
    price       NUMERIC,
    is_free     BOOLEAN DEFAULT FALSE,
    currency    currency_code,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    url         TEXT,
    district_id INTEGER REFERENCES district (id),
    city_id     INTEGER REFERENCES city (id),
    region_id   INTEGER REFERENCES region (id)
);

-- PHOTOS TABLE
CREATE TABLE if not Exists listing_photo
(
    id         SERIAL PRIMARY KEY,
    listing_id BIGINT REFERENCES listing (id) ON DELETE CASCADE,
    url        TEXT NOT NULL,
    width      INTEGER,
    height     INTEGER
);


