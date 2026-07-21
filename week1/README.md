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
4. Audits pandas `.1` duplicate columns before removing them. Formatting-only
   numeric differences are treated as equivalent; duplicate-only values are
   recovered, and non-null conflicts keep the first canonical value and are
   recorded for review.
5. Adds `SourceMonth` and `SourceFile` for local traceability.
6. Reconciles row counts before and after concatenation.
7. Filters to `PropertyType == "Residential"`.
8. Saves combined datasets locally; CSV files are ignored by Git.

## Latest verified results

| Dataset | Months | Rows before filter | Residential rows | Residential share |
| --- | ---: | ---: | ---: | ---: |
| Sold | 30 | 648,542 | 435,792 | 67.20% |
| Listings | 30 | 862,237 | 547,930 | 63.55% |

Coverage: **January 2024 through June 2026**. Row counts before and after
concatenation matched exactly for both datasets.

## Duplicate-column audit

The Sold files contained no pandas `.1` column pairs. All 30 Listing files
contained the same 11 duplicate-header pairs, covering 862,237 source rows.
Week 1 now compares every pair before deleting the `.1` copy.

- All `.1` columns are absent from the combined Listing output.
- One non-null `BuyerOfficeName` conflict was found; the first canonical value
  was retained and the conflict was logged.
- Ten canonical-only cells across two source records had a blank `.1` copy, so
  removing those copies did not discard information.
- No case required recovering a value from `.1` into a blank canonical column.

The local audit is written to
`outputs/week1/duplicate_column_audit.csv`. It contains counts and source-file
references only and remains excluded from Git with the other generated CSVs.

## Run

```bash
python3 week1/aggregation.py
```

Local summary outputs are written to `outputs/week1/`.
