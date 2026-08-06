# Week 8 Tableau Data Dictionary

## Market events data source

Use `outputs/week8/tableau_market_events.csv` for the Market Analysis
workbook.

| Field | Tableau role | Description |
| --- | --- | --- |
| EventId | Dimension | Stable event identity used to prevent exact duplicate counts |
| EventType | Dimension | `New Listing` or `Closed Sale` |
| EventDate | Date | ListingContractDate for new listings; CloseDate for closed sales |
| Year / Month / YrMo | Date dimensions | Calendar fields derived from EventDate |
| City | Geographic dimension | City filter; assign Tableau geographic role City |
| CountyOrParish | Geographic dimension | County filter; assign geographic role County |
| PostalCode | Geographic dimension | ZIP filter and map field; keep as text and assign ZIP Code role |
| PropertySubType | Dimension | Property subtype filter |
| ClosePrice | Measure | Populated for closed-sale events only |
| DaysOnMarket | Measure | Populated for closed-sale events only |
| CloseToOriginalListRatio | Measure | ClosePrice divided by OriginalListPrice for closed sales |
| CloseToOriginalListRatioOutlierFlag | Dimension | True when the ratio falls outside its Week 8 IQR bounds |
| CloseToOriginalListRatioEligible | Dimension | True when the ratio can be used in an average |
| NewListings | Measure | 1 for a new-listing event, otherwise 0 |
| ClosedSales | Measure | 1 for a closed-sale event, otherwise 0 |
| RecordCount | Measure | Always 1; general event-row count |

## Competitive sales data source

Use `outputs/week8/tableau_competitive_sales.csv` for the Competitive Analysis
workbook in Weeks 9–10.

| Field | Tableau role | Description |
| --- | --- | --- |
| ListAgentFullName | Dimension | Listing-agent name for top-agent rankings |
| ListOfficeName | Dimension | Listing office for top-office rankings |
| SalesVolume | Measure | ClosePrice; aggregate with SUM |
| UnitsSold | Measure | Always 1; aggregate with SUM |
| City / CountyOrParish / PostalCode | Geographic dimensions | Required competitive filters and maps |
| PropertySubType | Dimension | Required property subtype filter |
| ClosePrice | Measure | Sold price for median-price maps |
| YrMo | Date dimension | Monthly filter derived from CloseDate |

## Recommended formatting

- Format `ClosePrice`, `ListPrice`, `OriginalListPrice`, `PricePerSqFt`, and
  `SalesVolume` as currency.
- Format `CloseToOriginalListRatio` as a percentage with one decimal place.
- Use only the cleaned `CloseToOriginalListRatio`; outlier values are converted
  to null for this measure without removing their closed-sale records.
- Treat `PostalCode` as text so leading zeros are preserved.
- Use `EventDate` as a continuous month on the dashboard timeline.
