# Trestle and RESO Field Notes - california_sold

The california_sold table contains historical California sold and closed transactions. The key identifier is ListingKey. Core transaction fields include ClosePrice, CloseDate, OriginalListPrice, ListPrice, DaysOnMarket, ListingContractDate, and PurchaseContractDate.

Property fields include PropertyType, PropertySubType, LivingArea, LotSizeAcres, LotSizeSquareFeet, BedroomsTotal, BathroomsTotalInteger, YearBuilt, GarageSpaces, PoolPrivateYN, ViewYN, FireplaceYN, NewConstructionYN, AssociationFee, SubdivisionName, and HighSchoolDistrict.

Geographic fields include City, PostalCode, Latitude, Longitude, and UnparsedAddress. Agent and office fields include ListAgentFirstName, ListAgentLastName, ListAgentFullName, BuyerAgentFirstName, BuyerAgentLastName, ListOfficeName, and BuyerOfficeName.

ListingKey can be correlated with the active-listing table's L_ListingID after controlled type conversion. For market-level analysis, city and postal code can also be used, but they are not unique record identifiers.

Most california_sold names follow RESO-style conventions. The active rets_property table also contains legacy IDX fields such as L_SystemPrice, L_Keyword2, LM_Dec_3, LM_Int2_3, L_City, and L_Address; those names require the internal schema annotation rather than an assumed RESO mapping.
