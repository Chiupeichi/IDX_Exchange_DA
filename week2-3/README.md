# Week 2–3: Dataset Structuring, Validation, and Mortgage Rate Enrichment

## Overview

This project focuses on preparing MLS real estate datasets for downstream analytics. The workflow includes dataset validation, exploratory data analysis (EDA), and enrichment with external economic data from the Federal Reserve Economic Data (FRED).

The goal is to ensure data quality before analysis while integrating monthly 30-year fixed mortgage rates into both sold and listing datasets.

---

## Repository Structure

```
week2_3/
│
├── week2_3.ipynb
│      Notebook version of the entire workflow
│
├── mortgage_rate_enrichment.py
│      Python script for downloading mortgage rates,
│      creating monthly averages, merging with MLS data,
│      validating results, and exporting enriched datasets.
│
├── outputs/
│
│   ├── week2/
│   │
│   │   ├── sold_missing_summary.csv
│   │   ├── listings_missing_summary.csv
│   │   ├── numeric_summary.csv
│   │   └── outlier_summary.csv
│   │
│   └── week2_3/
│
│       ├── mortgage_rate_monthly.csv
│       ├── sold_with_mortgage_rates.csv
│       └── listings_with_mortgage_rates.csv
│
└── README.md
```

---

# Part 1 — Dataset Validation & Exploratory Data Analysis

### Objectives

- Understand the structure of MLS datasets
- Evaluate missing values
- Review distributions of important numeric variables
- Identify potential outliers
- Prepare datasets for downstream analysis

---

## Tasks Completed

### Dataset Understanding

- Loaded combined MLS sold and listing datasets
- Reviewed dataset dimensions
- Examined column names and data types

### Missing Value Analysis

- Calculated missing counts
- Calculated missing percentages
- Identified columns with high missing rates

### Numeric Distribution Review

Summary statistics generated for:

- ClosePrice
- ListPrice
- OriginalListPrice
- LivingArea
- LotSizeAcres
- BedroomsTotal
- BathroomsTotalInteger
- DaysOnMarket
- YearBuilt

Additional analyses:

- Histograms
- Boxplots
- Percentiles
- IQR-based outlier detection

---

## Outputs

| File | Description |
|------|-------------|
| sold_missing_summary.csv | Missing-value summary for sold dataset |
| listings_missing_summary.csv | Missing-value summary for listings dataset |
| numeric_summary.csv | Descriptive statistics for key numeric variables |
| outlier_summary.csv | IQR-based outlier counts and percentages |

---

# Part 2 — Mortgage Rate Enrichment

### Objective

Integrate monthly 30-year fixed mortgage rates from the Federal Reserve (FRED) into both MLS datasets.

---

## Workflow

### 1. Download Mortgage Rates

Downloaded the **MORTGAGE30US** series directly from FRED.

Source:

https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US

---

### 2. Resample Weekly Data

Converted weekly mortgage rates into monthly averages by:

- parsing dates
- creating a year-month key
- calculating monthly mean mortgage rates

---

### 3. Create Merge Keys

Created a common `year_month` key:

**Sold dataset**

```
CloseDate → year_month
```

**Listings dataset**

```
ListingContractDate → year_month
```

---

### 4. Merge Mortgage Rates

Merged monthly mortgage rates onto:

- Sold dataset
- Listings dataset

using

```
year_month
```

as the join key.

---

### 5. Validation

Validated that

- every MLS record successfully received a mortgage rate
- merge did not change dataset row counts

Validation results:

- Missing sold mortgage rates: **0**
- Missing listing mortgage rates: **0**

---

## Outputs

| File | Description |
|------|-------------|
| mortgage_rate_monthly.csv | Monthly average mortgage rates downloaded from FRED |
| sold_with_mortgage_rates.csv | Sold dataset enriched with mortgage rates |
| listings_with_mortgage_rates.csv | Listings dataset enriched with mortgage rates |

---

# Skills Learned

- Data validation
- Exploratory Data Analysis (EDA)
- Missing-value analysis
- Numeric distribution analysis
- Outlier detection
- Working with public APIs
- Time-series resampling
- Datetime feature engineering
- Dataset merging
- Merge validation
- Exporting processed datasets

---

# Technologies

- Python
- pandas
- NumPy
- Jupyter Notebook
- FRED API (CSV endpoint)

---
