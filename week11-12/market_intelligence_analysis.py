"""Create aggregate Irvine market metrics for the Weeks 11-12 deliverables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
MARKET_CSV = PROJECT_DIR / "outputs" / "week8" / "tableau_market_events.csv"
COMPETITIVE_CSV = (
    PROJECT_DIR / "outputs" / "week8" / "tableau_competitive_sales.csv"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "irvine_market_metrics.json"
CITY = "Irvine"
COUNTY = "Orange"
LATEST_COMPLETE_MONTH = "2026-04"
YEAR_AGO_MONTH = "2025-04"
CURRENT_PERIOD_START = "2025-05"
CURRENT_PERIOD_END = "2026-04"
PRIOR_PERIOD_START = "2024-05"
PRIOR_PERIOD_END = "2025-04"


def percent_change(current: float, prior: float) -> float | None:
    if pd.isna(current) or pd.isna(prior) or prior == 0:
        return None
    return (float(current) / float(prior) - 1.0) * 100.0


def clean_name(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace({"": pd.NA})


def load_market_data(path: Path) -> pd.DataFrame:
    columns = [
        "EventType",
        "YrMo",
        "City",
        "CountyOrParish",
        "ClosePrice",
        "DaysOnMarket",
        "CloseToOriginalListRatio",
        "PricePerSqFt",
        "NewListings",
        "ClosedSales",
    ]
    frame = pd.read_csv(path, usecols=columns, low_memory=False)
    frame["City"] = clean_name(frame["City"])
    frame["CountyOrParish"] = clean_name(frame["CountyOrParish"])
    return frame[
        frame["City"].eq(CITY) & frame["CountyOrParish"].eq(COUNTY)
    ].copy()


def monthly_market_summary(frame: pd.DataFrame) -> pd.DataFrame:
    sold = frame[frame["EventType"].eq("Closed Sale")]
    sold_monthly = sold.groupby("YrMo", observed=True).agg(
        median_close_price=("ClosePrice", "median"),
        average_days_on_market=("DaysOnMarket", "mean"),
        median_price_per_sq_ft=("PricePerSqFt", "median"),
        average_close_to_original_list_ratio=(
            "CloseToOriginalListRatio",
            "mean",
        ),
        closed_sales=("ClosedSales", "sum"),
        sales_volume=("ClosePrice", "sum"),
    )
    listing_monthly = (
        frame[frame["EventType"].eq("New Listing")]
        .groupby("YrMo", observed=True)
        .agg(new_listings=("NewListings", "sum"))
    )
    return sold_monthly.join(listing_monthly, how="outer").sort_index()


def period_summary(frame: pd.DataFrame, start: str, end: str) -> dict[str, float]:
    selected = frame[frame["YrMo"].between(start, end)]
    sold = selected[selected["EventType"].eq("Closed Sale")]
    listings = selected[selected["EventType"].eq("New Listing")]
    return {
        "median_close_price": float(sold["ClosePrice"].median()),
        "average_days_on_market": float(sold["DaysOnMarket"].mean()),
        "median_price_per_sq_ft": float(sold["PricePerSqFt"].median()),
        "average_close_to_original_list_ratio": float(
            sold["CloseToOriginalListRatio"].mean()
        ),
        "new_listings": int(listings["NewListings"].sum()),
        "closed_sales": int(sold["ClosedSales"].sum()),
        "sales_volume": float(sold["ClosePrice"].sum()),
    }


def load_competition(path: Path) -> pd.DataFrame:
    columns = [
        "YrMo",
        "City",
        "CountyOrParish",
        "ListAgentFullName",
        "ListOfficeName",
        "SalesVolume",
        "UnitsSold",
    ]
    frame = pd.read_csv(path, usecols=columns, low_memory=False)
    frame["City"] = clean_name(frame["City"])
    frame["CountyOrParish"] = clean_name(frame["CountyOrParish"])
    frame["ListAgentFullName"] = clean_name(frame["ListAgentFullName"])
    frame["ListOfficeName"] = clean_name(frame["ListOfficeName"])
    return frame[
        frame["City"].eq(CITY)
        & frame["CountyOrParish"].eq(COUNTY)
        & frame["YrMo"].between(CURRENT_PERIOD_START, CURRENT_PERIOD_END)
    ].copy()


def rank_competitors(frame: pd.DataFrame, field: str) -> list[dict[str, object]]:
    valid = frame.dropna(subset=[field])
    ranked = (
        valid.groupby(field, observed=True)
        .agg(sales_volume=("SalesVolume", "sum"), units_sold=("UnitsSold", "sum"))
        .sort_values(["sales_volume", "units_sold"], ascending=False)
        .head(5)
        .reset_index()
    )
    return [
        {
            "name": str(row[field]),
            "sales_volume": float(row["sales_volume"]),
            "units_sold": int(row["units_sold"]),
        }
        for _, row in ranked.iterrows()
    ]


def build_metrics(market_path: Path, competitive_path: Path) -> dict[str, object]:
    market = load_market_data(market_path)
    monthly = monthly_market_summary(market)
    current_month = monthly.loc[LATEST_COMPLETE_MONTH]
    prior_month = monthly.loc[YEAR_AGO_MONTH]
    current_period = period_summary(
        market, CURRENT_PERIOD_START, CURRENT_PERIOD_END
    )
    prior_period = period_summary(market, PRIOR_PERIOD_START, PRIOR_PERIOD_END)
    competition = load_competition(competitive_path)
    agents = rank_competitors(competition, "ListAgentFullName")
    offices = rank_competitors(competition, "ListOfficeName")
    total_competitive_volume = float(competition["SalesVolume"].sum())

    monthly_records = []
    for month, row in monthly.loc["2024-01":LATEST_COMPLETE_MONTH].iterrows():
        monthly_records.append(
            {
                "month": str(month),
                "median_close_price": float(row["median_close_price"]),
                "average_days_on_market": float(row["average_days_on_market"]),
                "new_listings": int(row["new_listings"]),
                "closed_sales": int(row["closed_sales"]),
            }
        )

    changes = {
        "median_close_price_yoy_pct": percent_change(
            current_month["median_close_price"], prior_month["median_close_price"]
        ),
        "days_on_market_yoy_days": float(
            current_month["average_days_on_market"]
            - prior_month["average_days_on_market"]
        ),
        "price_per_sq_ft_yoy_pct": percent_change(
            current_month["median_price_per_sq_ft"],
            prior_month["median_price_per_sq_ft"],
        ),
        "closed_sales_yoy_pct": percent_change(
            current_month["closed_sales"], prior_month["closed_sales"]
        ),
        "new_listings_yoy_pct": percent_change(
            current_month["new_listings"], prior_month["new_listings"]
        ),
        "trailing_12m_sales_volume_pct": percent_change(
            current_period["sales_volume"], prior_period["sales_volume"]
        ),
    }

    return {
        "geography": {"city": CITY, "county": COUNTY, "state": "California"},
        "data_coverage": {
            "all_sales_start": "2024-01",
            "all_sales_end": "2026-06",
            "latest_complete_activity_month": LATEST_COMPLETE_MONTH,
            "current_trailing_12_months": [CURRENT_PERIOD_START, CURRENT_PERIOD_END],
            "prior_trailing_12_months": [PRIOR_PERIOD_START, PRIOR_PERIOD_END],
        },
        "latest_month": {
            "month": LATEST_COMPLETE_MONTH,
            "median_close_price": float(current_month["median_close_price"]),
            "average_days_on_market": float(
                current_month["average_days_on_market"]
            ),
            "median_price_per_sq_ft": float(
                current_month["median_price_per_sq_ft"]
            ),
            "average_close_to_original_list_ratio": float(
                current_month["average_close_to_original_list_ratio"]
            ),
            "new_listings": int(current_month["new_listings"]),
            "closed_sales": int(current_month["closed_sales"]),
            "sales_volume": float(current_month["sales_volume"]),
        },
        "year_ago_month": {
            "month": YEAR_AGO_MONTH,
            "median_close_price": float(prior_month["median_close_price"]),
            "average_days_on_market": float(prior_month["average_days_on_market"]),
            "median_price_per_sq_ft": float(prior_month["median_price_per_sq_ft"]),
            "average_close_to_original_list_ratio": float(
                prior_month["average_close_to_original_list_ratio"]
            ),
            "new_listings": int(prior_month["new_listings"]),
            "closed_sales": int(prior_month["closed_sales"]),
            "sales_volume": float(prior_month["sales_volume"]),
        },
        "current_trailing_12_months": current_period,
        "prior_trailing_12_months": prior_period,
        "changes": changes,
        "top_agents": agents,
        "top_offices": offices,
        "top_office_volume_share_pct": (
            offices[0]["sales_volume"] / total_competitive_volume * 100.0
            if offices and total_competitive_volume
            else None
        ),
        "monthly": monthly_records,
        "methodology": (
            "Cleaned Residential records after Week 7 IQR filtering. April 2026 "
            "is used as the latest complete activity month because May-June 2026 "
            "new-listing coverage is incomplete; closed-sale coverage extends "
            "through June 2026."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market-csv", type=Path, default=MARKET_CSV)
    parser.add_argument("--competitive-csv", type=Path, default=COMPETITIVE_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = build_metrics(args.market_csv, args.competitive_csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
