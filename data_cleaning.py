from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SOLD_PATH = PROJECT_DIR / "outputs" / "week2_3" / "sold_with_mortgage_rates.csv"
LISTINGS_PATH = PROJECT_DIR / "outputs" / "week2_3" / "listings_with_mortgage_rates.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week4_5"

SOLD_DATE_COLUMNS = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate",
]

LISTING_DATE_COLUMNS = [
    "ListingContractDate",
    "ContractStatusChangeDate",
]

SOLD_NUMERIC_COLUMNS = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "Latitude",
    "Longitude",
    "rate_30yr_fixed",
]

LISTING_NUMERIC_COLUMNS = [
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "Latitude",
    "Longitude",
    "rate_30yr_fixed",
]

REQUIRED_SOLD_COLUMNS = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate",
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "Latitude",
    "Longitude",
]

REQUIRED_LISTING_COLUMNS = [
    "ListingContractDate",
    "ContractStatusChangeDate",
    "ListPrice",
    "LivingArea",
    "DaysOnMarket",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "Latitude",
    "Longitude",
]

CA_MIN_LAT = 32.0
CA_MAX_LAT = 42.5
CA_MIN_LON = -125.0
CA_MAX_LON = -114.0


def validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Run the Week 2-3 mortgage enrichment workflow first, "
            "or update the input path at the top of this script."
        )


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise KeyError(
            f"{dataset_name} is missing required columns: {missing_columns}"
        )


def validate_residential_only(df: pd.DataFrame, dataset_name: str) -> None:
    """Stop the pipeline if an upstream step supplied non-Residential rows."""
    property_types = set(df["PropertyType"].dropna().unique())
    if property_types != {"Residential"}:
        raise ValueError(
            f"{dataset_name} must contain only Residential rows; found: "
            f"{sorted(property_types)}"
        )


