# Weeks 11–12 — Final Market Intelligence Package

This folder contains the Irvine, Orange County market analysis built from the
cleaned Residential Tableau datasets.

## Deliverables

- [`irvine_market_metrics.json`](irvine_market_metrics.json) — aggregate values
  used by the Irvine market analysis.
- [`market_intelligence_analysis.py`](market_intelligence_analysis.py) — creates
  the aggregate metrics from the Week 8–10 Tableau-ready data.
- [`build_market_intelligence_report.py`](build_market_intelligence_report.py) —
  renders the one-page PDF from the metrics file.

The final Tableau workbooks remain in [`../week8-10/`](../week8-10/):

- `market_analysis.twbx`
- `competitive_analysis.twbx`

Published Tableau Public views:

- [Market Analysis](https://public.tableau.com/app/profile/pei.chi.chiu/viz/market_analysis_17870896129430/MarketOverview)
- [Competitive Analysis](https://public.tableau.com/app/profile/pei.chi.chiu/viz/competitive_analysis_17870897718410/CompetitiveOverview)

## Analysis scope

- Geography: Irvine, Orange County, California
- Property scope: cleaned Residential records after Week 7 IQR filtering
- Full sold-data coverage: January 2024 through June 2026
- Latest complete activity month: April 2026
- Competitive period: trailing 12 months from May 2025 through April 2026

April 2026 is used for the final month-to-month market comparison because May
and June 2026 do not contain complete new-listing coverage. Closed-sale data
continues through June 2026.

## Main findings

- April 2026 median close price: **$1.36M**, down **4.2%** year over year.
- Average days on market: **24.8 days**, up **4.4 days** year over year.
- Median price per square foot: **$768**, down **5.5%** year over year.
- Average close-to-original-list ratio: **98.2%**.
- April new listings: **330**, up **8.2%** year over year.
- April closed sales: **131**, up **11.0%** year over year.
- Trailing 12-month sales volume: **$2.1B**, down **5.7%** from the prior period.
- The leading listing office represented only **7.2%** of Irvine sales volume,
  indicating a fragmented competitive market.

## Rebuild the analysis and report

Run from the repository root after the Week 8–10 output CSV files are present:

```bash
python3 week11-12/market_intelligence_analysis.py
python3 week11-12/build_market_intelligence_report.py
```

The source MLS CSV files and row-level Tableau preparation outputs are excluded
from Git because they contain confidential working data.

## Tableau Public submission checklist

1. Publish both workbooks from Tableau Public Desktop.
2. Select **Show Sheets** during publishing so every dashboard tab is visible.
3. Confirm the dashboard size is Desktop / 1400 × 900.
4. Open each published workbook and test all city, county, ZIP code,
   PropertySubType, and month filters.
5. Submit both Tableau Public URLs.
