import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://www.fuel-finder.service.gov.uk/api/v1"
TOKEN_URL = f"{BASE_URL}/oauth/generate_access_token"
PRICES_URL = f"{BASE_URL}/pfs/fuel-prices"
INFO_URL = f"{BASE_URL}/pfs"
TOKEN_CACHE = ".token_cache.json"

CLIENT_ID = os.getenv("FUEL_API_CLIENT_ID")
CLIENT_SECRET = os.getenv("FUEL_API_CLIENT_SECRET")


def get_token():
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE) as f:
            cached = json.load(f)
        if time.time() < cached["expires_at"] - 60:
            print("Using cached token")
            return cached["access_token"]

    print("Requesting new token...")
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "FuelWatchUK/1.0 (portfolio data pipeline)",
        },
        json={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    )

    if resp.status_code != 200:
        print(f"Token request failed: {resp.status_code}")
        print(f"Response headers: {dict(resp.headers)}")
        print(f"Response body: {resp.text[:1000]}")

    resp.raise_for_status()
    data = resp.json()["data"]

    with open(TOKEN_CACHE, "w") as f:
        json.dump({
            "access_token": data["access_token"],
            "expires_at": time.time() + data["expires_in"]
        }, f)

    print("Token acquired and cached")
    return data["access_token"]


def fetch_batches(url, token, label):
    headers = {"Authorization": f"Bearer {token}"}
    all_records = []
    batch = 1

    while True:
        resp = requests.get(url, headers=headers, params={"batch-number": batch})

        if not resp.text.strip():
            break

        data = resp.json()

        if isinstance(data, dict) and not data.get("success", True):
            print(f"{label}: no more batches at {batch}, done")
            break

        if not data:
            break

        all_records.extend(data)
        batch += 1

    print(f"{label}: {len(all_records)} records across {batch-1} batches")
    return all_records


def fetch_all(token):
    prices = fetch_batches(PRICES_URL, token, "Prices")
    info = fetch_batches(INFO_URL, token, "Info")
    return prices, info


def flatten_prices(price_records):
    flat = {}
    for record in price_records:
        node_id = record["node_id"]
        flat[node_id] = {"node_id": node_id}
        for fp in record["fuel_prices"]:
            fuel = fp["fuel_type"].lower()
            flat[node_id][f"price_{fuel}"] = fp["price"]
            flat[node_id][f"submitted_{fuel}"] = fp["price_last_updated"]
            flat[node_id][f"effective_{fuel}"] = fp["price_change_effective_timestamp"]
    return list(flat.values())


def flatten_info(info_records):
    flat = {}
    for record in info_records:
        node_id = record["node_id"]
        loc = record.get("location", {})
        flat[node_id] = {
            "node_id": node_id,
            "trading_name": record.get("trading_name"),
            "brand_name": record.get("brand_name"),
            "temporary_closure": record.get("temporary_closure"),
            "permanent_closure": record.get("permanent_closure"),
            "permanent_closure_date": record.get("permanent_closure_date"),
            "is_motorway": record.get("is_motorway_service_station", False),
            "is_supermarket": record.get("is_supermarket_service_station", False),
            "address": loc.get("address_line_1"),
            "postcode": loc.get("postcode"),
            "city": loc.get("city"),
            "county": loc.get("county"),
            "country": loc.get("country"),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
        }
    return flat


if __name__ == "__main__":
    token = get_token()
    all_prices, all_info = fetch_all(token)
    flat_prices = flatten_prices(all_prices)
    flat_info = flatten_info(all_info)
    print(f"Flattened: {len(flat_prices)} price rows, {len(flat_info)} info rows")