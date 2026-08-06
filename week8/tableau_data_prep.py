"""Week 8: prepare compact, validated data sources for Tableau Public."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
SOLD_INPUT_PATH = (
    PROJECT_DIR / "outputs" / "week7" / "sold_week7_filtered.csv"
)
LISTING_INPUT_PATH = (
    PROJECT_DIR / "outputs" / "week4_5" / "listings_clean.csv"
)
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week8"
README_ASSET_DIR = SCRIPT_DIR / "assets"
CHUNK_SIZE = 25_000

DIMENSION_COLUMNS = [
    "PropertyType",
    "PropertySubType",
    "City",
    "CountyOrParish",
    "PostalCode",
    "MLSAreaMajor",
    "StateOrProvince",
]

SOLD_COLUMNS = [
    "ListingKey",
    "CloseDate",
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket",
    "CloseToOriginalListRatio",
    "PricePerSqFt",
    "rate_30yr_fixed",
    "ListAgentFullName",
    "ListAgentFirstName",
    "ListAgentLastName",
    "ListOfficeName",
    "BuyerOfficeName",
    *DIMENSION_COLUMNS,
]

LISTING_COLUMNS = [
    "ListingKey",
    "ListingContractDate",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "rate_30yr_fixed",
    *DIMENSION_COLUMNS,
]

MARKET_COLUMNS = [
    "EventId",
    "EventType",
    "EventDate",
    "Year",
    "Month",
    "YrMo",
    "ListingKey",
    *DIMENSION_COLUMNS,
    "ListPrice",
    "OriginalListPrice",
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "CloseToOriginalListRatio",
    "CloseToOriginalListRatioOutlierFlag",
    "CloseToOriginalListRatioEligible",
    "PricePerSqFt",
    "rate_30yr_fixed",
    "NewListings",
    "ClosedSales",
    "RecordCount",
    "SourceDataset",
]

COMPETITIVE_COLUMNS = [
    "EventId",
    "CloseDate",
    "Year",
    "Month",
    "YrMo",
    "ListingKey",
    "ListAgentFullName",
    "ListOfficeName",
    "BuyerOfficeName",
    *DIMENSION_COLUMNS,
    "ClosePrice",
    "SalesVolume",
    "UnitsSold",
    "DaysOnMarket",
    "CloseToOriginalListRatio",
    "CloseToOriginalListRatioOutlierFlag",
    "CloseToOriginalListRatioEligible",
    "PricePerSqFt",
    "rate_30yr_fixed",
]


def validate_columns(
    input_path: Path, required_columns: list[str], dataset_name: str
) -> None:
    """Fail clearly when an upstream output does not match expectations."""
    available_columns = set(pd.read_csv(input_path, nrows=0).columns)
    missing_columns = set(required_columns) - available_columns
    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def clean_string(series: pd.Series) -> pd.Series:
    """Trim text while retaining missing values for Tableau filters."""
    result = series.astype("string").str.strip()
    return result.mask(result.eq(""))


def prepare_dimensions(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize common geographic and property dimensions."""
    result = data.copy()
    for column in DIMENSION_COLUMNS:
        result[column] = clean_string(result[column])
    result["PostalCode"] = result["PostalCode"].str.replace(
        r"\.0$", "", regex=True
    )
    property_types = set(result["PropertyType"].dropna().unique())
    if property_types != {"Residential"}:
        raise ValueError(
            "Week 8 requires Residential-only inputs; found "
            f"{sorted(property_types)}"
        )
    return result


def add_event_dates(
    data: pd.DataFrame, source_date_column: str
) -> pd.DataFrame:
    """Create Tableau-friendly calendar fields from the event date."""
    result = data.copy()
    result["EventDate"] = pd.to_datetime(
        result[source_date_column], errors="coerce"
    )
    if result["EventDate"].isna().any():
        raise ValueError(
            f"{source_date_column} contains missing or invalid dates."
        )
    result["Year"] = result["EventDate"].dt.year.astype("Int64")
    result["Month"] = result["EventDate"].dt.month.astype("Int64")
    result["YrMo"] = result["EventDate"].dt.strftime("%Y-%m")
    return result


