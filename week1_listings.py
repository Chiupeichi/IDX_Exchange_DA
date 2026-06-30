import pandas as pd
from pathlib import Path

folder = Path(".")

# 找所有 Listing CSV
listing_files = sorted(folder.glob("CRMLSListing20*.csv"))

# 合併
listing = pd.concat(
    [pd.read_csv(file) for file in listing_files],
    ignore_index=True
)

# 印出 filter 前筆數
print("Listing rows before filter:", len(listing))

# Residential filter
listing = listing[listing["PropertyType"] == "Residential"]

# 印出 filter 後筆數
print("Listing rows after filter:", len(listing))

# 輸出 CSV
listing.to_csv(
    "combined_listing_202401_202604_residential.csv",
    index=False
)
