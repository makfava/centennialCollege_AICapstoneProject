import pandas as pd

# Load original delays dataset
df = pd.read_csv("../dataset/ttc_delays_2017_2025_unified.csv")

# Load geocoded master file (from chunks)
geo_master = pd.read_csv("unique_locations_geocoded_master_updated.csv")

# Apply cleaning function to both datasets
def clean_station_name(name):
    if pd.isna(name):
        return name
    name = name.strip().title().replace(".", "")
    abbr_map = {
        "Bd": "Bloor-Danforth",
        "BD": "Bloor-Danforth",
        "Yus": "Yonge-University-Spadina",
        "YUS": "Yonge-University-Spadina",
        "Shp": "Sheppard",
        "Stn": "Station",
        "Statio": "Station",
        "MC": "Metropolitan Centre",
        "Ctr": "Centre",
        "Centr": "Centre"
    }
    for k,v in abbr_map.items():
        name = name.replace(k, v)
    if " And " in name or " At " in name:
        parts = name.replace(" At ", " And ").split(" And ")
        if len(parts) == 2:
            name = f"{parts[0].strip()} St & {parts[1].strip()} St, Toronto, Canada"
    return name

df['Station_cleaned'] = df['Station'].apply(clean_station_name)
geo_master['Station_cleaned'] = geo_master['Station'].apply(clean_station_name)

# Deduplicate geo master so each station has one coordinate entry
geo_master_unique = geo_master.drop_duplicates(subset=['Station_cleaned'])

# Merge (one-to-many: one station → many incidents)
df_merged = df.merge(
    geo_master_unique[['Station_cleaned','Latitude','Longitude']],
    on="Station_cleaned", how="left"
)

print("Rows after merge:", len(df_merged))  # should equal 439,655 (same as original)

# Save enriched dataset
df_merged.to_csv("../dataset/ttc_delays_2017_2025_unified_with_coords.csv", index=False)




import pandas as pd

# Load merged dataset (after deduplicating geo master)
df_merged = pd.read_csv("../dataset/ttc_delays_2017_2025_unified_with_coords.csv")

df_merged.info()

# --- Coverage check ---
total_rows = len(df_merged)
missing_rows = df_merged[['Latitude','Longitude']].isna().any(axis=1).sum()
with_coords = df_merged[['Latitude','Longitude']].notna().all(axis=1).sum()

print(f"Total rows: {total_rows}")
print(f"Rows with coordinates: {with_coords}")
print(f"Rows missing coordinates: {missing_rows}")
print(f"Missing percentage: {missing_rows / total_rows:.2%}")

# --- Top 20 stations still missing ---
missing_stations = df_merged[df_merged[['Latitude','Longitude']].isna().any(axis=1)]
top_missing = missing_stations['Station'].value_counts().head(20)

print("\nTop 20 stations still missing coordinates:")
print(top_missing)




import requests

def test_nominatim(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    response = requests.get(url, params=params, headers={"User-Agent": "MarcoTest"})
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['display_name'], data[0]['lat'], data[0]['lon']
    return None

# Examples
print(test_nominatim("King St W & Queen St W, Toronto, Canada"))
print(test_nominatim("King Street West & Queen Street West, Toronto, Canada"))
print(test_nominatim("Weston Rd And Bradstock, Toronto, Canada"))
print(test_nominatim("Weston Road & Bradstock Road, Toronto, Canada"))


