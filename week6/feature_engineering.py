"""Week 6: create Residential market metrics and segmented summaries."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_PATH = PROJECT_DIR / "outputs" / "week4_5" / "sold_clean.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week6"
README_ASSET_DIR = SCRIPT_DIR / "assets"
CHUNK_SIZE = 25_000


def validate_residential_only(df: pd.DataFrame) -> None:
    property_types = set(df["PropertyType"].dropna().unique())
    if property_types != {"Residential"}:
        raise ValueError(
            "Week 6 must start from a Residential-only dataset; found "
            f"{sorted(property_types)}"
        )


def engineer_market_metrics(sold: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create price, time-series, and transaction-timeline metrics."""
    result = sold.copy()

    date_columns = [
        "CloseDate",
        "ListingContractDate",
        "PurchaseContractDate",
    ]
    numeric_columns = [
        "ClosePrice",
        "OriginalListPrice",
        "LivingArea",
        "DaysOnMarket",
    ]

    for column in date_columns:
        result[column] = pd.to_datetime(result[column], errors="coerce")
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    valid_original_list_price = result["OriginalListPrice"].where(
        result["OriginalListPrice"].gt(0)
    )
    valid_living_area = result["LivingArea"].where(
        result["LivingArea"].gt(0)
    )

    # The handbook requests both names; they use the same formula.
    result["PriceRatio"] = (
        result["ClosePrice"] / valid_original_list_price
    )
    result["CloseToOriginalListRatio"] = result["PriceRatio"]
    result["PricePerSqFt"] = result["ClosePrice"] / valid_living_area

    result["Year"] = result["CloseDate"].dt.year.astype("Int64")
    result["Month"] = result["CloseDate"].dt.month.astype("Int64")
    result["YrMo"] = result["CloseDate"].dt.strftime("%Y-%m")
    result["ListingToContractDays"] = (
        result["PurchaseContractDate"] - result["ListingContractDate"]
    ).dt.days
    result["ContractToCloseDays"] = (
        result["CloseDate"] - result["PurchaseContractDate"]
    ).dt.days

    result["price_ratio_eligible_flag"] = result["PriceRatio"].notna()
    result["ppsf_eligible_flag"] = result["PricePerSqFt"].notna()
    result["listing_to_contract_eligible_flag"] = (
        result["ListingToContractDays"].notna()
    )
    result["contract_to_close_eligible_flag"] = (
        result["ContractToCloseDays"].notna()
    )

    quality_summary = pd.DataFrame(
        [
            {
                "metric": "PriceRatio / CloseToOriginalListRatio",
                "rows_populated": int(result["price_ratio_eligible_flag"].sum()),
                "rows_missing": int(result["PriceRatio"].isna().sum()),
            },
            {
                "metric": "PricePerSqFt",
                "rows_populated": int(result["ppsf_eligible_flag"].sum()),
                "rows_missing": int(result["PricePerSqFt"].isna().sum()),
            },
            {
                "metric": "ListingToContractDays",
                "rows_populated": int(
                    result["listing_to_contract_eligible_flag"].sum()
                ),
                "rows_missing": int(result["ListingToContractDays"].isna().sum()),
            },
            {
                "metric": "ContractToCloseDays",
                "rows_populated": int(
                    result["contract_to_close_eligible_flag"].sum()
                ),
                "rows_missing": int(result["ContractToCloseDays"].isna().sum()),
            },
        ]
    )

    return result, quality_summary


def create_county_summary(sold: pd.DataFrame) -> pd.DataFrame:
    """Produce the required Week 6 segmented summary table."""
    return (
        sold.groupby("CountyOrParish", dropna=False)
        .agg(
            Transactions=("ListingKey", "size"),
            MedianClosePrice=("ClosePrice", "median"),
            AveragePricePerSqFt=("PricePerSqFt", "mean"),
            AveragePriceRatio=("PriceRatio", "mean"),
            AverageDaysOnMarket=("DaysOnMarket", "mean"),
            AverageListingToContractDays=("ListingToContractDays", "mean"),
            AverageContractToCloseDays=("ContractToCloseDays", "mean"),
        )
        .reset_index()
        .sort_values("Transactions", ascending=False)
    )


