#!/usr/bin/env python3
"""
Final script to download TTC datasets
This script should be used with browser automation to extract download URLs
"""

import os
import json
import requests
import time
from urllib.parse import urlparse

DOWNLOAD_DIR = "../dataset"

# These URLs were extracted from the browser snapshots
# You can manually add more URLs here or use browser automation to extract them

# TTC Streetcar Delay Data URLs (example - you need to extract actual URLs from browser)
STREETCAR_URLS = []

# TTC Bus Delay Data URLs
BUS_URLS = []

# TTC LRT Delay Data URLs  
LRT_URLS = []

# TTC Subway Delay Data URLs
SUBWAY_URLS = []

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        print(f"  Downloading: {os.path.basename(filepath)}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, stream=True, timeout=60, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        total_size = 0
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        if total_size == 0:
            print(f"    ⚠ Warning: Downloaded file is empty")
            return False
        
        file_size_mb = total_size / (1024 * 1024)
        if file_size_mb < 1:
            file_size_kb = total_size / 1024
            print(f"    ✓ Downloaded ({file_size_kb:.2f} KB)")
        else:
            print(f"    ✓ Downloaded ({file_size_mb:.2f} MB)")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def extract_filename_from_url(url):
    """Extract filename from URL"""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename or filename == '/' or '.' not in filename:
        if '/resource/' in url:
            resource_id = url.split('/resource/')[-1].split('/')[0]
            filename = f"{resource_id}.xlsx"
        else:
            filename = "download.xlsx"
    return filename

if __name__ == '__main__':
    print("=" * 70)
    print("TTC Delay Datasets Downloader")
    print("=" * 70)
    print("\nThis script requires download URLs to be extracted from the browser.")
    print("Please use browser automation to extract the URLs first.")
    print("\nAlternatively, you can manually add URLs to the script.")
