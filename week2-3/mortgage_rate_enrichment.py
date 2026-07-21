"""Weeks 2-3: enrich Residential MLS datasets with monthly FRED mortgage rates."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
SOLD_PATH = PROJECT_DIR / "combined_sold_202401_202606_residential.csv"
LISTINGS_PATH = PROJECT_DIR / "combined_listing_202401_202606_residential.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week2_3"
README_ASSET_DIR = SCRIPT_DIR / "assets"
FRED_MORTGAGE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"


def validate_residential_only(df: pd.DataFrame, dataset_name: str) -> None:
    property_types = set(df["PropertyType"].dropna().unique())
    if property_types != {"Residential"}:
        raise ValueError(
            f"{dataset_name} must contain only Residential rows; found: "
            f"{sorted(property_types)}"
        )


def create_monthly_mortgage_rates() -> pd.DataFrame:
    """Fetch the weekly FRED series and calculate calendar-month averages."""
    mortgage = pd.read_csv(
        FRED_MORTGAGE_URL,
        parse_dates=["observation_date"],
    ).rename(
        columns={
            "observation_date": "date",
            "MORTGAGE30US": "rate_30yr_fixed",
        }
    )

    mortgage["rate_30yr_fixed"] = pd.to_numeric(
        mortgage["rate_30yr_fixed"], errors="coerce"
    )
    mortgage = mortgage.dropna(subset=["date", "rate_30yr_fixed"])
    mortgage["year_month"] = mortgage["date"].dt.to_period("M").astype(str)

    return (
        mortgage.groupby("year_month", as_index=False)
        .agg(
            rate_30yr_fixed=("rate_30yr_fixed", "mean"),
            weekly_observation_count=("rate_30yr_fixed", "size"),
        )
        .sort_values("year_month")
    )


def save_mortgage_rate_chart(
    mortgage_monthly: pd.DataFrame,
    end_month: str,
) -> None:
    """Save a public-safe chart of monthly rates for the MLS analysis period."""
    recent = mortgage_monthly.loc[
        mortgage_monthly["year_month"].between("2024-01", end_month)
    ].copy()
    recent["date"] = pd.to_datetime(recent["year_month"] + "-01")

    fig, axis = plt.subplots(figsize=(10, 4.5))
    axis.plot(
        recent["date"],
        recent["rate_30yr_fixed"],
        color="#2f6f9f",
        linewidth=2,
        marker="o",
        markersize=3,
    )
    axis.set_title("U.S. 30-Year Fixed Mortgage Rate — Monthly Average")
    axis.set_xlabel("Month")
    axis.set_ylabel("Rate (%)")
    axis.grid(axis="y", alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(
        README_ASSET_DIR / "mortgage-rate-monthly.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


def add_mortgage_rates(
    df: pd.DataFrame,
    date_column: str,
    mortgage_monthly: pd.DataFrame,
    dataset_name: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Create a monthly join key, merge FRED rates, and validate the result."""
    enriched = df.copy()
    enriched[date_column] = pd.to_datetime(
        enriched[date_column], errors="coerce"
    )

    invalid_date_rows = int(enriched[date_column].isna().sum())
    enriched = enriched.dropna(subset=[date_column]).copy()

    enriched["year_month"] = (
        enriched[date_column].dt.to_period("M").astype(str)
    )
    enriched = enriched.merge(
        mortgage_monthly,
        on="year_month",
        how="left",
        validate="many_to_one",
    )

    missing_rates = int(enriched["rate_30yr_fixed"].isna().sum())
    if missing_rates:
        missing_months = sorted(
            enriched.loc[
                enriched["rate_30yr_fixed"].isna(), "year_month"
            ].unique()
        )
        raise ValueError(
            f"{dataset_name} has {missing_rates} rows without a mortgage rate "
            f"for month(s): {missing_months}"
        )

    quality_summary = {
        "dataset": dataset_name,
        "date_column": date_column,
        "rows_before_date_validation": len(df),
        "invalid_or_missing_date_rows_removed": invalid_date_rows,
        "rows_after_date_validation": len(enriched),
        "rows_without_mortgage_rate": missing_rates,
    }

    return enriched, quality_summary


def main() -> None:
    sold = pd.read_csv(SOLD_PATH, low_memory=False)
    listings = pd.read_csv(LISTINGS_PATH, low_memory=False)
    validate_residential_only(sold, "sold")
    validate_residential_only(listings, "listings")

    mortgage_monthly = create_monthly_mortgage_rates()
    sold_with_rates, sold_quality = add_mortgage_rates(
        sold, "CloseDate", mortgage_monthly, "sold"
    )
    listings_with_rates, listing_quality = add_mortgage_rates(
        listings, "ListingContractDate", mortgage_monthly, "listings"
    )
    merge_quality_summary = pd.DataFrame([sold_quality, listing_quality])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    README_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    sold_output_path = OUTPUT_DIR / "sold_with_mortgage_rates.csv"
    listings_output_path = OUTPUT_DIR / "listings_with_mortgage_rates.csv"
    mortgage_output_path = OUTPUT_DIR / "mortgage_rate_monthly.csv"
    quality_output_path = OUTPUT_DIR / "mortgage_merge_quality_summary.csv"

    sold_with_rates.to_csv(sold_output_path, index=False)
    listings_with_rates.to_csv(listings_output_path, index=False)
    mortgage_monthly.to_csv(mortgage_output_path, index=False)
    merge_quality_summary.to_csv(quality_output_path, index=False)
    analysis_end_month = max(
        sold_with_rates["year_month"].max(),
        listings_with_rates["year_month"].max(),
    )
    save_mortgage_rate_chart(mortgage_monthly, analysis_end_month)

    print("Mortgage-rate enrichment complete.")
    print(f"Sold rows: {len(sold_with_rates):,}")
    print(f"Listing rows: {len(listings_with_rates):,}")
    print("Missing sold mortgage rates: 0")
    print("Missing listing mortgage rates: 0")
    print(f"Saved: {sold_output_path}")
    print(f"Saved: {listings_output_path}")
    print(f"Saved: {quality_output_path}")


if __name__ == "__main__":
    main()
