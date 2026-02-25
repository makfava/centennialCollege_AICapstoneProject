# -*- coding: utf-8 -*-
"""
Created on Thu Feb 19 15:39:51 2026

@author: marco
"""

import pandas as pd
import re
from difflib import SequenceMatcher

MIN_STATION_COUNT = 10
SIMILARITY_THRESHOLD = 0.75   # lowered threshold
BATCH_SIZE = 200

def normalize_station_name(name: str) -> str:
    """Normalize station names for comparison."""
    name = str(name).upper().strip()
    name = re.sub(r'^\d+\s*', '', name)          # remove leading numbers
    name = re.sub(r'[^A-Z0-9\s]', '', name)      # remove punctuation
    name = re.sub(r'\s+', ' ', name)             # collapse whitespace
    return name

def token_similarity(a: str, b: str) -> float:
    """Word-level Jaccard similarity."""
    set_a, set_b = set(a.split()), set(b.split())
    if not set_a or not set_b:
        return 0
    return len(set_a & set_b) / len(set_a | set_b)

def combined_similarity(a: str, b: str) -> float:
    """Combine character and token similarity."""
    char_sim = SequenceMatcher(None, a, b).ratio()
    tok_sim = token_similarity(a, b)
    return (char_sim + tok_sim) / 2

def create_station_mapping(df, min_count=MIN_STATION_COUNT, similarity_threshold=SIMILARITY_THRESHOLD):
    # Normalize all names first
    df['Normalized'] = df['Station'].apply(normalize_station_name)

    station_counts = df['Normalized'].value_counts()
    valid_stations = station_counts[station_counts >= min_count].index.tolist()
    station_mapping = {}

    sorted_stations = sorted(station_counts.index.tolist(), key=lambda x: station_counts[x], reverse=True)

    for station in sorted_stations:
        if station in station_mapping:
            continue

        best_match, best_ratio = None, 0
        for valid_station in valid_stations:
            if valid_station == station:
                continue
            ratio = combined_similarity(station, valid_station)
            if ratio > best_ratio and ratio >= similarity_threshold:
                if station_counts[valid_station] >= station_counts[station]:
                    best_match, best_ratio = valid_station, ratio

        if best_match:
            station_mapping[station] = best_match
            print(f"Mapping '{station}' -> '{best_match}' (similarity: {best_ratio:.2f})")

    return station_mapping

def correct_stations_with_checkpoint(input_path="../TEST/ttc_delays_2017_2025_final.csv",
                                     output_path="../TEST/ttc_delays_2017_2025_final_corrected.csv",
                                     batch_size=BATCH_SIZE):
    df = pd.read_csv(input_path)

    # Normalize before mapping
    df['Normalized'] = df['Station'].apply(normalize_station_name)
    station_mapping = create_station_mapping(df)

    total_rows = len(df)
    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i+batch_size].copy()
        batch['Normalized'] = batch['Normalized'].map(station_mapping).fillna(batch['Normalized'])
        batch['Station'] = batch['Normalized']  # overwrite original with corrected

        if i == 0:
            batch.to_csv(output_path, index=False)
        else:
            batch.to_csv(output_path, mode='a', header=False, index=False)

        print(f"✅ Saved rows {i+1} to {min(i+batch_size, total_rows)} / {total_rows}")

    print(f"\nUnique stations after correction: {df['Normalized'].nunique()}")
    print(f"Mapped {len(station_mapping)} station name variations")

# Run correction safely on TEST copy
correct_stations_with_checkpoint()
