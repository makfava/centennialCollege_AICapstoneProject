# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 17:37:40 2026

@author: marco
"""

# main.py
import pandas as pd
import joblib
import json

from scripts.exploration.data_exploration import run_exploration
from scripts.modeling.preprocessing import preprocess_df
from scripts.modeling.train_model import train_model, compute_weights
from scripts.modeling.predict import predict_delay
from scripts.paths import get_dataset_path, get_model_path


# Load dataset
df = pd.read_csv(get_dataset_path("ttc_delays_2017_2025_final.csv"))

# Check missing values before cleaning
print("Missing values before cleaning:")
print(df[["Station", "Latitude", "Longitude"]].isna().sum())

# Drop rows missing location info
df = df.dropna(subset=["Station", "Latitude", "Longitude"])

# Check missing values after cleaning
print("\nMissing values after cleaning:")
print(df[["Station", "Latitude", "Longitude"]].isna().sum())


# Step 1: Run exploration functions
run_exploration(df)

# Normalize vehicle type to consistent casing
df["Vehicle_Type"] = df["Vehicle_Type"].astype(str).str.strip().str.capitalize()

# Step 2: Split into 3 DataFrames and preprocess each
df_bus = preprocess_df(df[df["Vehicle_Type"] == "Bus"])
df_subway = preprocess_df(df[df["Vehicle_Type"] == "Subway"])
df_streetcar = preprocess_df(df[df["Vehicle_Type"] == "Streetcar"])

datasets = {"Bus": df_bus, "Subway": df_subway, "Streetcar": df_streetcar}

# Step 3: Train and save models
for vehicle, df_vehicle in datasets.items():
    if len(df_vehicle) < 50:
        print(f"Skipping {vehicle}, not enough data ({len(df_vehicle)} rows)")
        continue

    print(f"\n=== Training {vehicle} model ===")
    model, features = train_model(df_vehicle)
    weights_by_code = compute_weights(df_vehicle, model, features)

    # Save model and weights
    model_file = get_model_path(f"ttc_delay_model_{vehicle.lower()}.pkl")
    weights_file = get_model_path(f"weights_by_code_{vehicle.lower()}.json")

    joblib.dump(model, model_file)
    with open(weights_file, "w") as f:
        json.dump(weights_by_code, f)

    print(f"Saved {vehicle} model and weights")


# Step 4: Unified prediction function
def check_delay(vehicle_type, station, code, line, hour, weekday):
    # Load correct model + weights
    model_file = get_model_path(f"ttc_delay_model_{vehicle.lower()}.pkl")
    weights_file = get_model_path(f"weights_by_code_{vehicle.lower()}.json")

    model = joblib.load(model_file)
    with open(weights_file) as f:
        weights_by_code = json.load(f)

    # Pick correct dataset
    df_vehicle = datasets[vehicle_type]

    # Call predict
    return predict_delay(vehicle_type, station, code, line, hour, weekday, df_vehicle, model, weights_by_code)


# Step 5: Example predictions
check_delay("Bus", "BROADVIEW STATION", "COLLISION - TTC", "100", 16, 4)
check_delay("Subway", "KENNEDY STATION", "MUIRS", "YU", 9, 2)
check_delay("Streetcar", "BINGHAM LOOP", "Cleaning", "503", 13, 3)
