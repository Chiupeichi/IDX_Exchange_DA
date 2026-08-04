"""Week 7: flag IQR outliers and create a filtered analysis dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_PATH = PROJECT_DIR / "outputs" / "week6" / "sold_week6_engineered.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week7"
README_ASSET_DIR = SCRIPT_DIR / "assets"
CHUNK_SIZE = 25_000
IQR_MULTIPLIER = 1.5
OUTLIER_FIELDS = ["ClosePrice", "LivingArea", "DaysOnMarket"]


def load_numeric_fields(input_path: Path) -> pd.DataFrame:
    """Load only the fields needed to calculate dataset-wide IQR bounds."""
    numeric_data = pd.read_csv(
        input_path,
        usecols=OUTLIER_FIELDS,
        low_memory=False,
    )
    for field in OUTLIER_FIELDS:
        numeric_data[field] = pd.to_numeric(
            numeric_data[field], errors="coerce"
        )
    return numeric_data


def calculate_iqr_summary(
    numeric_data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    """Calculate 1.5 x IQR bounds and independent outlier counts."""
    summary_rows: list[dict[str, float | int | str]] = []
    bounds: dict[str, tuple[float, float]] = {}

    for field in OUTLIER_FIELDS:
        values = numeric_data[field]
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - IQR_MULTIPLIER * iqr
        upper_bound = q3 + IQR_MULTIPLIER * iqr
        outlier_flag = values.notna() & (
            values.lt(lower_bound) | values.gt(upper_bound)
        )
        bounds[field] = (lower_bound, upper_bound)
        summary_rows.append(
            {
                "field": field,
                "rows_total": len(numeric_data),
                "rows_non_null": int(values.notna().sum()),
                "rows_missing": int(values.isna().sum()),
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "outlier_count": int(outlier_flag.sum()),
                "outlier_pct": float(outlier_flag.mean() * 100),
            }
        )

    return pd.DataFrame(summary_rows), bounds


def add_quality_flags(
    data: pd.DataFrame,
    bounds: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Add IQR and business-rule flags without deleting source records."""
    result = data.copy()

    for field in OUTLIER_FIELDS:
        values = pd.to_numeric(result[field], errors="coerce")
        lower_bound, upper_bound = bounds[field]
        result[f"{field}_outlier_flag"] = values.notna() & (
            values.lt(lower_bound) | values.gt(upper_bound)
        )

    result["any_outlier_flag"] = result[
        [f"{field}_outlier_flag" for field in OUTLIER_FIELDS]
    ].any(axis=1)

    close_price = pd.to_numeric(result["ClosePrice"], errors="coerce")
    living_area = pd.to_numeric(result["LivingArea"], errors="coerce")
    days_on_market = pd.to_numeric(result["DaysOnMarket"], errors="coerce")
    result["ClosePrice_invalid_flag"] = close_price.notna() & close_price.le(0)
    result["LivingArea_invalid_flag"] = living_area.notna() & living_area.le(0)
    result["DaysOnMarket_invalid_flag"] = (
        days_on_market.notna() & days_on_market.lt(0)
    )
    result["business_rule_invalid_flag"] = result[
        [
            "ClosePrice_invalid_flag",
            "LivingArea_invalid_flag",
            "DaysOnMarket_invalid_flag",
        ]
    ].any(axis=1)
    result["analysis_exclude_flag"] = (
        result["any_outlier_flag"]
        | result["business_rule_invalid_flag"]
    )
    return result


