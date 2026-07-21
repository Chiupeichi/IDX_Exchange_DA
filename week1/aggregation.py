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
DUPLICATE_COLUMN_PATTERN = re.compile(r"^(?P<original>.+)\.(?P<suffix>\d+)$")
NUMERIC_DUPLICATE_COLUMNS = {
    "DaysOnMarket",
    "Latitude",
    "ListPrice",
    "LivingArea",
    "Longitude",
}
DUPLICATE_AUDIT_COLUMNS = [
    "dataset",
    "source_month",
    "source_file",
    "original_column",
    "duplicate_column",
    "rows_checked",
    "equivalent_rows",
    "canonical_only_rows",
    "duplicate_only_rows_recovered",
    "conflicting_non_null_rows_kept_canonical",
]


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


def equivalent_values(
    left: pd.Series,
    right: pd.Series,
    allow_numeric_formatting: bool,
) -> pd.Series:
    """Compare duplicate columns while tolerating formatting-only differences."""
    both_missing = left.isna() & right.isna()
    text_equal = (
        left.astype("string")
        .str.strip()
        .eq(right.astype("string").str.strip())
        .fillna(False)
    )

    if not allow_numeric_formatting:
        return both_missing | text_equal

    left_numeric = pd.to_numeric(left, errors="coerce")
    right_numeric = pd.to_numeric(right, errors="coerce")
    numeric_equal = left_numeric.notna() & right_numeric.notna() & left_numeric.eq(
        right_numeric
    )
    return both_missing | text_equal | numeric_equal


def remove_duplicate_columns(
    frame: pd.DataFrame,
    dataset: str,
    source_month: str,
    source_file: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Audit pandas ``.1`` columns, preserve information, and remove copies.

    Duplicate-only values are copied into the canonical column before removal.
    If both copies contain different non-null values, the canonical (first)
    column is retained and the conflict count is recorded for review.
    """
    duplicate_columns: list[tuple[str, str]] = []
    for column in frame.columns:
        match = DUPLICATE_COLUMN_PATTERN.fullmatch(column)
        if match and match.group("original") in frame.columns:
            duplicate_columns.append((match.group("original"), column))

    audit_rows: list[dict[str, object]] = []
    for original, duplicate in duplicate_columns:
        original_values = frame[original]
        duplicate_values = frame[duplicate]
        equivalent = equivalent_values(
            original_values,
            duplicate_values,
            allow_numeric_formatting=original in NUMERIC_DUPLICATE_COLUMNS,
        )
        canonical_only = original_values.notna() & duplicate_values.isna()
        duplicate_only = original_values.isna() & duplicate_values.notna()
        conflicts = (
            original_values.notna()
            & duplicate_values.notna()
            & ~equivalent
        )

        if duplicate_only.any():
            frame.loc[duplicate_only, original] = duplicate_values.loc[duplicate_only]

        audit_rows.append(
            {
                "dataset": dataset,
                "source_month": source_month,
                "source_file": source_file,
                "original_column": original,
                "duplicate_column": duplicate,
                "rows_checked": len(frame),
                "equivalent_rows": int(equivalent.sum()),
                "canonical_only_rows": int(canonical_only.sum()),
                "duplicate_only_rows_recovered": int(duplicate_only.sum()),
                "conflicting_non_null_rows_kept_canonical": int(conflicts.sum()),
            }
        )

    if duplicate_columns:
        frame = frame.drop(
            columns=[duplicate for _, duplicate in duplicate_columns]
        )

    remaining_duplicates = []
    for column in frame.columns:
        match = DUPLICATE_COLUMN_PATTERN.fullmatch(column)
        if match and match.group("original") in frame.columns:
            remaining_duplicates.append(column)
    if remaining_duplicates:
        raise ValueError(
            f"{dataset} {source_file}: duplicate columns remain after cleanup: "
            f"{', '.join(remaining_duplicates)}"
        )

    return frame, audit_rows


def build_dataset(
    prefix: str,
    label: str,
    prefer_filled: bool,
) -> tuple[
    pd.DataFrame,
    list[dict[str, object]],
    pd.DataFrame,
    list[dict[str, object]],
]:
    """Load, document, combine, and Residential-filter one MLS dataset."""
    selected_files = select_monthly_files(prefix, prefer_filled=prefer_filled)
    frames: list[pd.DataFrame] = []
    manifest_rows: list[dict[str, object]] = []
    duplicate_audit_rows: list[dict[str, object]] = []

    for month, path in selected_files:
        monthly = pd.read_csv(path, low_memory=False)
        monthly, monthly_duplicate_audit = remove_duplicate_columns(
            monthly,
            dataset=label,
            source_month=month,
            source_file=path.name,
        )
        duplicate_audit_rows.extend(monthly_duplicate_audit)
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

    return (
        residential,
        manifest_rows + [summary],
        property_type_summary,
        duplicate_audit_rows,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sold, sold_rows, sold_types, sold_duplicate_audit = build_dataset(
        prefix="CRMLSSold",
        label="sold",
        prefer_filled=True,
    )
    listings, listing_rows, listing_types, listing_duplicate_audit = build_dataset(
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
    duplicate_column_audit = pd.DataFrame(
        sold_duplicate_audit + listing_duplicate_audit,
        columns=DUPLICATE_AUDIT_COLUMNS,
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
    duplicate_column_audit.to_csv(
        OUTPUT_DIR / "duplicate_column_audit.csv",
        index=False,
    )

    print("Week 1 aggregation complete.")
    print(aggregation_summary.to_string(index=False))
    print(f"Saved: {sold_path.name}")
    print(f"Saved: {listing_path.name}")
    print(f"Saved reports to: {OUTPUT_DIR}")
    if not duplicate_column_audit.empty:
        duplicate_pairs = duplicate_column_audit[
            ["original_column", "duplicate_column"]
        ].drop_duplicates()
        conflicts = int(
            duplicate_column_audit[
                "conflicting_non_null_rows_kept_canonical"
            ].sum()
        )
        recovered = int(
            duplicate_column_audit["duplicate_only_rows_recovered"].sum()
        )
        print(
            f"Removed {len(duplicate_pairs)} duplicate column pairs after audit; "
            f"kept {conflicts} canonical conflicting values and recovered "
            f"{recovered} duplicate-only values."
        )


if __name__ == "__main__":
    main()
