# Field Usage Notes

## `rets_property`

| Purpose | Fields | Safety / validation |
| --- | --- | --- |
| Identity | `L_ListingID`, `L_DisplayId` | Return only identifiers needed for a result card; never bulk export |
| Search | `L_City`, `L_Zip`, `L_Class`, `L_Type_`, `L_SystemPrice`, `L_Keyword2`, `LM_Dec_3`, `LM_Int2_3` | Parameterize all SQL values and limit results to 50 |
| Display | `L_Address`, `DaysOnMarket`, `PhotoCount` | WhatsApp displays no more than five cards |
| Recommendations | `L_Remarks`, property attributes, coordinates | Embeddings should exclude contact details and credentials |
| Agent / office | `LA1_UserFirstName`, `LA1_UserLastName`, `LO1_OrganizationName` | Do not include email or direct phone in public logs |

## `california_sold`

| Purpose | Fields | Safety / validation |
| --- | --- | --- |
| Market price | `ClosePrice`, `CloseDate`, `City`, `PostalCode`, `PropertyType` | Use Residential filters and aggregate before presentation |
| Market speed | `DaysOnMarket` | Apply consistent null and validity rules |
| Ratio | `ClosePrice`, `OriginalListPrice` | Require positive values and exclude metric-specific outliers |
| Comps | `ListingKey`, location, type, beds, baths, living area, close date | Never expose row-level bulk datasets |
| Offices / agents | `ListAgentFullName`, `ListOfficeName` | Use only for approved analysis; avoid contact information |

## Join guidance

The preferred record-level key is `california_sold.ListingKey` matched to a validated numeric conversion of `rets_property.L_ListingID`. City and postal code support market-level grouping but are not unique keys and must not be treated as record-level matches.
