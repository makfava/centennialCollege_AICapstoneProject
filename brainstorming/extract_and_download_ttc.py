#!/usr/bin/env python3
"""
Extract download URLs from TTC dataset pages and download files
Uses requests to get page HTML and extract download links
"""

import os
import re
import time
import requests
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE_URL = "https://open.toronto.ca"
DATASET_URLS = [
    "https://open.toronto.ca/dataset/ttc-streetcar-delay-data/",
    "https://open.toronto.ca/dataset/ttc-bus-delay-data",
    "https://open.toronto.ca/dataset/ttc-lrt-delay-data/",
    "https://open.toronto.ca/dataset/ttc-subway-delay-data/",
]

DOWNLOAD_DIR = "../dataset"

def get_page_html(url):
    """Get HTML content from URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  ✗ Error fetching page: {e}")
        return None

def extract_download_links_from_html(html, base_url):
    """Extract download links from HTML"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    download_links = []
    
    # Find all links
    all_links = soup.find_all('a', href=True)
    
    for link in all_links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Check if it's a download link
        if 'download' in link_text.lower() and any(ext in link_text.lower() for ext in ['xlsx', 'csv', 'json', 'xml', 'dataset']):
            full_url = urljoin(base_url, href)
            
            # Extract filename
            filename = None
            match = re.search(r'Download\s+(.+?)\s+(?:dataset|in)', link_text, re.IGNORECASE)
            if match:
                dataset_part = match.group(1).strip()
                filename = dataset_part.lower().replace(' ', '-').replace('_', '-')
                
                if 'xlsx' in link_text.lower():
                    filename += '.xlsx'
                elif 'csv' in link_text.lower():
                    filename += '.csv'
                elif 'json' in link_text.lower():
                    filename += '.json'
                else:
                    filename += '.xlsx'
            
            if not filename:
                parsed = urlparse(href)
                filename = os.path.basename(parsed.path)
                if not filename or filename == '/' or '.' not in filename:
                    if '/resource/' in href:
                        resource_id = href.split('/resource/')[-1].split('/')[0]
                        filename = f"{resource_id}.xlsx"
                    else:
                        filename = "download.xlsx"
            
            filename = re.sub(r'[^\w\-\.]', '', filename)
            
            download_links.append({
                'url': full_url,
                'filename': filename,
                'text': link_text
            })
    
    # Remove duplicates
    seen_urls = set()
    unique_links = []
    for link in download_links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def download_file(url, filepath):
    """Download a file from URL"""
    try:
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

def process_dataset(url, base_dir):
    """Process a single dataset page"""
    dataset_name = url.split('/dataset/')[-1].rstrip('/')
    dataset_dir = os.path.join(base_dir, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)
    
    print(f"\nProcessing: {dataset_name}")
    print(f"  Fetching page...")
    
    html = get_page_html(url)
    if not html:
        return []
    
    print(f"  Extracting download links...")
    download_links = extract_download_links_from_html(html, BASE_URL)
    
    if not download_links:
        print(f"  ⚠ No download links found")
        return []
    
    print(f"  Found {len(download_links)} download links")
    
    downloaded_files = []
    for i, link_info in enumerate(download_links, 1):
        url = link_info['url']
        filename = link_info['filename']
        filepath = os.path.join(dataset_dir, filename)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"  [{i}/{len(download_links)}] ⊘ Skipping {filename}")
            downloaded_files.append(filepath)
            continue
        
        print(f"  [{i}/{len(download_links)}] {filename}")
        if download_file(url, filepath):
            downloaded_files.append(filepath)
            time.sleep(0.5)
    
    return downloaded_files

def main():
    """Main function"""
    print("=" * 70)
    print("TTC Delay Datasets Downloader (HTML Parser)")
    print("=" * 70)
    
    download_dir = os.path.abspath(DOWNLOAD_DIR)
    os.makedirs(download_dir, exist_ok=True)
    print(f"\nDownload directory: {download_dir}")
    
    all_downloaded = []
    
    for url in DATASET_URLS:
        try:
            downloaded = process_dataset(url, download_dir)
            all_downloaded.extend(downloaded)
            print(f"\n✓ Completed: {len(downloaded)} files downloaded")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 70}")
    print("Download Summary")
    print('=' * 70)
    print(f"Total files downloaded: {len(all_downloaded)}")
    
    log_file = os.path.join(download_dir, 'download_log.json')
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files': len(all_downloaded),
            'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'files': all_downloaded
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Download log saved to: {log_file}")

if __name__ == '__main__':
    main()