def calculate_ratio_iqr_bounds() -> tuple[float, float]:
    """Calculate sold-to-original-list ratio bounds for its Tableau average."""
    ratio = pd.to_numeric(
        pd.read_csv(
            SOLD_INPUT_PATH,
            usecols=["CloseToOriginalListRatio"],
            low_memory=False,
        )["CloseToOriginalListRatio"],
        errors="coerce",
    )
    q1 = float(ratio.quantile(0.25))
    q3 = float(ratio.quantile(0.75))
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def apply_ratio_quality(
    data: pd.DataFrame, ratio_bounds: tuple[float, float]
) -> pd.DataFrame:
    """Exclude ratio-only outliers from averages without dropping sale rows."""
    result = data.copy()
    ratio = pd.to_numeric(
        result["CloseToOriginalListRatio"], errors="coerce"
    )
    lower_bound, upper_bound = ratio_bounds
    outlier_flag = ratio.notna() & (
        ratio.lt(lower_bound) | ratio.gt(upper_bound)
    )
    result["CloseToOriginalListRatioOutlierFlag"] = outlier_flag
    result["CloseToOriginalListRatioEligible"] = (
        ratio.notna() & ~outlier_flag
    )
    result["CloseToOriginalListRatio"] = ratio.where(
        result["CloseToOriginalListRatioEligible"]
    )
    return result


def prepare_sold_market_events(
    data: pd.DataFrame, ratio_bounds: tuple[float, float]
) -> pd.DataFrame:
    """Convert clean sold rows into closed-sale event records."""
    result = prepare_dimensions(data)
    result = add_event_dates(result, "CloseDate")
    result = apply_ratio_quality(result, ratio_bounds)
    result["EventType"] = "Closed Sale"
    result["EventId"] = (
        "Closed Sale|"
        + clean_string(result["ListingKey"])
        + "|"
        + result["EventDate"].dt.strftime("%Y-%m-%d")
    )
    result["NewListings"] = 0
    result["ClosedSales"] = 1
    result["RecordCount"] = 1
    result["SourceDataset"] = "Week 7 clean filtered sold"
    return result[MARKET_COLUMNS]


def prepare_listing_market_events(data: pd.DataFrame) -> pd.DataFrame:
    """Convert clean listing rows into new-listing event records."""
    result = prepare_dimensions(data)
    result = add_event_dates(result, "ListingContractDate")
    result["EventType"] = "New Listing"
    result["EventId"] = (
        "New Listing|"
        + clean_string(result["ListingKey"])
        + "|"
        + result["EventDate"].dt.strftime("%Y-%m-%d")
    )
    for column in [
        "ClosePrice",
        "DaysOnMarket",
        "CloseToOriginalListRatio",
        "PricePerSqFt",
    ]:
        result[column] = pd.NA
    result["CloseToOriginalListRatioOutlierFlag"] = False
    result["CloseToOriginalListRatioEligible"] = False
    result["NewListings"] = 1
    result["ClosedSales"] = 0
    result["RecordCount"] = 1
    result["SourceDataset"] = "Weeks 4-5 clean listings"
    return result[MARKET_COLUMNS]


def prepare_competitive_sales(
    data: pd.DataFrame, ratio_bounds: tuple[float, float]
) -> pd.DataFrame:
    """Select agent, office, sales, and geography fields for Tableau."""
    result = prepare_dimensions(data)
    result = add_event_dates(result, "CloseDate")
    result = apply_ratio_quality(result, ratio_bounds)
    fallback_name = (
        clean_string(result["ListAgentFirstName"]).fillna("")
        + " "
        + clean_string(result["ListAgentLastName"]).fillna("")
    ).str.strip()
    fallback_name = fallback_name.mask(fallback_name.eq(""))
    result["ListAgentFullName"] = clean_string(
        result["ListAgentFullName"]
    ).fillna(fallback_name)
    result["ListOfficeName"] = clean_string(result["ListOfficeName"])
    result["BuyerOfficeName"] = clean_string(result["BuyerOfficeName"])
    result["EventId"] = (
        "Closed Sale|"
        + clean_string(result["ListingKey"])
        + "|"
        + result["EventDate"].dt.strftime("%Y-%m-%d")
    )
    result["CloseDate"] = result["EventDate"]
    result["SalesVolume"] = pd.to_numeric(
        result["ClosePrice"], errors="coerce"
    )
    result["UnitsSold"] = 1
    return result[COMPETITIVE_COLUMNS]


def append_unique_events(
    events: pd.DataFrame,
    output_path: Path,
    seen_event_ids: set[str],
    write_header: bool,
) -> tuple[int, int, bool, pd.DataFrame]:
    """Remove exact event duplicates across and within input chunks."""
    duplicate_mask = (
        events["EventId"].isin(seen_event_ids)
        | events["EventId"].duplicated(keep="first")
    )
    unique_events = events.loc[~duplicate_mask].copy()
    seen_event_ids.update(unique_events["EventId"].dropna().tolist())
    unique_events.to_csv(
        output_path,
        index=False,
        mode="w" if write_header else "a",
        header=write_header,
    )
    return (
        len(unique_events),
        int(duplicate_mask.sum()),
        False,
        unique_events,
    )


