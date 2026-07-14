# Weeks 4–5: Data Cleaning and Preparation

## Overview

This phase focuses on transforming raw CRMLS listing and transaction data into analysis-ready datasets. The workflow includes data type conversion, data validation, quality checks, and generation of cleaned datasets for downstream analytics.

---

## Tasks

- Convert date columns to `datetime`
- Convert numeric fields to appropriate numeric types
- Validate required columns
- Identify missing values
- Flag invalid numeric values
- Perform transaction date consistency checks
- Perform geographic data quality checks
- Export cleaned datasets and validation summaries

---

## Files

### Notebook

```
week4-5.ipynb
```

Main notebook containing the complete data cleaning workflow.

---

### Outputs

```
outputs/
├── sold_clean.csv
├── listings_clean.csv
├── cleaning_summary.csv
├── date_conversion_summary.csv
├── numeric_conversion_summary.csv
├── numeric_invalid_flag_summary.csv
├── date_consistency_summary.csv
└── geographic_data_quality_summary.csv
```

---

## Data Cleaning Workflow

### 1. Required Column Validation

- Verified all required columns exist
- Checked Sold and Listings datasets separately

Output:

```
Missing sold columns:
[]

Missing listings columns:
[]
```

---

### 2. Date Conversion

Converted:

- CloseDate
- PurchaseContractDate
- ListingContractDate
- ContractStatusChangeDate

Output:

- date_conversion_summary.csv

---

### 3. Numeric Type Conversion

Converted price, property, and coordinate fields into numeric types using

```python
pd.to_numeric(errors="coerce")
```

Output:

- numeric_conversion_summary.csv

---

### 4. Numeric Validation

Created quality flags for:

- Invalid ClosePrice/ListPrice
- Invalid LivingArea
- Negative DaysOnMarket
- Negative Bedrooms
- Negative Bathrooms

Output:

- numeric_invalid_flag_summary.csv

---

### 5. Date Consistency Checks

Created flags for:

- listing_after_close_flag
- purchase_after_close_flag
- negative_timeline_flag

Output:

- date_consistency_summary.csv

---

### 6. Geographic Data Quality Checks

Flagged records with:

- Missing coordinates
- Zero coordinates
- Positive longitude values
- Invalid latitude range
- Invalid longitude range
- Out-of-California coordinates

Output:

- geographic_data_quality_summary.csv

---

### 7. Create Clean Dataset

Removed records containing invalid:

- Price
- Living area
- Days on market
- Timeline
- Geographic coordinates

Output:

- sold_clean.csv
- listings_clean.csv

Cleaning summary:

| Dataset | Before | Removed | After |
|---------|--------:|--------:|------:|
| Sold | 519,932 | 1,333 | 518,599 |
| Listings | 860,898 | 1,394 | 859,504 |

---

## Skills Learned

- Data validation
- Data cleaning
- Feature quality assessment
- Datetime processing
- Geographic data validation
- Building analysis-ready datasets using Pandas