def convert_date_columns(
    df: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    converted = df.copy()
    summary: list[dict[str, object]] = []

    for column in columns:
        if column not in converted.columns:
            continue

        before_missing = int(converted[column].isna().sum())
        converted[column] = pd.to_datetime(converted[column], errors="coerce")
        after_missing = int(converted[column].isna().sum())

        summary.append(
            {
                "dataset": dataset_name,
                "column": column,
                "missing_before": before_missing,
                "missing_after": after_missing,
                "new_invalid_dates": after_missing - before_missing,
            }
        )

    return converted, summary


def convert_numeric_columns(
    df: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    converted = df.copy()
    summary: list[dict[str, object]] = []

    for column in columns:
        if column not in converted.columns:
            continue

        before_missing = int(converted[column].isna().sum())
        converted[column] = pd.to_numeric(converted[column], errors="coerce")
        after_missing = int(converted[column].isna().sum())

        summary.append(
            {
                "dataset": dataset_name,
                "column": column,
                "missing_before": before_missing,
                "missing_after": after_missing,
                "new_invalid_numeric_values": after_missing - before_missing,
            }
        )

    return converted, summary


def add_numeric_flags(
    sold: pd.DataFrame,
    listings: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sold = sold.copy()
    listings = listings.copy()

    # Missing core values are retained for traceability, but explicitly flagged
    # so later metric calculations can exclude values that are not computable.
    sold["missing_close_price_flag"] = sold["ClosePrice"].isna()
    sold["missing_living_area_flag"] = sold["LivingArea"].isna()
    sold["invalid_close_price_flag"] = sold["ClosePrice"].le(0)
    sold["invalid_living_area_flag"] = sold["LivingArea"].le(0)
    sold["negative_days_on_market_flag"] = sold["DaysOnMarket"].lt(0)
    sold["negative_bedrooms_flag"] = sold["BedroomsTotal"].lt(0)
    sold["negative_bathrooms_flag"] = sold["BathroomsTotalInteger"].lt(0)

    listings["missing_list_price_flag"] = listings["ListPrice"].isna()
    listings["missing_living_area_flag"] = listings["LivingArea"].isna()
    listings["invalid_list_price_flag"] = listings["ListPrice"].le(0)
    listings["invalid_living_area_flag"] = listings["LivingArea"].le(0)
    listings["negative_days_on_market_flag"] = listings["DaysOnMarket"].lt(0)
    listings["negative_bedrooms_flag"] = listings["BedroomsTotal"].lt(0)
    listings["negative_bathrooms_flag"] = listings["BathroomsTotalInteger"].lt(0)

    summary_rows = []

    for dataset_name, df, flags in [
        (
            "sold",
            sold,
            [
                "missing_close_price_flag",
                "missing_living_area_flag",
                "invalid_close_price_flag",
                "invalid_living_area_flag",
                "negative_days_on_market_flag",
                "negative_bedrooms_flag",
                "negative_bathrooms_flag",
            ],
        ),
        (
            "listings",
            listings,
            [
                "missing_list_price_flag",
                "missing_living_area_flag",
                "invalid_list_price_flag",
                "invalid_living_area_flag",
                "negative_days_on_market_flag",
                "negative_bedrooms_flag",
                "negative_bathrooms_flag",
            ],
        ),
    ]:
        for flag in flags:
            summary_rows.append(
                {
                    "dataset": dataset_name,
                    "flag": flag,
                    "flagged_rows": int(df[flag].sum()),
                }
            )

    return sold, listings, pd.DataFrame(summary_rows)


def add_date_consistency_flags(
    sold: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sold = sold.copy()

    sold["listing_after_close_flag"] = (
        sold["ListingContractDate"].notna()
        & sold["CloseDate"].notna()
        & (sold["ListingContractDate"] > sold["CloseDate"])
    )

    sold["purchase_after_close_flag"] = (
        sold["PurchaseContractDate"].notna()
        & sold["CloseDate"].notna()
        & (sold["PurchaseContractDate"] > sold["CloseDate"])
    )

    sold["negative_timeline_flag"] = (
        sold["ListingContractDate"].notna()
        & sold["PurchaseContractDate"].notna()
        & (sold["ListingContractDate"] > sold["PurchaseContractDate"])
    )

    summary = pd.DataFrame(
        [
            {
                "flag": "listing_after_close_flag",
                "count": int(sold["listing_after_close_flag"].sum()),
            },
            {
                "flag": "purchase_after_close_flag",
                "count": int(sold["purchase_after_close_flag"].sum()),
            },
            {
                "flag": "negative_timeline_flag",
                "count": int(sold["negative_timeline_flag"].sum()),
            },
        ]
    )

    return sold, summary


def add_geographic_flags(df: pd.DataFrame) -> pd.DataFrame:
    flagged = df.copy()

    flagged["missing_coordinate_flag"] = (
        flagged["Latitude"].isna() | flagged["Longitude"].isna()
    )
    flagged["zero_coordinate_flag"] = (
        flagged["Latitude"].eq(0) | flagged["Longitude"].eq(0)
    )
    flagged["positive_longitude_flag"] = (
        flagged["Longitude"].notna() & flagged["Longitude"].gt(0)
    )
    flagged["invalid_latitude_range_flag"] = (
        flagged["Latitude"].notna()
        & (flagged["Latitude"].lt(-90) | flagged["Latitude"].gt(90))
    )
    flagged["invalid_longitude_range_flag"] = (
        flagged["Longitude"].notna()
        & (flagged["Longitude"].lt(-180) | flagged["Longitude"].gt(180))
    )
    flagged["out_of_california_flag"] = (
        flagged["Latitude"].notna()
        & flagged["Longitude"].notna()
        & (
            flagged["Latitude"].lt(CA_MIN_LAT)
            | flagged["Latitude"].gt(CA_MAX_LAT)
            | flagged["Longitude"].lt(CA_MIN_LON)
            | flagged["Longitude"].gt(CA_MAX_LON)
        )
    )

    return flagged


def geographic_summary(
    sold: pd.DataFrame,
    listings: pd.DataFrame,
) -> pd.DataFrame:
    flags = [
        "missing_coordinate_flag",
        "zero_coordinate_flag",
        "positive_longitude_flag",
        "invalid_latitude_range_flag",
        "invalid_longitude_range_flag",
        "out_of_california_flag",
    ]

    rows = []

    for dataset_name, df in [("sold", sold), ("listings", listings)]:
        for flag in flags:
            rows.append(
                {
                    "dataset": dataset_name,
                    "flag": flag,
                    "flagged_rows": int(df[flag].sum()),
                }
            )

    return pd.DataFrame(rows)


def create_clean_datasets(
    sold: pd.DataFrame,
    listings: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sold_remove_flag = (
        sold["invalid_close_price_flag"]
        | sold["invalid_living_area_flag"]
        | sold["negative_days_on_market_flag"]
        | sold["negative_bedrooms_flag"]
        | sold["negative_bathrooms_flag"]
        | sold["listing_after_close_flag"]
        | sold["purchase_after_close_flag"]
        | sold["negative_timeline_flag"]
        | sold["zero_coordinate_flag"]
        | sold["positive_longitude_flag"]
        | sold["invalid_latitude_range_flag"]
        | sold["invalid_longitude_range_flag"]
        | sold["out_of_california_flag"]
    )

    listings_remove_flag = (
        listings["invalid_list_price_flag"]
        | listings["invalid_living_area_flag"]
        | listings["negative_days_on_market_flag"]
        | listings["negative_bedrooms_flag"]
        | listings["negative_bathrooms_flag"]
        | listings["zero_coordinate_flag"]
        | listings["positive_longitude_flag"]
        | listings["invalid_latitude_range_flag"]
        | listings["invalid_longitude_range_flag"]
        | listings["out_of_california_flag"]
    )

    sold_clean = sold.loc[~sold_remove_flag].copy()
    listings_clean = listings.loc[~listings_remove_flag].copy()

    summary = pd.DataFrame(
        [
            {
                "dataset": "sold",
                "rows_before": len(sold),
                "rows_removed": int(sold_remove_flag.sum()),
                "rows_after": len(sold_clean),
                "percent_removed": round(sold_remove_flag.mean() * 100, 4),
            },
            {
                "dataset": "listings",
                "rows_before": len(listings),
                "rows_removed": int(listings_remove_flag.sum()),
                "rows_after": len(listings_clean),
                "percent_removed": round(listings_remove_flag.mean() * 100, 4),
            },
        ]
    )

    return sold_clean, listings_clean, summary


def validate_clean_datasets(
    sold_clean: pd.DataFrame,
    listings_clean: pd.DataFrame,
) -> None:
    sold_invalid_count = int(
        (
            sold_clean["ClosePrice"].le(0)
            | sold_clean["LivingArea"].le(0)
            | sold_clean["DaysOnMarket"].lt(0)
            | sold_clean["negative_bedrooms_flag"]
            | sold_clean["negative_bathrooms_flag"]
            | sold_clean["listing_after_close_flag"]
            | sold_clean["purchase_after_close_flag"]
            | sold_clean["negative_timeline_flag"]
            | sold_clean["zero_coordinate_flag"]
            | sold_clean["positive_longitude_flag"]
            | sold_clean["invalid_latitude_range_flag"]
            | sold_clean["invalid_longitude_range_flag"]
            | sold_clean["out_of_california_flag"]
        ).sum()
    )

    listings_invalid_count = int(
        (
            listings_clean["ListPrice"].le(0)
            | listings_clean["LivingArea"].le(0)
            | listings_clean["DaysOnMarket"].lt(0)
            | listings_clean["negative_bedrooms_flag"]
            | listings_clean["negative_bathrooms_flag"]
            | listings_clean["zero_coordinate_flag"]
            | listings_clean["positive_longitude_flag"]
            | listings_clean["invalid_latitude_range_flag"]
            | listings_clean["invalid_longitude_range_flag"]
            | listings_clean["out_of_california_flag"]
        ).sum()
    )

    if sold_invalid_count or listings_invalid_count:
        raise ValueError(
            "Post-cleaning validation failed. "
            f"Sold invalid rows: {sold_invalid_count}; "
            f"Listings invalid rows: {listings_invalid_count}."
        )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    validate_input_file(SOLD_PATH)
    validate_input_file(LISTINGS_PATH)

    print("Loading Week 2-3 enriched datasets...")
    sold = pd.read_csv(SOLD_PATH, low_memory=False)
    listings = pd.read_csv(LISTINGS_PATH, low_memory=False)

    validate_required_columns(sold, REQUIRED_SOLD_COLUMNS, "sold")
    validate_required_columns(listings, REQUIRED_LISTING_COLUMNS, "listings")
    validate_residential_only(sold, "sold")
    validate_residential_only(listings, "listings")

    print("Converting date columns...")
    sold, sold_date_summary = convert_date_columns(
        sold, SOLD_DATE_COLUMNS, "sold"
    )
    listings, listing_date_summary = convert_date_columns(
        listings, LISTING_DATE_COLUMNS, "listings"
    )
    date_conversion_summary = pd.DataFrame(
        sold_date_summary + listing_date_summary
    )

    print("Converting numeric columns...")
    sold, sold_numeric_summary = convert_numeric_columns(
        sold, SOLD_NUMERIC_COLUMNS, "sold"
    )
    listings, listing_numeric_summary = convert_numeric_columns(
        listings, LISTING_NUMERIC_COLUMNS, "listings"
    )
    numeric_conversion_summary = pd.DataFrame(
        sold_numeric_summary + listing_numeric_summary
    )

    print("Creating numeric validation flags...")
    sold, listings, numeric_flag_summary = add_numeric_flags(sold, listings)

    print("Creating date consistency flags...")
    sold, date_flag_summary = add_date_consistency_flags(sold)

    print("Creating geographic quality flags...")
    sold = add_geographic_flags(sold)
    listings = add_geographic_flags(listings)
    geo_flag_summary = geographic_summary(sold, listings)

    print("Creating cleaned analysis-ready datasets...")
    sold_clean, listings_clean, cleaning_summary = create_clean_datasets(
        sold, listings
    )
    validate_clean_datasets(sold_clean, listings_clean)

    print("Saving cleaned datasets and quality summaries...")
    sold_clean.to_csv(OUTPUT_DIR / "sold_clean.csv", index=False)
    listings_clean.to_csv(OUTPUT_DIR / "listings_clean.csv", index=False)
    cleaning_summary.to_csv(OUTPUT_DIR / "cleaning_summary.csv", index=False)
    date_conversion_summary.to_csv(
        OUTPUT_DIR / "date_conversion_summary.csv", index=False
    )
    numeric_conversion_summary.to_csv(
        OUTPUT_DIR / "numeric_conversion_summary.csv", index=False
    )
    numeric_flag_summary.to_csv(
        OUTPUT_DIR / "numeric_invalid_flag_summary.csv", index=False
    )
    date_flag_summary.to_csv(
        OUTPUT_DIR / "date_consistency_summary.csv", index=False
    )
    geo_flag_summary.to_csv(
        OUTPUT_DIR / "geographic_data_quality_summary.csv", index=False
    )

    print("\nWeek 4-5 data cleaning complete.")
    print(cleaning_summary.to_string(index=False))
    print(f"\nOutputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
