# IDX Exchange — Data Analyst Internship

Python workflows for the IDX Exchange MLS Analytics Program. The pipeline
combines monthly CRMLS files, validates and enriches Residential records,
cleans invalid observations, and creates Week 6 market metrics.

The repository contains code only. Raw and generated MLS CSV files are
confidential working data and are intentionally excluded from Git.

## Current scope

| Week | Script | Output location |
| --- | --- | --- |
| 1 | `week1_aggregation.py` | `outputs/week1/` plus combined Residential CSVs |
| 2 | `dataset_validation.py` | `outputs/week2/` |
| 2–3 | `week2_3_mortgage_rates.py` | `outputs/week2_3/` |
| 4–5 | `data_cleaning.py` | `outputs/week4_5/` |
| 6 | `week6_feature_engineering.py` | `outputs/week6/` |

The current monthly source range is January 2024 through June 2026. Week 1
discovers the latest available month automatically and requires continuous
monthly coverage beginning in January 2024.

## Requirements

- Python 3.11 or newer
- pandas
- matplotlib
- Internet access during the Weeks 2–3 mortgage-rate step so the script can
  download the `MORTGAGE30US` series from FRED

Install the Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Input files

Place the monthly CSV files in the repository root using these names:

```text
CRMLSListingYYYYMM.csv
CRMLSSoldYYYYMM.csv
```

When both versions exist for a Sold month, Week 1 uses the `_filled` version
instead of the raw version. It selects only one file per month, preventing
duplicate transactions.

Do not commit monthly data, combined data, generated outputs, backups, or the
internship handbook. The project `.gitignore` blocks these files.

## Run the pipeline

Run the scripts from the repository root in this order:

```bash
python3 week1_aggregation.py
python3 dataset_validation.py
python3 week2_3_mortgage_rates.py
python3 data_cleaning.py
python3 week6_feature_engineering.py
```

Each stage validates its required inputs before processing. The large datasets
are not committed; rerunning the scripts recreates them locally.

## Workflow details

### Week 1 — Monthly aggregation

- Verifies continuous month coverage from January 2024 through the latest file
- Uses one Sold and one Listing source per month
- Adds source-month and source-file traceability columns
- Reconciles row counts before and after concatenation
- Filters both datasets to `PropertyType == "Residential"`

### Weeks 2–3 — Validation and mortgage enrichment

- Produces missing-value reports and flags columns above 90% missing
- Creates percentile, histogram, boxplot, and IQR outlier summaries
- Downloads the FRED `MORTGAGE30US` weekly series
- Calculates monthly average mortgage rates
- Merges rates using `CloseDate` for Sold and `ListingContractDate` for Listings
- Fails validation if an MLS month has no matching mortgage rate

### Weeks 4–5 — Cleaning

- Converts required date and numeric columns
- Flags invalid prices, living areas, days on market, bedroom, and bathroom data
- Checks transaction date ordering
- Flags missing, zero, positive-longitude, implausible, and out-of-state coordinates
- Saves cleaned datasets plus before/after and quality summaries

### Week 6 — Feature engineering

- Creates price ratio and close-to-original-list ratio
- Calculates price per square foot
- Derives Year, Month, and YrMo from CloseDate
- Calculates listing-to-contract and contract-to-close intervals
- Produces metric-quality and county-level summary files

School-district spatial mapping is intentionally outside this Data Analyst
repository because it belongs to the separate AI Agent project.

## Data safety

Before publishing, verify that Git is not tracking data files:

```bash
git ls-files '*.csv' '*.CSV' '*.geojson'
```

The command should return no output.
