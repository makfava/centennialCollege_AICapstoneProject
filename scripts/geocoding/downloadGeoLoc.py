# -*- coding: utf-8 -*-
"""
Created on Wed Feb 11 09:57:59 2026

@author: marco
"""

import pandas as pd
from geopy.geocoders import Nominatim
import time, os
import glob

# Load master file
unique_locations_df = pd.read_csv("unique_locations_geocoded_master.csv")

# Filter missing coordinates
missing = unique_locations_df[unique_locations_df['Latitude'].isna()].copy()

# Cleaning function
def clean_station_name(name):
    name = name.strip().title().replace(".", "")
    abbr_map = {
        "Bd": "Bloor-Danforth",
        "Yus": "Yonge-University-Spadina",
        "Shp": "Sheppard",
        "Stn": "Station"
    }
    for k,v in abbr_map.items():
        name = name.replace(k, v)
    if " And " in name or " At " in name:
        parts = name.replace(" At ", " And ").split(" And ")
        if len(parts) == 2:
            name = f"{parts[0].strip()} St & {parts[1].strip()} St, Toronto, Canada"
    return name

# Apply cleaning
missing['Cleaned'] = missing['Station'].apply(clean_station_name)

# Geocoder
geolocator = Nominatim(user_agent="ttc_delays_mapper")

batch_size = 1000
total = len(missing)

for start in range(0, total, batch_size):
    end = min(start + batch_size, total)
    filename = f"retry_batch_{start}_{end}.csv"
    
    # Skip if already saved
    if os.path.exists(filename):
        print(f"Skipping {filename}, already exists.")
        continue
    
    batch = missing.iloc[start:end]
    coords = []
    
    for i, row in batch.iterrows():
        try:
            result = geolocator.geocode(row['Cleaned'])
            if result:
                coords.append((row['Station'], result.latitude, result.longitude))
        except Exception:
            pass
        
        if i % 100 == 0 or i == end:
            print(f"Processed {i}/{total} missing rows")
        time.sleep(1)
    
    # Save batch
    batch_df = pd.DataFrame(coords, columns=['Station','Latitude','Longitude'])
    batch_df.to_csv(filename, index=False)
    print(f"Saved {filename}")
    
    

# Load master file
master_df = pd.read_csv("unique_locations_geocoded_master.csv")

# Load all retry batch files
retry_files = glob.glob("retry_batch_*.csv")
retry_dfs = [pd.read_csv(f) for f in retry_files]
retry_df = pd.concat(retry_dfs, ignore_index=True)

print(f"Retry dataset has {len(retry_df)} recovered coordinates")

# Merge retry results into master
merged_df = master_df.merge(retry_df, on="Station", how="left", suffixes=('', '_retry'))

# Fill NaN lat/long with retry values
merged_df['Latitude'] = merged_df['Latitude'].fillna(merged_df['Latitude_retry'])
merged_df['Longitude'] = merged_df['Longitude'].fillna(merged_df['Longitude_retry'])

# Drop helper columns
merged_df = merged_df.drop(columns=['Latitude_retry','Longitude_retry'])

# Save updated master
merged_df.to_csv("unique_locations_geocoded_master_updated.csv", index=False)

print(f"Updated master file saved with {len(merged_df)} rows")
print("Still missing:", merged_df['Latitude'].isna().sum())






# Merge to the original dataset

# Load delays dataset
df = pd.read_csv("../dataset/ttc_delays_2017_2025_unified.csv")

# Load geocoded master file (Station, Latitude, Longitude)
geo_master = pd.read_csv("unique_locations_geocoded_master_updated.csv")

# --- Before merge ---
print("Before merge:")
print("Rows in delays dataset:", len(df))
print("Unique stations in delays:", df['Station'].nunique())

# --- Merge coordinates into delays dataset ---
df_merged = df.merge(geo_master, on="Station", how="left")

# --- After merge ---
print("\nAfter merge:")
print("Rows with coordinates:", df_merged[['Latitude','Longitude']].notna().all(axis=1).sum())
print("Rows missing coordinates:", df_merged[['Latitude','Longitude']].isna().any(axis=1).sum())
print("Coverage rate:", df_merged[['Latitude','Longitude']].notna().all(axis=1).mean())

# Save enriched dataset
df_merged.to_csv("ttc_delays_with_coords.csv", index=False)




# Load delays dataset
df = pd.read_csv("../dataset/ttc_delays_2017_2025_unified.csv")

# Load geocoded master file (Station, Latitude, Longitude)
geo_master = pd.read_csv("unique_locations_geocoded_master_updated.csv")

# Merge coordinates into delays dataset
df_merged = df.merge(geo_master, on="Station", how="left")

# Calculate missing and coverage
total_rows = len(df_merged)
missing_rows = df_merged[['Latitude','Longitude']].isna().any(axis=1).sum()
with_coords = df_merged[['Latitude','Longitude']].notna().all(axis=1).sum()

print(f"Total rows: {total_rows}")
print(f"Rows with coordinates: {with_coords}")
print(f"Rows missing coordinates: {missing_rows}")
print(f"Missing percentage: {missing_rows / total_rows:.2%}")






df = pd.read_csv("ttc_delays_with_coords.csv")

# Filter rows still missing coordinates
missing_rows = df[df[['Latitude','Longitude']].isna().any(axis=1)]

print("Total missing rows:", len(missing_rows))
print("Unique stations still missing:", missing_rows['Station'].nunique())

# Show the top 20 most frequent missing stations
top_missing = missing_rows['Station'].value_counts().head(20)
print("\nTop 20 missing stations:")
print(top_missing)









































