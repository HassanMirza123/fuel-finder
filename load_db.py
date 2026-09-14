import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?sslmode=require"
)
engine = create_engine(DB_URL)

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS forecourts (
    node_id         TEXT PRIMARY KEY,
    trading_name    TEXT,
    brand_name      TEXT,
    is_motorway     BOOLEAN,
    is_supermarket  BOOLEAN,
    address         TEXT,
    postcode        TEXT,
    city            TEXT,
    county          TEXT,
    country         TEXT,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6)
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id              SERIAL PRIMARY KEY,
    node_id         TEXT REFERENCES forecourts(node_id),
    snapshot_at     TIMESTAMPTZ,
    price_e5        NUMERIC(6,1),
    submitted_e5    TIMESTAMPTZ,
    effective_e5    TIMESTAMPTZ,
    price_e10       NUMERIC(6,1),
    submitted_e10   TIMESTAMPTZ,
    effective_e10   TIMESTAMPTZ,
    price_b7s       NUMERIC(6,1),
    submitted_b7s   TIMESTAMPTZ,
    effective_b7s   TIMESTAMPTZ,
    price_b7p       NUMERIC(6,1),
    submitted_b7p   TIMESTAMPTZ,
    effective_b7p   TIMESTAMPTZ
);
"""

FORECOURT_COLS = [
    "node_id", "trading_name", "brand_name",
    "is_motorway", "is_supermarket",
    "address", "postcode", "city", "county", "country",
    "latitude", "longitude"
]

PRICE_COLS = [
    "node_id", "snapshot_at",
    "price_e5", "submitted_e5", "effective_e5",
    "price_e10", "submitted_e10", "effective_e10",
    "price_b7s", "submitted_b7s", "effective_b7s",
    "price_b7p", "submitted_b7p", "effective_b7p",
]


def init_db():
    with engine.connect() as conn:
        conn.execute(text(CREATE_TABLES_SQL))
        conn.commit()


def load(df):
    init_db()

    # Only keep columns that exist in both the df and our target list
    forecourts_df = df[[c for c in FORECOURT_COLS if c in df.columns]].drop_duplicates(subset="node_id")
    prices_df = df[[c for c in PRICE_COLS if c in df.columns]]

    # Upsert forecourts
    with engine.connect() as conn:
        for _, row in forecourts_df.iterrows():
            conn.execute(text("""
                INSERT INTO forecourts
                    (node_id, trading_name, brand_name, is_motorway, is_supermarket,
                     address, postcode, city, county, country, latitude, longitude)
                VALUES
                    (:node_id, :trading_name, :brand_name, :is_motorway, :is_supermarket,
                     :address, :postcode, :city, :county, :country, :latitude, :longitude)
                ON CONFLICT (node_id) DO NOTHING
            """), row.to_dict())
        conn.commit()
    print(f"Forecourts: {len(forecourts_df)} rows upserted")

    # Check for duplicate snapshot
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM price_snapshots
            WHERE snapshot_at = :snapshot_at
        """), {"snapshot_at": prices_df["snapshot_at"].iloc[0]})

        if result.scalar() > 0:
            print("Snapshot already loaded, skipping price insert")
        else:
            prices_df.to_sql("price_snapshots", engine, if_exists="append", index=False)
            print(f"Price snapshots: {len(prices_df)} rows inserted")


if __name__ == "__main__":
    from clean import clean_api_records
    from fetch import get_token, fetch_all, flatten_prices, flatten_info

    token = get_token()
    all_prices, all_info = fetch_all(token)

    flat_prices = flatten_prices(all_prices)
    flat_info = flatten_info(all_info)

    merged = []
    for row in flat_prices:
        node_id = row["node_id"]
        if node_id in flat_info:
            merged.append({**flat_info[node_id], **row})

    df = clean_api_records(merged)
    load(df)