def create_dataset_comparison(
    numeric_data: pd.DataFrame,
    bounds: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Compare row counts and medians before and after filtering."""
    flagged = add_quality_flags(numeric_data, bounds)
    filtered = flagged.loc[~flagged["analysis_exclude_flag"]]

    return pd.DataFrame(
        [
            {
                "dataset": "full_flagged",
                "row_count": len(flagged),
                "median_ClosePrice": numeric_data["ClosePrice"].median(),
                "median_LivingArea": numeric_data["LivingArea"].median(),
                "median_DaysOnMarket": numeric_data["DaysOnMarket"].median(),
            },
            {
                "dataset": "clean_filtered",
                "row_count": len(filtered),
                "median_ClosePrice": filtered["ClosePrice"].median(),
                "median_LivingArea": filtered["LivingArea"].median(),
                "median_DaysOnMarket": filtered["DaysOnMarket"].median(),
            },
        ]
    )


def save_outlier_chart(summary: pd.DataFrame) -> None:
    """Save aggregate outlier counts for the public Week 7 README."""
    fig, axis = plt.subplots(figsize=(8.5, 4.5))
    bars = axis.barh(
        summary["field"],
        summary["outlier_count"],
        color="#2f6f9f",
    )
    axis.invert_yaxis()
    axis.set_title("Week 7 IQR Outlier Flags")
    axis.set_xlabel("Rows flagged")
    axis.bar_label(bars, fmt="{:,.0f}", padding=4)
    axis.set_xlim(0, summary["outlier_count"].max() * 1.15)
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(
        README_ASSET_DIR / "iqr-outlier-counts.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)


def write_flagged_and_filtered_outputs(
    bounds: dict[str, tuple[float, float]],
) -> tuple[int, int, int]:
    """Stream the wide Week 6 dataset into full and filtered outputs."""
    flagged_path = OUTPUT_DIR / "sold_week7_flagged.csv"
    filtered_path = OUTPUT_DIR / "sold_week7_filtered.csv"
    rows_processed = 0
    rows_filtered = 0
    business_rule_invalid_rows = 0
    first_chunk = True

    for chunk in pd.read_csv(INPUT_PATH, chunksize=CHUNK_SIZE, low_memory=False):
        missing_fields = set(OUTLIER_FIELDS) - set(chunk.columns)
        if missing_fields:
            raise ValueError(
                "Week 7 input is missing required fields: "
                f"{sorted(missing_fields)}"
            )

        flagged_chunk = add_quality_flags(chunk, bounds)
        filtered_chunk = flagged_chunk.loc[
            ~flagged_chunk["analysis_exclude_flag"]
        ]
        mode = "w" if first_chunk else "a"
        flagged_chunk.to_csv(
            flagged_path,
            index=False,
            mode=mode,
            header=first_chunk,
        )
        filtered_chunk.to_csv(
            filtered_path,
            index=False,
            mode=mode,
            header=first_chunk,
        )
        first_chunk = False
        rows_processed += len(flagged_chunk)
        rows_filtered += len(filtered_chunk)
        business_rule_invalid_rows += int(
            flagged_chunk["business_rule_invalid_flag"].sum()
        )

    return rows_processed, rows_filtered, business_rule_invalid_rows


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Week 6 output not found. Run "
            "`python3 week6/feature_engineering.py` first."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    README_ASSET_DIR.mkdir(parents=True, exist_ok=True)

    numeric_data = load_numeric_fields(INPUT_PATH)
    iqr_summary, bounds = calculate_iqr_summary(numeric_data)
    dataset_comparison = create_dataset_comparison(numeric_data, bounds)
    rows_processed, rows_filtered, invalid_rows = (
        write_flagged_and_filtered_outputs(bounds)
    )

    if rows_processed != len(numeric_data):
        raise RuntimeError(
            "Flagged output row count does not match the Week 6 input."
        )
    expected_filtered_rows = int(
        dataset_comparison.loc[
            dataset_comparison["dataset"].eq("clean_filtered"), "row_count"
        ].iloc[0]
    )
    if rows_filtered != expected_filtered_rows:
        raise RuntimeError(
            "Filtered output row count does not match the calculated summary."
        )

    iqr_summary.to_csv(OUTPUT_DIR / "outlier_summary.csv", index=False)
    dataset_comparison.to_csv(
        OUTPUT_DIR / "dataset_comparison.csv", index=False
    )
    save_outlier_chart(iqr_summary)

    print("Week 7 outlier detection complete.")
    print(f"Rows in full flagged dataset: {rows_processed:,}")
    print(f"Rows in clean filtered dataset: {rows_filtered:,}")
    print(f"Rows excluded: {rows_processed - rows_filtered:,}")
    print(f"Business-rule invalid rows: {invalid_rows:,}")
    print(f"Saved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
