import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from geopy.geocoders import Nominatim
import time

# -----------------------------
# 1. Load and preprocess delays dataset
# -----------------------------
df = pd.read_csv("../dataset/ttc_delays_2017_2025_final.csv")

# Convert Date and Time into datetime object
df['Date'] = pd.to_datetime(df['Date'])
df['Time'] = pd.to_datetime(df['Time'], errors='coerce').dt.time
df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))

# Encode categorical variables
df_encoded = pd.get_dummies(df, columns=['Vehicle_Type','Code','Bound'])

# Normalize numeric features
scaler = MinMaxScaler()
df[['Min Delay','Min Gap']] = scaler.fit_transform(df[['Min Delay','Min Gap']])

# -----------------------------
# 2. Geocode incident locations
# -----------------------------
geolocator = Nominatim(user_agent="ttc_delays_mapper")

# Get unique incident locations (from Station column)
unique_locations = df['Station'].dropna().unique()

# Take a sample of 200 unique locations to test
sample_locations = df['Station'].dropna().unique()[:200]

location_map = {}
for i, loc in enumerate(sample_locations, 1):
    try:
        result = geolocator.geocode(loc + ", Toronto, Canada")
        if result:
            location_map[loc] = (result.latitude, result.longitude)
        else:
            location_map[loc] = (None, None)
    except Exception:
        location_map[loc] = (None, None)
    
    if i % 50 == 0:
        print(f"Processed {i} / {len(sample_locations)} sample locations")
    time.sleep(1)  # avoid rate limits

# Map back to DataFrame for the sample
df_sample = df[df['Station'].isin(sample_locations)].copy()
df_sample[['Latitude','Longitude']] = df_sample['Station'].map(location_map).apply(pd.Series)

print(df_sample[['Station','Latitude','Longitude']].head(20))

# Count how many locations got valid coordinates
detected = df_sample['Latitude'].notna().sum()
missing = df_sample['Latitude'].isna().sum()

print(f"Detected coordinates: {detected}")
print(f"Missing coordinates: {missing}")
print(f"Detection rate: {detected / (detected + missing):.2%}")

import matplotlib.pyplot as plt

plt.figure(figsize=(8,8))
plt.scatter(df_sample['Longitude'], df_sample['Latitude'], 
            s=5, alpha=0.5, c='blue')
plt.title("Incident Locations (Sample)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()

import folium

# Center map roughly on Toronto
m = folium.Map(location=[43.7, -79.4], zoom_start=11)

# Add incident markers
for _, row in df_sample.dropna(subset=['Latitude','Longitude']).iterrows():
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=2,
        color='red',
        fill=True,
        fill_opacity=0.6
    ).add_to(m)

# Save to HTML
m.save("incident_map_sample.html")



from folium.plugins import HeatMap

m = folium.Map(location=[43.7, -79.4], zoom_start=11)

# Prepare data for heatmap
heat_data = df_sample.dropna(subset=['Latitude','Longitude'])[['Latitude','Longitude']].values.tolist()

HeatMap(heat_data, radius=8, blur=6, max_zoom=13).add_to(m)

m.save("incident_heatmap_sample.html")

# most problematic intersections:
top_locations = df_sample['Station'].value_counts().head(20)
print(top_locations)

top_locations = df_sample['Station'].value_counts().head(20)

plt.figure(figsize=(10,6))
top_locations.plot(kind='bar', color='steelblue')
plt.title("Top 20 Incident Locations (Sample)")
plt.ylabel("Number of Incidents")
plt.xticks(rotation=45, ha='right')
plt.show()





# -----------------------------
# 3. Map coordinates back to DataFrame
# -----------------------------
df[['Latitude','Longitude']] = df['Station'].map(location_map).apply(pd.Series)

# -----------------------------
# 4. Check coverage
# -----------------------------
missing = df[df['Latitude'].isna()]
print(f"Missing coordinates after geocoding: {len(missing)} rows")
print(missing['Station'].unique()[:20])  # show first 20 still unmatched