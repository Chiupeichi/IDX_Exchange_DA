# IDX_Exchange
# IDX Exchange – Week 1: Monthly Dataset Aggregation

This repository contains my Week 1 submission for the IDX Exchange Data Analyst Internship.

## Objective

The goal of Week 1 is to combine all monthly CRMLS Listing and Sold datasets from **January 2024 through the latest completed month**, prepare unified datasets for analysis, and keep only **Residential** properties.

---


---

## What the scripts do

### Listings

The listings script:

- Reads every monthly Listing CSV.
- Combines all monthly datasets into one dataframe.
- Reports the total number of rows before filtering.
- Filters records where:

```
PropertyType == "Residential"
```

- Reports the remaining row count.
- Saves the combined Residential listing dataset as a CSV.

---

### Sold Transactions

The sold script:

- Reads one Sold CSV for each month.
- Ignores duplicate `_filled.csv` files.
- Combines all monthly datasets.
- Reports the total number of rows before filtering.
- Filters records where:

```
PropertyType == "Residential"
```

- Reports the remaining row count.
- Saves the combined Residential sold dataset as a CSV.

---

## Week 1 Deliverables Completed

- Combined all monthly Listing files.
- Combined all monthly Sold files.
- Included data from January 2024 through the latest completed month.
- Filtered both datasets to Residential properties only.
- Printed row counts before and after filtering.
- Exported two combined Residential CSV files.

---

## Output Files

```
combined_listing_202401_202604_residential.csv
combined_sold_202401_202604_residential.csv
```

---

## Notes

The original MLS data files are confidential and are **not included** in this repository.

Only the Python scripts and documentation are uploaded to GitHub.
