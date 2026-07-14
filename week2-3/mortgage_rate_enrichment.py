from pathlib import Path
import pandas as pd

# ==========================================================
# File Paths
# ==========================================================

PROJECT_DIR = Path.cwd()

SOLD_PATH = PROJECT_DIR / "combined_sold_202401_202604.csv"
LISTINGS_PATH = PROJECT_DIR / "combined_listing_202401_202604.csv"

OUTPUT_DIR = PROJECT_DIR / "outputs" / "week2_3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# Load MLS datasets
# ==========================================================

print("Loading datasets...")

sold = pd.read_csv(SOLD_PATH, low_memory=False)
listings = pd.read_csv(LISTINGS_PATH, low_memory=False)

# ==========================================================
# Fetch mortgage rate data from FRED
# ==========================================================

print("Downloading mortgage rates from FRED...")

FRED_MORTGAGE_URL = (
    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
)

mortgage = pd.read_csv(
    FRED_MORTGAGE_URL,
    parse_dates=["observation_date"]
)

mortgage = mortgage.rename(
    columns={
        "observation_date": "date",
        "MORTGAGE30US": "rate_30yr_fixed"
    }
)

# ==========================================================
# Convert weekly rates to monthly averages
# ==========================================================

mortgage["rate_30yr_fixed"] = pd.to_numeric(
    mortgage["rate_30yr_fixed"],
    errors="coerce"
)

mortgage = mortgage.dropna(
    subset=["date", "rate_30yr_fixed"]
)

mortgage["year_month"] = (
    mortgage["date"]
    .dt.to_period("M")
    .astype(str)
)

mortgage_monthly = (
    mortgage
    .groupby("year_month", as_index=False)
    .agg(
        rate_30yr_fixed=("rate_30yr_fixed", "mean"),
        weekly_observation_count=("rate_30yr_fixed", "size")
    )
)

# ==========================================================
# Create year_month keys
# ==========================================================

print("Creating year-month keys...")

sold["CloseDate"] = pd.to_datetime(
    sold["CloseDate"],
    errors="coerce"
)

sold["year_month"] = (
    sold["CloseDate"]
    .dt.to_period("M")
    .astype(str)
)

listings["ListingContractDate"] = pd.to_datetime(
    listings["ListingContractDate"],
    errors="coerce"
)

listings["year_month"] = (
    listings["ListingContractDate"]
    .dt.to_period("M")
    .astype(str)
)

# ==========================================================
# Merge mortgage rates
# ==========================================================

print("Merging mortgage rates...")

sold_with_rates = sold.merge(
    mortgage_monthly,
    on="year_month",
    how="left",
    validate="many_to_one"
)

listings_with_rates = listings.merge(
    mortgage_monthly,
    on="year_month",
    how="left",
    validate="many_to_one"
)

# ==========================================================
# Validation
# ==========================================================

print("\nValidation Results")

print(
    "Missing sold mortgage rates:",
    sold_with_rates["rate_30yr_fixed"].isna().sum()
)

print(
    "Missing listings mortgage rates:",
    listings_with_rates["rate_30yr_fixed"].isna().sum()
)

print(
    "Sold rows:",
    len(sold),
    "→",
    len(sold_with_rates)
)

print(
    "Listings rows:",
    len(listings),
    "→",
    len(listings_with_rates)
)

# ==========================================================
# Save outputs
# ==========================================================

print("\nSaving datasets...")

mortgage_monthly.to_csv(
    OUTPUT_DIR / "mortgage_rate_monthly.csv",
    index=False
)

sold_with_rates.to_csv(
    OUTPUT_DIR / "sold_with_mortgage_rates.csv",
    index=False
)

listings_with_rates.to_csv(
    OUTPUT_DIR / "listings_with_mortgage_rates.csv",
    index=False
)

print("Done!")
print("Output folder:", OUTPUT_DIR)
