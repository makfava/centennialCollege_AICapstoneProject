#!/usr/bin/env python3
"""
Unify TTC delay datasets (Bus, Streetcar, Subway) from 2017 to 2025
Creates a single unified dataset with all three vehicle types
"""

import os
import pandas as pd
from pathlib import Path
import glob

# Base directory
BASE_DIR = Path(__file__).parent.parent / "dataset"
OUTPUT_FILE = BASE_DIR / "ttc_delays_2017_2025_unified.csv"

# Column mapping to standardize names
BUS_XLSX_COLUMNS = {
    'Report Date': 'Date',
    'Route': 'Line',
    'Location': 'Station',
    'Incident': 'Code',
    'Direction': 'Bound'
}

STREETCAR_XLSX_COLUMNS = {
    'Report Date': 'Date',
    'Route': 'Line',
    'Location': 'Station',
    'Incident': 'Code',
    'Direction': 'Bound'
}

def standardize_columns(df, vehicle_type):
    """Standardize column names across different file formats"""
    # Rename columns based on vehicle type
    if vehicle_type in ['bus', 'streetcar']:
        df = df.rename(columns=BUS_XLSX_COLUMNS)
    
    # Ensure all required columns exist
    required_columns = ['Date', 'Line', 'Time', 'Day', 'Station', 'Code', 
                       'Min Delay', 'Min Gap', 'Bound', 'Vehicle']
    
    # For subway, Line might be in a different position, but it should exist
    if 'Line' not in df.columns and 'Route' in df.columns:
        df['Line'] = df['Route']
    
    # Select only the columns we need (in the right order)
    available_columns = [col for col in required_columns if col in df.columns]
    df = df[available_columns]
    
    # Add Vehicle_Type column
    df['Vehicle_Type'] = vehicle_type.upper()
    
    return df

def load_xlsx_files(vehicle_type, years):
    """Load XLSX files for a specific vehicle type and years"""
    dataframes = []
    vehicle_dir = BASE_DIR / f"ttc-{vehicle_type}-delay-data"
    
    for year in years:
        # Try different filename patterns
        pattern = f"ttc-{vehicle_type}-delay-data-{year}.xlsx"
        file_path = vehicle_dir / pattern
        
        if file_path.exists():
            try:
                print(f"  Loading {file_path.name}...")
                df = pd.read_excel(file_path)
                df = standardize_columns(df, vehicle_type)
                dataframes.append(df)
                print(f"    ✓ Loaded {len(df):,} rows")
            except Exception as e:
                print(f"    ✗ Error loading {file_path.name}: {e}")
        else:
            print(f"  ⚠ No file found for {vehicle_type} {year}")
    
    return dataframes

def load_csv_2025(vehicle_type):
    """Load CSV file for 2025 data"""
    vehicle_dir = BASE_DIR / f"ttc-{vehicle_type}-delay-data"
    
    # Find the CSV file for 2025
    csv_files = list(vehicle_dir.glob("*2025*.csv"))
    csv_files = [f for f in csv_files if 'unified' not in f.name.lower()]
    
    if not csv_files:
        print(f"  ⚠ No 2025 CSV file found for {vehicle_type}")
        return None
    
    csv_file = csv_files[0]
    try:
        print(f"  Loading {csv_file.name}...")
        df = pd.read_csv(csv_file)
        
        # Remove _id column if present
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])
        
        # Standardize columns
        df = standardize_columns(df, vehicle_type)
        print(f"    ✓ Loaded {len(df):,} rows")
        return df
    except Exception as e:
        print(f"    ✗ Error loading {csv_file.name}: {e}")
        return None

def process_subway_special_files():
    """Process special subway files (2014-2017 split files)"""
    subway_dir = BASE_DIR / "ttc-subway-delay-data"
    dataframes = []
    
    # Files that contain 2017 data
    special_files = [
        "ttc-subway-delay-jan-2014-april-2017.xlsx",
        "ttc-subway-delay-may-december-2017.xlsx"
    ]
    
    for filename in special_files:
        file_path = subway_dir / filename
        if file_path.exists():
            try:
                print(f"  Loading {filename}...")
                df = pd.read_excel(file_path)
                
                # Filter only 2017 data
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df[df['Date'].dt.year == 2017]
                
                df = standardize_columns(df, 'subway')
                dataframes.append(df)
                print(f"    ✓ Loaded {len(df):,} rows from 2017")
            except Exception as e:
                print(f"    ✗ Error loading {filename}: {e}")
    
    return dataframes

def main():
    """Main function to unify all datasets"""
    print("=" * 70)
    print("TTC Delay Datasets Unification (2017-2025)")
    print("=" * 70)
    
    years = list(range(2017, 2025))  # 2017 to 2024
    all_dataframes = []
    
    # Process each vehicle type
    for vehicle_type in ['bus', 'streetcar', 'subway']:
        print(f"\n{'=' * 70}")
        print(f"Processing {vehicle_type.upper()} data")
        print('=' * 70)
        
        # Load XLSX files (2017-2024)
        xlsx_dfs = load_xlsx_files(vehicle_type, years)
        all_dataframes.extend(xlsx_dfs)
        
        # Special handling for subway 2017 files
        if vehicle_type == 'subway':
            special_dfs = process_subway_special_files()
            all_dataframes.extend(special_dfs)
        
        # Load CSV file (2025)
        csv_df = load_csv_2025(vehicle_type)
        if csv_df is not None:
            all_dataframes.append(csv_df)
    
    if not all_dataframes:
        print("\n✗ No data loaded. Exiting.")
        return
    
    print(f"\n{'=' * 70}")
    print("Combining all datasets...")
    print('=' * 70)
    
    # Combine all dataframes
    unified_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Ensure Date is datetime
    unified_df['Date'] = pd.to_datetime(unified_df['Date'], errors='coerce')
    
    # Filter to keep only 2017-2025 data
    unified_df = unified_df[
        (unified_df['Date'].dt.year >= 2017) & 
        (unified_df['Date'].dt.year <= 2025)
    ]
    
    # Sort by Date
    unified_df = unified_df.sort_values('Date').reset_index(drop=True)
    
    # Reorder columns
    column_order = ['Vehicle_Type', 'Date', 'Line', 'Time', 'Day', 'Station', 
                   'Code', 'Min Delay', 'Min Gap', 'Bound', 'Vehicle']
    unified_df = unified_df[[col for col in column_order if col in unified_df.columns]]
    
    print(f"\n✓ Combined dataset:")
    print(f"  Total rows: {len(unified_df):,}")
    print(f"  Date range: {unified_df['Date'].min().date()} to {unified_df['Date'].max().date()}")
    print(f"  Vehicle types: {unified_df['Vehicle_Type'].value_counts().to_dict()}")
    
    # Save to CSV
    print(f"\n{'=' * 70}")
    print(f"Saving unified dataset...")
    print('=' * 70)
    unified_df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Saved to: {OUTPUT_FILE}")
    print(f"  File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")
    
    # Show sample
    print(f"\n{'=' * 70}")
    print("Sample data (first 5 rows):")
    print('=' * 70)
    print(unified_df.head().to_string())

if __name__ == '__main__':
    main()
