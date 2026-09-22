import pandas as pd


def load_and_clean(filepath):
    df = pd.read_csv(filepath)

    # Slim to the columns we care about
    cols_to_keep = [
        "forecourts.node_id",
        "forecourts.trading_name",
        "forecourts.brand_name",
        "forecourts.is_motorway_service_station",
        "forecourts.is_supermarket_service_station",
        "forecourts.location.postcode",
        "forecourts.location.address_line_1",
        "forecourts.location.city",
        "forecourts.location.county",
        "forecourts.location.country",
        "forecourts.location.latitude",
        "forecourts.location.longitude",
        "forecourts.fuel_price.E5",
        "forecourts.price_submission_timestamp.E5",
        "forecourts.price_change_effective_timestamp.E5",
        "forecourts.fuel_price.E10",
        "forecourts.price_submission_timestamp.E10",
        "forecourts.price_change_effective_timestamp.E10",
        "forecourts.fuel_price.B7S",
        "forecourts.price_submission_timestamp.B7S",
        "forecourts.price_change_effective_timestamp.B7S",
        "forecourts.fuel_price.B7P",
        "forecourts.price_submission_timestamp.B7P",
        "forecourts.price_change_effective_timestamp.B7P",
    ]
    df = df[cols_to_keep].copy()

    # Rename to clean short names for the database
    df.columns = [
        "node_id", "trading_name", "brand_name",
        "is_motorway", "is_supermarket",
        "postcode", "address", "city", "county", "country",
        "latitude", "longitude",
        "price_e5", "submitted_e5", "effective_e5",
        "price_e10", "submitted_e10", "effective_e10",
        "price_b7s", "submitted_b7s", "effective_b7s",
        "price_b7p", "submitted_b7p", "effective_b7p",
    ]

    # Normalise country
    country_map = {
        "ENGLAND": "England", "E": "England",
        "SCOTLAND": "Scotland", "S": "Scotland",
        "WALES": "Wales", "W": "Wales",
        "NORTHERN IRELAND": "Northern Ireland", "N": "Northern Ireland",
        "UNITED KINGDOM": "England", "UK": "England",
    }
    df["country"] = df["country"].str.strip().replace(country_map)

    # Normalise brand and trading name
    df["brand_name"] = df["brand_name"].str.strip().str.title()
    df["trading_name"] = df["trading_name"].str.strip().str.title()

    # Parse timestamps — the raw format is "Mon Jun 15 2026 18:14:58 GMT+0000 (Coordinated Universal Time)"
    # Strip the verbose GMT suffix first, then parse with an explicit format
    ts_cols = [
        "submitted_e5", "effective_e5",
        "submitted_e10", "effective_e10",
        "submitted_b7s", "effective_b7s",
        "submitted_b7p", "effective_b7p",
    ]
    for col in ts_cols:
        cleaned = df[col].str.replace(
            r"\s*GMT\+\d{4}\s*\(.*?\)", "", regex=True
        ).str.strip()
        df[col] = pd.to_datetime(
            cleaned, format="%a %b %d %Y %H:%M:%S", utc=True, errors="coerce"
        )

    # Derive snapshot timestamp from the latest price submission in the file
    # This means the same CSV loaded twice will produce the same snapshot_at
    # and the duplicate check in load_db.py will correctly skip it
    snapshot_time = None
    for col in ["submitted_e5", "submitted_e10", "submitted_b7s", "submitted_b7p"]:
        val = df[col].max()
        if pd.notna(val):
            snapshot_time = val
            break

    if snapshot_time is None:
        raise ValueError(
            "Could not determine snapshot timestamp — no valid timestamps in data"
        )

    df["snapshot_at"] = snapshot_time

    # Drop rows with no prices at all — they carry no useful information
    price_cols = ["price_e5", "price_e10", "price_b7s", "price_b7p"]
    df = df.dropna(subset=price_cols, how="all")

    return df

def clean_api_records(merged_records):
    import pandas as pd

    df = pd.DataFrame(merged_records)

    # Rename API fuel type column names to match database columns
    df = df.rename(columns={
        "price_b7_standard": "price_b7s",
        "submitted_b7_standard": "submitted_b7s",
        "effective_b7_standard": "effective_b7s",
        "price_b7_premium": "price_b7p",
        "submitted_b7_premium": "submitted_b7p",
        "effective_b7_premium": "effective_b7p",
    })

    # Normalise country
    country_map = {
        "ENGLAND": "England", "E": "England",
        "SCOTLAND": "Scotland", "S": "Scotland",
        "WALES": "Wales", "W": "Wales",
        "NORTHERN IRELAND": "Northern Ireland", "N": "Northern Ireland",
        "UNITED KINGDOM": "England", "UK": "England",
    }
    df["country"] = df["country"].str.strip().replace(country_map)

    # Normalise brand and trading name
    df["brand_name"] = df["brand_name"].str.strip().str.title()
    df["trading_name"] = df["trading_name"].str.strip().str.title()

    # Replace empty strings with None
    df = df.replace({"": None})

    # Parse permanent closure date
    if "permanent_closure_date" in df.columns:
        parsed_dates = pd.to_datetime(
            df["permanent_closure_date"], errors="coerce"
        )

        df["permanent_closure_date"] = parsed_dates.apply(
            lambda value: value.date() if pd.notna(value) else None
        )

    # Parse timestamps — API gives clean ISO 8601 so no regex needed
    ts_cols = [
        "submitted_e5", "effective_e5",
        "submitted_e10", "effective_e10",
        "submitted_b7s", "effective_b7s",
        "submitted_b7p", "effective_b7p",
    ]
    for col in ts_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    # Derive snapshot timestamp from latest price submission
    snapshot_time = None
    for col in ["submitted_e5", "submitted_e10", "submitted_b7s", "submitted_b7p"]:
        if col in df.columns:
            val = df[col].max()
            if pd.notna(val):
                snapshot_time = val
                break

    if snapshot_time is None:
        raise ValueError("Could not determine snapshot timestamp")

    df["snapshot_at"] = snapshot_time

    # Drop rows with no prices at all
    price_cols = [c for c in ["price_e5", "price_e10", "price_b7s", "price_b7p"] if c in df.columns]
    df = df.dropna(subset=price_cols, how="all")

    return df


if __name__ == "__main__":
    df = load_and_clean("UpdatedFuelPrice-1781600400051.csv")
    print("Clean shape:", df.shape)
    print()
    print("Timestamp dtype:", df["submitted_e5"].dtype)
    print("Sample timestamps:")
    print(df["submitted_e5"].dropna().head(5))
    print()
    print("Snapshot time:", df["snapshot_at"].iloc[0])
    print()
    print("Country value counts:")
    print(df["country"].value_counts())
    print()
    print(df[["trading_name", "brand_name", "country", "price_e5", "price_b7s"]].head(5))