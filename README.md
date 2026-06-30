# IDX Exchange — Data Analyst Internship

This repository contains my project work for the **IDX Exchange Data Analyst Internship**, a 12-week MLS Analytics & Tableau Dashboard program. The internship is structured as a progressive data pipeline: each phase builds on the previous one, taking raw MLS transaction data all the way through cleaning, feature engineering, dashboarding, and final market insights.

**Tools:** Python (Pandas), Tableau Desktop
**Data source:** CoreLogic Trestle API, delivered as monthly MLS Listing & Sold CSV files via the IDX Exchange pipeline
**Scope:** Residential MLS transactions, January 2024 → most recently completed calendar month

---

## Program Overview (Weeks 0–12)

| Phase | Week(s) | Focus | What happens |
|-------|---------|-------|--------------|
| Orientation | **Week 0** | MLS Data Pipeline | Understand how monthly datasets are produced from the Trestle API and exported to CSV; retrieve pre-generated files via FTP |
| Data Cleaning | **Week 1** | Monthly Dataset Aggregation | Concatenate all monthly files (Jan 2024 → latest) into combined Sold & Listing datasets; filter to Residential |
| Data Cleaning | **Weeks 2–3** | Structuring & Validation + Mortgage Enrichment | EDA, missing-value analysis, numeric distributions; merge in the FRED 30-yr fixed mortgage rate on a year-month key |
| Data Cleaning | **Weeks 4–5** | Cleaning & Preparation | Convert date fields, type numerics, handle missing values, add date-consistency and geographic quality flags |
| Market Analytics | **Week 6** | Feature Engineering & Market Metrics | Build price ratio, PPSF, days-on-market, YrMo, listing-to-contract / contract-to-close days; add school districts; segment analysis |
| Market Analytics | **Week 7** | Outlier Detection & Data Quality | Apply IQR filtering to key numeric fields; flag rather than delete; produce flagged + clean datasets |
| Dashboard Dev | **Weeks 8–10** | Tableau Dashboards | Build `market_analysis.twbx` and `competitive_analysis.twbx` with filterable monthly dashboards |
| Market Insights | **Weeks 11–12** | Final Presentation & Report | Publish dashboards to Tableau Public, write a 1-page market intelligence report, deliver a 5-min presentation |

**Final deliverable:** Tableau dashboards + 1-page Market Intelligence Report + presentation.

---

## Week 1 — Monthly Dataset Aggregation

### Objective
Load and concatenate every monthly MLS file from **January 2024 through the most recently completed calendar month** into two analysis-ready combined datasets (Sold and Listings), filter both to **Residential** properties only, and save the results as new CSVs. This enables trend analysis across multiple months instead of working with one file at a time.

### Files in this repo
| File | Purpose |
|------|---------|
| `week1_sold.py` | Combines and filters the monthly **Sold** files (`CRMLSSoldYYYYMM.csv`) |
| `week1_listings.py` | Combines and filters the monthly **Listing** files (`CRMLSListingYYYYMM.csv`) |

### What each script does
1. **Discover** every monthly CSV in the folder with `Path().glob()` (`CRMLSListing20*.csv` / `CRMLSSold20*.csv`), excluding `_filled` working copies so only the raw monthly files are combined.
2. **Read** each file and **concatenate** them into a single DataFrame with `pd.concat(..., ignore_index=True)`.
3. **Record row counts** before and after concatenation, and before and after the Residential filter.
4. **Filter** to `PropertyType == 'Residential'`.
5. **Save** the combined Residential dataset to a new CSV.


### Outputs
- `combined_sold_202401_202604_residential.csv` — combined, Residential-filtered Sold dataset
- `combined_listing_202401_202604_residential.csv` — combined, Residential-filtered Listing dataset

### Notes
- Row counts are confirmed at each stage — **before/after concatenation** and **before/after the Residential filter** — per the Week 1 deliverable requirements.
- Monthly counts may differ slightly from a teammate's depending on when the data was pulled from the pipeline.
- The MLS datasets are confidential and for program use only, and are not committed to this repository.

---

## Skills Demonstrated (Week 1)
- Multi-file dataset management
- Data aggregation with Pandas (`pd.concat`)
- Property-type filtering
- Preparing time-series datasets for downstream analysis

