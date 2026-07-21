from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


# ==========================================================
# Project paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

SOLD_PATH = PROJECT_DIR / "combined_sold_202401_202606_residential.csv"
LISTING_PATH = PROJECT_DIR / "combined_listing_202401_202606_residential.csv"

OUTPUT_DIR = PROJECT_DIR / "outputs" / "week2"
PLOT_DIR = OUTPUT_DIR / "distribution_plots"
README_ASSET_DIR = SCRIPT_DIR / "assets"

NUMERIC_COLUMNS = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt",
]

PUBLISHED_PLOTS = {
    ("sold", "ClosePrice"): "sold-close-price-distribution.png",
    ("sold", "DaysOnMarket"): "sold-days-on-market-distribution.png",
}


# ==========================================================
# Helper functions
# ==========================================================

def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return missing counts and percentages for every column."""
    summary = pd.DataFrame(
        {
            "Missing Count": df.isna().sum(),
            "Missing %": (df.isna().mean() * 100).round(2),
        }
    )

    return summary.sort_values("Missing %", ascending=False)


def numeric_summary(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Generate descriptive statistics for available numeric columns."""
    available_columns = [column for column in columns if column in df.columns]

    if not available_columns:
        raise ValueError("None of the requested numeric columns exist in the dataset.")

    summary = (
        df[available_columns]
        .apply(pd.to_numeric, errors="coerce")
        .describe(
            percentiles=[0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
        )
        .T
        .rename(columns={"50%": "median"})
    )

    return summary


def outlier_summary(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Identify potential outliers using the 1.5 × IQR rule."""
    results: list[dict[str, object]] = []

    for column in columns:
        if column not in df.columns:
            continue

        data = pd.to_numeric(df[column], errors="coerce").dropna()

        if data.empty:
            continue

        q1 = data.quantile(0.25)
        median = data.median()
        q3 = data.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (data < lower_bound) | (data > upper_bound)
        outlier_count = int(outlier_mask.sum())

        results.append(
            {
                "Column": column,
                "Count": len(data),
                "Q1": q1,
                "Median": median,
                "Q3": q3,
                "IQR": iqr,
                "Lower Bound": lower_bound,
                "Upper Bound": upper_bound,
                "Outlier Count": outlier_count,
                "Outlier %": round(outlier_count / len(data) * 100, 2),
            }
        )

    return pd.DataFrame(results)


def save_distribution_plot(
    df: pd.DataFrame,
    column: str,
    dataset_name: str,
) -> None:
    """Save a histogram and boxplot for one numeric field."""
    if column not in df.columns:
        return

    data = pd.to_numeric(df[column], errors="coerce").dropna()

    if data.empty:
        return

    lower = data.quantile(0.01)
    upper = data.quantile(0.99)
    display_data = data.loc[data.between(lower, upper)]
    if display_data.empty or lower == upper:
        display_data = data

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].hist(display_data, bins=50, color="#2f6f9f", edgecolor="white")
    axes[0].set_title("Histogram (1st–99th percentile)")
    axes[0].set_xlabel(column)
    axes[0].set_ylabel("Frequency")

    axes[1].boxplot(display_data, vert=False, showfliers=True)
    axes[1].set_title("Boxplot (1st–99th percentile)")
    axes[1].set_xlabel(column)
    axes[1].set_yticks([])

    number_formatter = FuncFormatter(lambda value, _: f"{value:,.0f}")
    axes[0].xaxis.set_major_formatter(number_formatter)
    axes[1].xaxis.set_major_formatter(number_formatter)

    fig.suptitle(f"{dataset_name.title()} {column} Distribution")

    fig.tight_layout()

    output_path = PLOT_DIR / f"{dataset_name}_{column}_distribution.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight")

    published_name = PUBLISHED_PLOTS.get((dataset_name, column))
    if published_name:
        fig.savefig(
            README_ASSET_DIR / published_name,
            dpi=150,
            bbox_inches="tight",
        )
    plt.close(fig)


def validate_input_file(path: Path) -> None:
    """Stop with a clear message when an input file cannot be found."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Place the CSV in the same folder as this script, "
            "or update the path at the top of the file."
        )


# ==========================================================
# Main workflow
# ==========================================================

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    README_ASSET_DIR.mkdir(parents=True, exist_ok=True)

    validate_input_file(SOLD_PATH)
    validate_input_file(LISTING_PATH)

    print("Loading residential MLS datasets...")
    sold = pd.read_csv(SOLD_PATH, low_memory=False)
    listing = pd.read_csv(LISTING_PATH, low_memory=False)

    print("\nDataset dimensions")
    print(f"Sold: {sold.shape[0]:,} rows × {sold.shape[1]} columns")
    print(f"Listing: {listing.shape[0]:,} rows × {listing.shape[1]} columns")

    # ------------------------------------------------------
    # Missing-value analysis
    # ------------------------------------------------------

    print("\nCalculating missing-value summaries...")
    sold_missing = missing_summary(sold)
    listing_missing = missing_summary(listing)

    sold_missing.to_csv(
        OUTPUT_DIR / "sold_missing_summary.csv",
        index=True,
    )
    listing_missing.to_csv(
        OUTPUT_DIR / "listing_missing_summary.csv",
        index=True,
    )

    sold_high_missing = sold_missing[sold_missing["Missing %"] > 90]
    listing_high_missing = listing_missing[listing_missing["Missing %"] > 90]

    sold_high_missing.to_csv(
        OUTPUT_DIR / "sold_columns_over_90_percent_missing.csv",
        index=True,
    )
    listing_high_missing.to_csv(
        OUTPUT_DIR / "listing_columns_over_90_percent_missing.csv",
        index=True,
    )

    # ------------------------------------------------------
    # Numeric summaries
    # ------------------------------------------------------

    print("Generating numeric summaries...")
    sold_numeric = numeric_summary(sold, NUMERIC_COLUMNS)
    listing_numeric = numeric_summary(listing, NUMERIC_COLUMNS)

    sold_numeric.to_csv(
        OUTPUT_DIR / "sold_numeric_summary.csv",
        index=True,
    )
    listing_numeric.to_csv(
        OUTPUT_DIR / "listing_numeric_summary.csv",
        index=True,
    )

    # ------------------------------------------------------
    # Outlier review
    # ------------------------------------------------------

    print("Calculating IQR-based outlier summaries...")
    sold_outliers = outlier_summary(sold, NUMERIC_COLUMNS)
    listing_outliers = outlier_summary(listing, NUMERIC_COLUMNS)

    sold_outliers.to_csv(
        OUTPUT_DIR / "sold_outlier_summary.csv",
        index=False,
    )
    listing_outliers.to_csv(
        OUTPUT_DIR / "listing_outlier_summary.csv",
        index=False,
    )

    # ------------------------------------------------------
    # Distribution plots
    # ------------------------------------------------------

    print("Saving histograms and boxplots...")
    for column in NUMERIC_COLUMNS:
        save_distribution_plot(sold, column, "sold")
        save_distribution_plot(listing, column, "listing")

    print("\nWeek 2–3 dataset validation complete.")
    print(f"Sold columns with more than 90% missing: {len(sold_high_missing)}")
    print(f"Listing columns with more than 90% missing: {len(listing_high_missing)}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
