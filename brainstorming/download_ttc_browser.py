#!/usr/bin/env python3
"""
Download TTC delay datasets using browser automation
Extracts download URLs from rendered pages and downloads files
"""

import os
import time
import requests
import json
import re
from urllib.parse import urljoin, urlparse

# This script will be used with browser automation
# The browser will extract the download links and this script will download them

BASE_URL = "https://open.toronto.ca"
DOWNLOAD_DIR = "../dataset"

def download_file(url, filepath):
    """Download a file from URL"""
    try:
        print(f"  Downloading: {os.path.basename(filepath)}")
        response = requests.get(url, stream=True, timeout=60, allow_redirects=True)
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

def extract_filename_from_url(url, link_text=""):
    """Extract filename from URL or link text"""
    # Try to extract from link text first
    if link_text:
        match = re.search(r'Download\s+(.+?)\s+dataset', link_text, re.IGNORECASE)
        if match:
            dataset_part = match.group(1).strip()
            filename = dataset_part.lower().replace(' ', '-').replace('_', '-')
            
            # Add extension
            if 'xlsx' in link_text.lower():
                filename += '.xlsx'
            elif 'csv' in link_text.lower():
                filename += '.csv'
            elif 'json' in link_text.lower():
                filename += '.json'
            else:
                filename += '.xlsx'
            
            return re.sub(r'[^\w\-\.]', '', filename)
    
    # Fallback to URL
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
    print("This script is meant to be used with browser automation")
    print("Use download_ttc_datasets.py instead")
