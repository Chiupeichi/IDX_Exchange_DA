# Week 8 — Tableau Data Preparation and Market Dashboard Setup

## Objective

Prepare compact, validated Tableau data sources from the clean Week 7 sold
records and the clean Weeks 4–5 listing records. Week 8 establishes the Market
Analysis workbook foundation; the final two Tableau workbooks are due at the
end of the combined Weeks 8–10 phase.

## Script

[`tableau_data_prep.py`](tableau_data_prep.py) prepares and validates the two
Tableau datasets. [`build_market_analysis_workbook.py`](build_market_analysis_workbook.py)
then converts the market events into a Tableau Hyper extract and creates the
packaged Market Analysis workbook. [`build_competitive_analysis_workbook.py`](build_competitive_analysis_workbook.py)
converts the competitive sales dataset into the second packaged workbook.

The script creates:

- a long-format market event table that supports new listings, closed sales,
  median close price, average days on market, and average close-to-original-list
  ratio;
- a competitive sales table with agent, office, sales volume, unit, and
  geographic fields for Weeks 9–10;
- monthly validation summaries and local top-100 agent and office checks;
- an audit summary reconciling input rows, output events, exact duplicates, and
  calendar coverage.

The close-to-original-list ratio receives a metric-specific IQR eligibility
check before Tableau aggregation. Ratio outliers are converted to null only for
that measure; their sale rows remain available for closed-sales counts and all
other eligible metrics.

## Latest verified results

Coverage: **January 2024 through June 2026 (30 months)**

| Dataset / check | Rows |
| --- | ---: |
| Week 7 clean sold input | 366,890 |
| Exact duplicate sold events removed | 34 |
| Closed-sale events | 366,856 |
| New-listing events | 547,263 |
| Combined market events | 914,119 |
| Competitive sales rows | 366,856 |

The market and competitive outputs contain zero duplicate `EventId` values.
The five required market measures reconcile to 547,263 new listings and
366,856 closed sales.

For `CloseToOriginalListRatio`, the Week 8 IQR eligibility range is
**0.8758–1.1111**. The script retains all sale rows but excludes 34,302 ratio
outliers from that measure's averages; 332,131 ratios remain eligible. Monthly
eligible-ratio averages range from 98.38% to 100.96%, replacing the distorted
results produced by the raw extreme ratios.

![Monthly residential market activity](assets/monthly-market-activity.png)

### Source completeness caution

The monthly validation step flags months with event counts below 50% of the
30-month median. The latest source files contain unusually low new-listing
volume for January, May, and June 2026, and unusually low closed-sales volume
for May 2026. These months are retained without imputation; Tableau viewers
should treat them as potentially incomplete source periods rather than market
collapses.

## Generated outputs

- `tableau_market_events.csv` — Market Analysis Tableau source;
- `tableau_competitive_sales.csv` — Competitive Analysis Tableau source;
- `market_analysis.hyper` — local Tableau extract with 914,119 market events;
- `outputs/week8/market_analysis.twbx` — local build of the Market Analysis
  workbook;
- `week8/market_analysis.twbx` — publishable, Git-tracked deliverable with
  direct listing identifiers removed;
- `outputs/week8/competitive_analysis.twbx` — local build of the Competitive
  Analysis workbook;
- `week8/competitive_analysis.twbx` — publishable, Git-tracked competitive
  deliverable with 366,856 closed-sale rows and direct identifiers removed;
- `market_monthly_summary.csv` — validation of all five market measures;
- `top_100_listing_agents.csv` and `top_100_listing_offices.csv` — local
  ranking checks;
- `tableau_data_quality_summary.csv` — row, duplicate, metric, and coverage
  audit.

## Market Analysis workbook

Run the workbook builder, then open
`outputs/week8/market_analysis.twbx` in Tableau Public. The packaged workbook
uses a local Hyper extract, so it meets Tableau Public's extract requirement
without reconnecting to the source CSV.

The workbook contains the following worksheets with continuous
MONTH(`EventDate`) on Columns:

| Worksheet | Rows / Marks | Required filter |
| --- | --- | --- |
| Monthly Median Close Price | MEDIAN(`ClosePrice`) | EventType = Closed Sale |
| Average Days on Market | AVG(`DaysOnMarket`) | EventType = Closed Sale |
| Average Close-to-Original-List Ratio | AVG(`CloseToOriginalListRatio`) | EventType = Closed Sale |
| New Listings | SUM(`NewListings`) | None |
| Closed Sales | SUM(`ClosedSales`) | None |

Each required worksheet has its own dashboard with `City`, `CountyOrParish`,
`PostalCode`, and `PropertySubType` dropdown filters. The workbook contains:

1. `Close Price Dashboard`;
2. `Days on Market Dashboard`;
3. `List-to-Sale Ratio Dashboard`;
4. `New Listings Dashboard`;
5. `Closed Sales Dashboard`; and
6. `Market Overview`, the custom dashboard combining all five measures.

The three geographic fields have their matching Tableau geographic roles.

The publishable workbook was validated in Tableau Public 2026.1: the workbook
DOM, packaged Hyper connection, dashboard query batches, and all five worksheet
computations completed successfully.

See [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for field roles and formatting.

## Competitive Analysis workbook

Run `build_competitive_analysis_workbook.py --publish-copy`, then open
`week8/competitive_analysis.twbx` in Tableau Public. The packaged Hyper extract
covers January 2024 through June 2026 and contains 366,856 cleaned closed-sale
rows.

The workbook contains six worksheets:

| Worksheet | Calculation |
| --- | --- |
| Top 100 Listing Agents - Sales Volume | Dynamic Top 100 by SUM(`SalesVolume`) |
| Top 100 Listing Agents - Units Sold | Dynamic Top 100 by SUM(`UnitsSold`) |
| Top 100 Listing Offices - Sales Volume | Dynamic Top 100 by SUM(`SalesVolume`) |
| Top 100 Listing Offices - Units Sold | Dynamic Top 100 by SUM(`UnitsSold`) |
| ZIP Median Close Price Map | MEDIAN(`ClosePrice`) by ZIP code |
| ZIP Homes Sold Map | SUM(`UnitsSold`) by ZIP code |

Those sheets are organized into four required dashboards—`Top 100 Listing
Agents`, `Top 100 Listing Offices`, `ZIP Median Close Price`, and `ZIP Homes
Sold`—plus the custom `Competitive Overview`. Every dashboard provides shared
dropdown controls for `YrMo`, `City`, `CountyOrParish`, `PostalCode`, and
`PropertySubType`.

The competitive workbook was validated in Tableau Public 2026.1: the workbook
DOM loaded successfully, the packaged Hyper connection opened, all dashboard
query batches completed, and the ZIP maps connected to Tableau geocoding.

## Data safety

The source CSV and local working extracts remain under `outputs/week8/`, which
is excluded from Git. The tracked `week8/market_analysis.twbx` uses a dedicated
publishable Hyper extract that omits the direct identifiers `EventId` and
`ListingKey`; it retains the pattern-level month, geography, property type, and
market measures required for the assignment.

The tracked `week8/competitive_analysis.twbx` follows the same policy: it
contains aggregate-ready competitive fields but excludes `EventId` and
`ListingKey`.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 week8/tableau_data_prep.py
python3 week8/build_market_analysis_workbook.py --publish-copy
python3 week8/build_competitive_analysis_workbook.py --publish-copy
```
