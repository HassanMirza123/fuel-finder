import pandas as pd

df = pd.read_csv("UpdatedFuelPrice-1781600400051.csv")

print("Shape: ", df.shape)
print()
print("Column names: ")
for col in df.columns:
    print(col)

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

df = df[cols_to_keep]

print("Slimmed shape:", df.shape)
print()
print(df.head(3))