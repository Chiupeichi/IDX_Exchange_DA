# Week 1 — Monthly Dataset Aggregation

## Objective

Combine all monthly Sold and Listing files from January 2024 through the latest
available month, reconcile row counts, and retain Residential properties only.

## Script

[`aggregation.py`](aggregation.py)

The script:

1. Discovers monthly source files and checks for missing months.
2. Selects exactly one file for each dataset and month.
3. Prefers a Sold `_filled` file when one is available.
4. Adds `SourceMonth` and `SourceFile` for local traceability.
5. Reconciles row counts before and after concatenation.
6. Filters to `PropertyType == "Residential"`.
7. Saves combined datasets locally; CSV files are ignored by Git.

## Latest verified results

| Dataset | Months | Rows before filter | Residential rows | Residential share |
| --- | ---: | ---: | ---: | ---: |
| Sold | 30 | 648,542 | 435,792 | 67.20% |
| Listings | 30 | 862,237 | 547,930 | 63.55% |

Coverage: **January 2024 through June 2026**. Row counts before and after
concatenation matched exactly for both datasets.

## Run

```bash
python3 week1/aggregation.py
```

Local summary outputs are written to `outputs/week1/`.
