# census-ftd-explorer-public
Public version of Census Foreign Trade Data API explorer
This script is designed to be used with the Census Foreign Trade Data API
provided by the US Census Bureau. Census allows up to 500 calls per day 
without a key, but the key is free with registration.
More documentations is found at 
https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf

Other endpoints and datasets are available but this version is purely 
focused on getting monthly export statistics, including:
1. port of export
2. HS commodity at the 6 digit level
3. country of destination

Calls in the script are broken into loops as large calls seem to cause
difficulties with the API. Rough order of operations is:
1. Set API call components as variables, including year and month
2. Set data to return as variable 'cols'
3. Create dict for HS chapters with simplified API call
4. Start a loop on 'year' value
5. Generate dict for ports with simplified API call; this happens within the year loop because ports sometimes change from year to year
6. Start loops for port, HS chapter, and month to grab all export data by port, year, month, and HS chapter
7. Pass successful responses to a dataframe, pass zeroes for any 204 responses into the dataframe
8. Push the dataframe into a CSV for easy ingestion in Excel or Tableau