def write_tableau_sources(
    ratio_bounds: tuple[float, float],
) -> dict[str, int]:
    """Stream upstream datasets into compact market and competitive files."""
    market_path = OUTPUT_DIR / "tableau_market_events.csv"
    competitive_path = OUTPUT_DIR / "tableau_competitive_sales.csv"
    seen_market_ids: set[str] = set()
    seen_competitive_ids: set[str] = set()
    market_header = True
    competitive_header = True
    counts = {
        "sold_input_rows": 0,
        "listing_input_rows": 0,
        "closed_sale_events": 0,
        "new_listing_events": 0,
        "sold_exact_duplicates_removed": 0,
        "listing_exact_duplicates_removed": 0,
        "competitive_sales_rows": 0,
        "ratio_outlier_rows": 0,
        "ratio_eligible_rows": 0,
    }
    dtype = {"ListingKey": "string", "PostalCode": "string"}

    for chunk in pd.read_csv(
        SOLD_INPUT_PATH,
        usecols=SOLD_COLUMNS,
        dtype=dtype,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        counts["sold_input_rows"] += len(chunk)
        market_events = prepare_sold_market_events(chunk, ratio_bounds)
        unique_rows, duplicates, market_header, unique_market = (
            append_unique_events(
                market_events,
                market_path,
                seen_market_ids,
                market_header,
            )
        )
        counts["closed_sale_events"] += unique_rows
        counts["sold_exact_duplicates_removed"] += duplicates
        counts["ratio_outlier_rows"] += int(
            unique_market["CloseToOriginalListRatioOutlierFlag"].sum()
        )
        counts["ratio_eligible_rows"] += int(
            unique_market["CloseToOriginalListRatioEligible"].sum()
        )

        competitive_events = prepare_competitive_sales(chunk, ratio_bounds)
        unique_competitive, _, competitive_header, _ = append_unique_events(
            competitive_events,
            competitive_path,
            seen_competitive_ids,
            competitive_header,
        )
        if unique_competitive != len(unique_market):
            raise RuntimeError(
                "Market and competitive sold row counts do not match."
            )
        counts["competitive_sales_rows"] += unique_competitive

    for chunk in pd.read_csv(
        LISTING_INPUT_PATH,
        usecols=LISTING_COLUMNS,
        dtype=dtype,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        counts["listing_input_rows"] += len(chunk)
        market_events = prepare_listing_market_events(chunk)
        unique_rows, duplicates, market_header, _ = append_unique_events(
            market_events,
            market_path,
            seen_market_ids,
            market_header,
        )
        counts["new_listing_events"] += unique_rows
        counts["listing_exact_duplicates_removed"] += duplicates

    return counts


def create_market_monthly_summary() -> pd.DataFrame:
    """Create a compact validation table for all required market measures."""
    data = pd.read_csv(
        OUTPUT_DIR / "tableau_market_events.csv",
        usecols=[
            "YrMo",
            "NewListings",
            "ClosedSales",
            "ClosePrice",
            "DaysOnMarket",
            "CloseToOriginalListRatio",
        ],
        low_memory=False,
    )
    summary = (
        data.groupby("YrMo", as_index=False)
        .agg(
            NewListings=("NewListings", "sum"),
            ClosedSales=("ClosedSales", "sum"),
            MedianClosePrice=("ClosePrice", "median"),
            AverageDaysOnMarket=("DaysOnMarket", "mean"),
            AverageCloseToOriginalListRatio=(
                "CloseToOriginalListRatio",
                "mean",
            ),
        )
        .sort_values("YrMo")
    )
    new_listing_threshold = summary["NewListings"].median() * 0.5
    closed_sales_threshold = summary["ClosedSales"].median() * 0.5
    summary["NewListingsLowVolumeFlag"] = summary["NewListings"].lt(
        new_listing_threshold
    )
    summary["ClosedSalesLowVolumeFlag"] = summary["ClosedSales"].lt(
        closed_sales_threshold
    )
    return summary


def create_competitive_summaries() -> None:
    """Create local top-100 validation tables for agents and offices."""
    data = pd.read_csv(
        OUTPUT_DIR / "tableau_competitive_sales.csv",
        usecols=[
            "ListAgentFullName",
            "ListOfficeName",
            "SalesVolume",
            "UnitsSold",
        ],
        low_memory=False,
    )
    for dimension, filename in [
        ("ListAgentFullName", "top_100_listing_agents.csv"),
        ("ListOfficeName", "top_100_listing_offices.csv"),
    ]:
        summary = (
            data.dropna(subset=[dimension])
            .groupby(dimension, as_index=False)
            .agg(
                SalesVolume=("SalesVolume", "sum"),
                UnitsSold=("UnitsSold", "sum"),
            )
            .sort_values(
                ["SalesVolume", "UnitsSold"],
                ascending=[False, False],
            )
            .head(100)
        )
        summary.to_csv(OUTPUT_DIR / filename, index=False)


def create_quality_summary(
    counts: dict[str, int],
    monthly_summary: pd.DataFrame,
    ratio_bounds: tuple[float, float],
) -> pd.DataFrame:
    """Record row reconciliation and calendar coverage for auditability."""
    market_rows = counts["closed_sale_events"] + counts["new_listing_events"]
    low_listing_months = monthly_summary.loc[
        monthly_summary["NewListingsLowVolumeFlag"], "YrMo"
    ].tolist()
    low_closed_months = monthly_summary.loc[
        monthly_summary["ClosedSalesLowVolumeFlag"], "YrMo"
    ].tolist()
    return pd.DataFrame(
        [
            {
                **counts,
                "market_event_rows": market_rows,
                "calendar_months": len(monthly_summary),
                "first_month": monthly_summary["YrMo"].min(),
                "latest_month": monthly_summary["YrMo"].max(),
                "ratio_iqr_lower_bound": ratio_bounds[0],
                "ratio_iqr_upper_bound": ratio_bounds[1],
                "low_new_listing_months": ";".join(low_listing_months),
                "low_closed_sales_months": ";".join(low_closed_months),
            }
        ]
    )


def save_market_activity_chart(monthly_summary: pd.DataFrame) -> None:
    """Save a public aggregate chart that validates monthly event counts."""
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.plot(
        monthly_summary["YrMo"],
        monthly_summary["NewListings"],
        label="New listings",
        color="#2f6f9f",
        linewidth=2,
    )
    axis.plot(
        monthly_summary["YrMo"],
        monthly_summary["ClosedSales"],
        label="Closed sales",
        color="#d97941",
        linewidth=2,
    )
    axis.set_title("Monthly Residential Market Activity")
    axis.set_xlabel("Month")
    axis.set_ylabel("Events")
    axis.tick_params(axis="x", rotation=45)
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    for index, label in enumerate(axis.get_xticklabels()):
        label.set_visible(index % 3 == 0 or index == len(monthly_summary) - 1)
    fig.tight_layout()
    fig.savefig(
        README_ASSET_DIR / "monthly-market-activity.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


def main() -> None:
    for path, columns, name in [
        (SOLD_INPUT_PATH, SOLD_COLUMNS, "Week 7 sold input"),
        (LISTING_INPUT_PATH, LISTING_COLUMNS, "Weeks 4-5 listing input"),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{name} not found: {path}")
        validate_columns(path, columns, name)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    README_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    ratio_bounds = calculate_ratio_iqr_bounds()
    counts = write_tableau_sources(ratio_bounds)
    monthly_summary = create_market_monthly_summary()
    monthly_summary.to_csv(
        OUTPUT_DIR / "market_monthly_summary.csv", index=False
    )
    create_competitive_summaries()
    quality_summary = create_quality_summary(
        counts, monthly_summary, ratio_bounds
    )
    quality_summary.to_csv(
        OUTPUT_DIR / "tableau_data_quality_summary.csv", index=False
    )
    save_market_activity_chart(monthly_summary)

    print("Week 8 Tableau data preparation complete.")
    print(
        "Market events: "
        f"{int(quality_summary['market_event_rows'].iloc[0]):,}"
    )
    print(f"Closed-sale events: {counts['closed_sale_events']:,}")
    print(f"New-listing events: {counts['new_listing_events']:,}")
    print(
        "Exact duplicate sold events removed: "
        f"{counts['sold_exact_duplicates_removed']:,}"
    )
    print(
        "Ratio outliers excluded from ratio averages: "
        f"{counts['ratio_outlier_rows']:,}"
    )
    print(
        f"Coverage: {quality_summary['first_month'].iloc[0]} through "
        f"{quality_summary['latest_month'].iloc[0]}"
    )
    print(
        "Low-volume new-listing months: "
        f"{quality_summary['low_new_listing_months'].iloc[0]}"
    )
    print(
        "Low-volume closed-sales months: "
        f"{quality_summary['low_closed_sales_months'].iloc[0]}"
    )
    print(f"Saved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