def save_metric_quality_chart(summary: pd.DataFrame) -> None:
    """Save aggregate metric-missing counts for the Week 6 README."""
    labels = summary["metric"].replace(
        {"PriceRatio / CloseToOriginalListRatio": "Price ratios"}
    )
    fig, axis = plt.subplots(figsize=(8.5, 4.5))
    bars = axis.barh(labels, summary["rows_missing"], color="#2f6f9f")
    axis.invert_yaxis()
    axis.set_title("Week 6 Metric Quality — Missing Rows")
    axis.set_xlabel("Rows missing")
    axis.bar_label(bars, fmt="{:,.0f}", padding=4)
    axis.set_xlim(0, summary["rows_missing"].max() * 1.15)
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(
        README_ASSET_DIR / "metric-missing-rows.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    README_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    engineered_output_path = OUTPUT_DIR / "sold_week6_engineered.csv"
    metric_counts = {
        "PriceRatio / CloseToOriginalListRatio": [0, 0],
        "PricePerSqFt": [0, 0],
        "ListingToContractDays": [0, 0],
        "ContractToCloseDays": [0, 0],
    }
    rows_processed = 0
    first_chunk = True

    # Stream the wide MLS dataset instead of retaining all 435k rows in memory.
    for chunk in pd.read_csv(INPUT_PATH, chunksize=CHUNK_SIZE, low_memory=False):
        validate_residential_only(chunk)
        engineered_chunk, _ = engineer_market_metrics(chunk)
        engineered_chunk.to_csv(
            engineered_output_path,
            index=False,
            mode="w" if first_chunk else "a",
            header=first_chunk,
        )
        first_chunk = False
        rows_processed += len(engineered_chunk)

        metric_counts["PriceRatio / CloseToOriginalListRatio"][0] += int(
            engineered_chunk["PriceRatio"].notna().sum()
        )
        metric_counts["PriceRatio / CloseToOriginalListRatio"][1] += int(
            engineered_chunk["PriceRatio"].isna().sum()
        )
        metric_counts["PricePerSqFt"][0] += int(
            engineered_chunk["PricePerSqFt"].notna().sum()
        )
        metric_counts["PricePerSqFt"][1] += int(
            engineered_chunk["PricePerSqFt"].isna().sum()
        )
        metric_counts["ListingToContractDays"][0] += int(
            engineered_chunk["ListingToContractDays"].notna().sum()
        )
        metric_counts["ListingToContractDays"][1] += int(
            engineered_chunk["ListingToContractDays"].isna().sum()
        )
        metric_counts["ContractToCloseDays"][0] += int(
            engineered_chunk["ContractToCloseDays"].notna().sum()
        )
        metric_counts["ContractToCloseDays"][1] += int(
            engineered_chunk["ContractToCloseDays"].isna().sum()
        )

    metric_quality_summary = pd.DataFrame(
        [
            {
                "metric": metric,
                "rows_populated": populated,
                "rows_missing": missing,
            }
            for metric, (populated, missing) in metric_counts.items()
        ]
    )

    summary_columns = [
        "ListingKey",
        "CloseDate",
        "ClosePrice",
        "OriginalListPrice",
        "LivingArea",
        "PriceRatio",
        "CloseToOriginalListRatio",
        "PricePerSqFt",
        "DaysOnMarket",
        "Year",
        "Month",
        "YrMo",
        "ListingToContractDays",
        "ContractToCloseDays",
        "CountyOrParish",
    ]
    summary_data = pd.read_csv(
        engineered_output_path,
        usecols=summary_columns,
        low_memory=False,
    )

    county_summary = create_county_summary(summary_data)
    sample_columns = [
        "ListingKey",
        "CloseDate",
        "ClosePrice",
        "OriginalListPrice",
        "LivingArea",
        "PriceRatio",
        "CloseToOriginalListRatio",
        "PricePerSqFt",
        "DaysOnMarket",
        "Year",
        "Month",
        "YrMo",
        "ListingToContractDays",
        "ContractToCloseDays",
        "CountyOrParish",
    ]
    sample_output = summary_data.loc[
        summary_data["PriceRatio"].notna()
        & summary_data["PricePerSqFt"].notna()
        & summary_data["ListingToContractDays"].notna()
        & summary_data["ContractToCloseDays"].notna(),
        sample_columns,
    ].head(20)

    sample_output.to_csv(OUTPUT_DIR / "week6_sample_output.csv", index=False)
    county_summary.to_csv(OUTPUT_DIR / "county_summary.csv", index=False)
    metric_quality_summary.to_csv(
        OUTPUT_DIR / "metric_quality_summary.csv", index=False
    )
    save_metric_quality_chart(metric_quality_summary)

    print("Week 6 feature engineering complete.")
    print(f"Rows processed: {rows_processed:,}")
    print(f"Saved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
