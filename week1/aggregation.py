"""Week 1: combine monthly MLS data into Residential analysis datasets.

For Sold data, an ``_filled`` file is preferred when it exists for a month.
Those files contain the same transactions as the raw version, with missing
coordinates filled. Only one file is selected per month, so transactions are
never duplicated.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs" / "week1"
START_MONTH = pd.Period("2024-01", freq="M")


def get_month(path: Path) -> str:
    """Return YYYYMM from a monthly MLS filename."""
    match = re.search(r"(20\d{4})", path.name)
    if match is None:
        raise ValueError(f"Could not find a YYYYMM value in {path.name}")
    return match.group(1)


def select_monthly_files(prefix: str, prefer_filled: bool) -> list[tuple[str, Path]]:
    """Choose exactly one source file for each month.

    The selected files must cover every month from January 2024 through the
    latest month available for the dataset.  A ``_filled`` Sold file replaces,
    rather than supplements, the raw file for the same month.
    """
    candidates: dict[str, dict[str, Path]] = defaultdict(dict)

    for path in sorted(PROJECT_DIR.glob(f"{prefix}20*.csv")):
        month = get_month(path)
        version = "filled" if "_filled" in path.stem else "raw"
        candidates[month][version] = path

    if not candidates:
        raise FileNotFoundError(f"No monthly files found for prefix {prefix}")

    latest_month = pd.Period(max(candidates), freq="M")
    expected = pd.period_range(START_MONTH, latest_month, freq="M")
    missing = [period.strftime("%Y%m") for period in expected if period.strftime("%Y%m") not in candidates]

    if missing:
        raise ValueError(
            f"{prefix} is missing monthly files: {', '.join(missing)}. "
            "Download or generate the missing month before aggregating."
        )

    selected: list[tuple[str, Path]] = []
    for period in expected:
        month = period.strftime("%Y%m")
        versions = candidates[month]
        if prefer_filled and "filled" in versions:
            selected.append((month, versions["filled"]))
        elif "raw" in versions:
            selected.append((month, versions["raw"]))
        else:
            selected.append((month, versions["filled"]))

    return selected


def build_dataset(prefix: str, label: str, prefer_filled: bool) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Load, document, combine, and Residential-filter one MLS dataset."""
    selected_files = select_monthly_files(prefix, prefer_filled=prefer_filled)
    frames: list[pd.DataFrame] = []
    manifest_rows: list[dict[str, object]] = []

    for month, path in selected_files:
        monthly = pd.read_csv(path, low_memory=False)
        monthly["SourceMonth"] = month
        monthly["SourceFile"] = path.name
        frames.append(monthly)

        manifest_rows.append(
            {
                "dataset": label,
                "source_month": month,
                "source_file": path.name,
                "source_version": "filled" if "_filled" in path.stem else "raw",
                "rows_read": len(monthly),
                "residential_rows": int(monthly["PropertyType"].eq("Residential").sum()),
            }
        )

    rows_before_concat = sum(len(frame) for frame in frames)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    rows_after_concat = len(combined)

    if rows_before_concat != rows_after_concat:
        raise ValueError(
            f"{label}: concatenation row count does not reconcile "
            f"({rows_before_concat} != {rows_after_concat})."
        )

    property_type_summary = (
        combined["PropertyType"]
        .fillna("<missing>")
        .value_counts(dropna=False)
        .rename_axis("PropertyType")
        .reset_index(name="row_count")
    )
    property_type_summary.insert(0, "dataset", label)
    property_type_summary["percent_of_dataset"] = (
        property_type_summary["row_count"] / rows_after_concat * 100
    ).round(4)

    residential = combined.loc[
        combined["PropertyType"].eq("Residential")
    ].copy()

    summary = {
        "dataset": label,
        "first_month": selected_files[0][0],
        "last_month": selected_files[-1][0],
        "monthly_files_used": len(selected_files),
        "rows_before_concat": rows_before_concat,
        "rows_after_concat": rows_after_concat,
        "rows_before_residential_filter": rows_after_concat,
        "rows_after_residential_filter": len(residential),
    }

    return residential, manifest_rows + [summary], property_type_summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sold, sold_rows, sold_types = build_dataset(
        prefix="CRMLSSold",
        label="sold",
        prefer_filled=True,
    )
    listings, listing_rows, listing_types = build_dataset(
        prefix="CRMLSListing",
        label="listing",
        prefer_filled=False,
    )

    aggregation_summary = pd.DataFrame(
        [row for row in sold_rows + listing_rows if "rows_after_concat" in row]
    )
    source_manifest = pd.DataFrame(
        [row for row in sold_rows + listing_rows if "source_month" in row]
    )
    property_type_summary = pd.concat(
        [sold_types, listing_types], ignore_index=True
    )

    start_month = aggregation_summary["first_month"].min()
    end_month = aggregation_summary["last_month"].max()

    sold_path = PROJECT_DIR / f"combined_sold_{start_month}_{end_month}_residential.csv"
    listing_path = PROJECT_DIR / f"combined_listing_{start_month}_{end_month}_residential.csv"

    sold.to_csv(sold_path, index=False)
    listings.to_csv(listing_path, index=False)
    aggregation_summary.to_csv(OUTPUT_DIR / "aggregation_summary.csv", index=False)
    source_manifest.to_csv(OUTPUT_DIR / "source_manifest.csv", index=False)
    property_type_summary.to_csv(
        OUTPUT_DIR / "property_type_summary_before_filter.csv",
        index=False,
    )

    print("Week 1 aggregation complete.")
    print(aggregation_summary.to_string(index=False))
    print(f"Saved: {sold_path.name}")
    print(f"Saved: {listing_path.name}")
    print(f"Saved reports to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
