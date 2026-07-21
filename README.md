# IDX Exchange — Data Analyst Internship

Python workflows for the IDX Exchange MLS Analytics Program. The project
combines monthly CRMLS files, validates and enriches Residential records,
cleans invalid observations, and creates market metrics for analysis.

The public repository contains code, documentation, and aggregate charts only.
Raw and generated MLS CSV files are confidential working data and are excluded
from Git.

## Repository structure

| Week | Folder | Main work |
| --- | --- | --- |
| Week 1 | [`week1/`](week1/) | Monthly aggregation and Residential filtering |
| Weeks 2–3 | [`week2-3/`](week2-3/) | EDA, validation, distributions, and FRED mortgage rates |
| Weeks 4–5 | [`week4-5/`](week4-5/) | Data cleaning and quality flags |
| Week 6 | [`week6/`](week6/) | Market metrics and segmented summaries |

Each folder contains its own Python script(s), README, key results, and selected
aggregate charts where a visual is useful.

## Requirements

- Python 3.11 or newer
- pandas
- matplotlib
- Internet access during the FRED mortgage-rate step

```bash
python3 -m pip install -r requirements.txt
```

## Input files

Place monthly source files in the repository root:

```text
CRMLSListingYYYYMM.csv
CRMLSSoldYYYYMM.csv
```

When both versions exist for a Sold month, Week 1 selects the `_filled` version
instead of the raw version. Only one file is used per dataset and month.

## Run the pipeline

Run from the repository root:

```bash
python3 week1/aggregation.py
python3 week2-3/dataset_validation.py
python3 week2-3/mortgage_rate_enrichment.py
python3 week4-5/data_cleaning.py
python3 week6/feature_engineering.py
```

The current local analysis covers January 2024 through June 2026. Week 1
discovers the latest month automatically and verifies continuous monthly
coverage from January 2024.

## Data safety

The `.gitignore` blocks CSV files, generated outputs, local backups, notebooks,
GeoJSON, and the internship handbook. README charts contain aggregate results
only—never addresses, listing identifiers, coordinates, or row-level MLS data.

Before publishing, this command should return no output:

```bash
git ls-files '*.csv' '*.CSV' '*.geojson' '*.ipynb'
```

School-district spatial mapping is intentionally excluded because it belongs to
the separate AI Agent project.
