# main public
# This script is designed to be used with the Census Foreign Trade Data API
# provided by the US Census Bureau. Census allows up to 500 calls per day 
# without a key, but the key is free with registration.
# More documentations is found at 
# https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf

import json
import time
from datetime import datetime
import requests
import pandas as pd

# Creating a DataFrame with the specified columns
#this one works for some reason
cols = "PORT_NAME,CTY_NAME,CTY_CODE,E_COMMODITY_LDESC,E_COMMODITY_SDESC,ALL_VAL_MO,VES_VAL_MO,CNT_VAL_MO,AIR_VAL_MO,VES_WGT_MO,CNT_WGT_MO,AIR_WGT_MO,LAST_UPDATE"
#2024-05-17 testing add to cols, this didn't work for me
#cols = "PORT_NAME,CTY_NAME,CTY_CODE,E_COMMODITY_LDESC,E_COMMODITY_SDESC,ALL_VAL_MO,VES_VAL_MO,CNT_VAL_MO,AIR_VAL_MO,VES_WGT_MO,CNT_WGT_MO,AIR_WGT_MO,YEAR,MONTH,PORT,E_COMMODITY"

columns = cols.split(",")
df = pd.DataFrame(columns=columns)

# Get a timestamp to unique-ify CSV output
current_datetime = datetime.now()
grabdatetime = current_datetime.strftime("%Y-%m-%d_%H%M%S")
print(grabdatetime)

# Set variables for main URL
base_url = "https://api.census.gov/data/timeseries/intltrade/"
dimex = "exports"
dataset = "porths"
summarylevel = "DET"
summaryleveltwo = "HSPTCY"
commagglevel = "HS6"

# Set variable for the CSV filename
csv_filename = f"CensusFTD_{dimex}_{dataset}_{summarylevel}_{summaryleveltwo}_{commagglevel}_{grabdatetime}.csv"

# Read API key from file
# disabling in public
# keyfile = "census_api_key.txt"
# with open(keyfile) as key:
#     api_key = key.read().strip()
    
# bring your own key, they're free
api_key = "your_api_key"

# Load HS chapter data into a dictionary
# HS chapter data is stable so will not change year to year
hs_column_dict = {}
dict_hs_url = f"{base_url}{dimex}/{dataset}?get=E_COMMODITY&key={api_key}&SUMMARY_LVL=DET&SUMMARY_LVL2=HS&COMM_LVL=HS2&YEAR=2014&MONTH=01"

try:
    hs_response = requests.get(dict_hs_url, timeout=30)
    if hs_response.status_code == 200:
        hs_dict_data = json.loads(hs_response.text)
        headers = hs_dict_data[0]
        hs_column_name = "E_COMMODITY"
        hs_column_index = headers.index(hs_column_name)
        hs_column_dict = {entry[hs_column_index]: True for entry in hs_dict_data[1:] if entry[hs_column_index]}
        print(f"Nice! Got HS chapters.")
    else:
        print(f"Whoops! Failed to retrieve HS dict data from the API: response {hs_response.status_code}")
except Exception as e:
    print(f"UHOH! An error occurred trying to retrieve HS dict data: {e}")

if not hs_column_dict:
    print("HS column dictionary is empty or not loaded correctly. Exiting...")
    exit(1)

### MANUALLY SETTING HS DICT FOR TESTING, COMMENT IN PROD
hs_column_dict = {"93": True, "97": True}

# trying this function to ensure DF has the right columns
def ensure_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]

# Loop through years and months
for year in range(14, 15):
    year_url = f"20{year}"
    for month in range(1, 13):
        month_url = str(month).zfill(2)
        dcode = f"{year_url}-{month_url}"

        # Load port data into a dictionary
        # Port codes may change year to year so need to load for each year but not month
        pt_column_dict = {}
        dict_pt_url = f"{base_url}{dimex}/{dataset}?get=PORT&key={api_key}&YEAR={year_url}&MONTH={month_url}&SUMMARY_LVL=DET&SUMMARY_LVL2=PT"

        try:
            pt_response = requests.get(dict_pt_url, timeout=30)
            if pt_response.status_code == 200:
                pt_dict_data = json.loads(pt_response.text)
                headers = pt_dict_data[0]
                pt_column_name = "PORT"
                pt_column_index = headers.index(pt_column_name)
                pt_column_dict = {entry[pt_column_index]: True for entry in pt_dict_data[1:] if entry[pt_column_index]}
                print(f"Sweet! Got port codes for {year_url}.")
            else:
                print(f"Whoops! Failed to retrieve port dict data from the API: response {pt_response.status_code}")
                continue
        except Exception as e:
            print(f"UHOH! An error occurred trying to retrieve port dict data: {e}")
            continue

        if not pt_column_dict:
            print(f"Port column dictionary is empty or not loading for year {year_url} and month {month_url}. Exiting...")
            exit(1)

        ### MANUALLY SETTING PT DICT FOR TESTING, COMMENT IN PROD
        pt_column_dict = {"2007": True, "1703": True}

        # Loop through ports and HS codes
        # this breaks up results into chunks, so need to loop and concat into DF
        for pt_value in pt_column_dict.keys():
            for hs_value in hs_column_dict.keys():
                # NOTE: the asterik at the end of the URL is a wildcard, it will return all HS6 codes for the chapter specified
                data_url = f"{base_url}{dimex}/{dataset}?get={cols}&key={api_key}&YEAR={year_url}&MONTH={month_url}&SUMMARY_LVL={summarylevel}&SUMMARY_LVL2={summaryleveltwo}&PORT={pt_value}&COMM_LVL={commagglevel}&E_COMMODITY={hs_value}*"

                try:
                    response = requests.get(data_url, timeout=120)
                    if response.status_code == 200:
                        data = json.loads(response.text)
                        if len(data) > 1:  # Check if there's data other than headers
                            temp_df = pd.DataFrame(data[1:], columns=data[0])
                            temp_df = ensure_columns(temp_df, columns)  # Ensure columns are in the right order
                            temp_df = temp_df[columns]  # Reindex columns
                            df = pd.concat([df, temp_df], ignore_index=True)
                            print(df.shape)
                            print(f"Woot! Data retrieved for: {dcode}, {pt_value},{hs_value}")
                    elif response.status_code == 204:
                        # Create a line of zero values if call is valid but no data
                        zero_data = {col: 0 for col in columns}
                        zero_data.update({
                             "YEAR": year_url,
                             "MONTH": month_url,
                             "PORT": pt_value,
                             "E_COMMODITY": hs_value
                         })
                        temp_df = pd.DataFrame([zero_data], columns=columns)
                        df = pd.concat([df, temp_df], ignore_index=True)
                        print(f"Zeroes! 204: YM {dcode}, Pt {pt_value}, HS {hs_value}")
                    else:
                        print(f"NOES! Failed to retrieve data for: {dcode}, {pt_value}, {hs_value} - Status code: {response.status_code}")
                except Exception as e:
                    print(f"UHOH! An error occurred trying to retrieve data: {e}")
                
time.sleep(1)  # Pause to avoid hitting API rate limits
print(f"Loop done! Saving to {csv_filename}...")
# Save the DataFrame as a CSV file
df.to_csv(csv_filename, index=False, header=True)
print(f"Data saved to {csv_filename}")
