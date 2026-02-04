#!/usr/bin/env python3
"""
Download TTC delay datasets from Toronto Open Data Portal
Downloads datasets from:
- TTC Streetcar Delay Data
- TTC Bus Delay Data
- TTC LRT Delay Data
- TTC Subway Delay Data

Uses Selenium to extract download links and requests to download files
"""

import os
import time
import requests
import json
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

BASE_URL = "https://open.toronto.ca"
DATASET_URLS = [
    "https://open.toronto.ca/dataset/ttc-streetcar-delay-data/",
    "https://open.toronto.ca/dataset/ttc-bus-delay-data",
    "https://open.toronto.ca/dataset/ttc-lrt-delay-data/",
    "https://open.toronto.ca/dataset/ttc-subway-delay-data/",
]

DOWNLOAD_DIR = "../dataset"

def setup_driver():
    """Setup Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Trying Firefox...")
        try:
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            driver = webdriver.Firefox(options=firefox_options)
            return driver
        except Exception as e2:
            print(f"Error setting up Firefox driver: {e2}")
            raise

def extract_download_links(driver, url):
    """Extract all download links from a dataset page"""
    print(f"  Loading page: {url}")
    driver.get(url)
    
    # Wait longer for JavaScript to load content
    time.sleep(5)
    
    # Wait for download links to appear - they usually have "Download" text
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
        )
    except TimeoutException:
        print(f"  ⚠ Timeout waiting for download links, but continuing...")
    
    # Wait a bit more for all content to load
    time.sleep(3)
    
    # Scroll to load lazy content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    # Get page source and parse
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    download_links = []
    
    # Find all links that contain "Download" and have href
    all_links = soup.find_all('a', href=True)
    
    print(f"  Found {len(all_links)} total links on page")
    
    for link in all_links:
        href = link.get('href', '')
        link_text = link.get_text(strip=True)
        
        # Check if it's a download link - be more lenient
        if 'download' in link_text.lower():
            # Check if it's a data file link
            if any(ext in link_text.lower() for ext in ['xlsx', 'csv', 'json', 'xml', 'dataset']):
                full_url = urljoin(BASE_URL, href)
                
                # Extract filename from link text
                filename = None
                
                # Try to extract dataset name from link text
                # Pattern: "Download ttc-streetcar-delay-data-2014 dataset in XLSX format"
                match = re.search(r'Download\s+(.+?)\s+(?:dataset|in)', link_text, re.IGNORECASE)
                if match:
                    dataset_part = match.group(1).strip()
                    # Clean the name
                    filename = dataset_part.lower().replace(' ', '-').replace('_', '-')
                    
                    # Add extension
                    if 'xlsx' in link_text.lower():
                        filename += '.xlsx'
                    elif 'csv' in link_text.lower():
                        filename += '.csv'
                    elif 'json' in link_text.lower():
                        filename += '.json'
                    elif 'xml' in link_text.lower():
                        filename += '.xml'
                    else:
                        filename += '.xlsx'  # Default
                
                # If no filename extracted, try from href
                if not filename:
                    parsed = urlparse(href)
                    filename = os.path.basename(parsed.path)
                    if not filename or filename == '/' or '.' not in filename:
                        # Try to extract from resource ID
                        if '/resource/' in href:
                            resource_id = href.split('/resource/')[-1].split('/')[0]
                            format_type = 'xlsx'
                            if 'csv' in link_text.lower():
                                format_type = 'csv'
                            elif 'json' in link_text.lower():
                                format_type = 'json'
                            filename = f"{resource_id}.{format_type}"
                        else:
                            # Generate from link text
                            filename = link_text.lower().replace(' ', '-').replace('download', '').strip()
                            filename = re.sub(r'[^a-z0-9\-]', '', filename)
                            if '.' not in filename:
                                filename += '.xlsx'
                
                # Clean filename
                filename = re.sub(r'[^\w\-\.]', '', filename)
                
                download_links.append({
                    'url': full_url,
                    'filename': filename,
                    'text': link_text
                })
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_links = []
    for link in download_links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)
    
    print(f"  Found {len(unique_links)} download links")
    return unique_links

def download_file(url, filepath):
    """Download a file from URL"""
    try:
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

def download_datasets_from_page(driver, url, base_dir):
    """Download all datasets from a page"""
    # Extract dataset name from URL
    dataset_name = url.split('/dataset/')[-1].rstrip('/')
    dataset_dir = os.path.join(base_dir, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Get download links
    download_links = extract_download_links(driver, url)
    
    if not download_links:
        print(f"  ⚠ No download links found")
        return []
    
    downloaded_files = []
    
    for i, link_info in enumerate(download_links, 1):
        url = link_info['url']
        filename = link_info['filename'] or 'download.xlsx'
        
        # Clean filename
        filename = re.sub(r'[^\w\-\.]', '', filename)
        filepath = os.path.join(dataset_dir, filename)
        
        # Skip if file already exists and has content
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 0:
                print(f"  [{i}/{len(download_links)}] ⊘ Skipping {filename} (already exists)")
                downloaded_files.append(filepath)
                continue
        
        print(f"  [{i}/{len(download_links)}] {filename}")
        
        if download_file(url, filepath):
            downloaded_files.append(filepath)
            time.sleep(0.5)  # Be polite, wait between downloads
    
    return downloaded_files

def main():
    """Main function to download all TTC datasets"""
    print("=" * 70)
    print("TTC Delay Datasets Downloader")
    print("=" * 70)
    
    # Create download directory
    download_dir = os.path.abspath(DOWNLOAD_DIR)
    os.makedirs(download_dir, exist_ok=True)
    print(f"\nDownload directory: {download_dir}")
    
    driver = None
    all_downloaded = []
    
    try:
        driver = setup_driver()
        print("✓ Driver initialized successfully\n")
        
        for url in DATASET_URLS:
            print(f"{'=' * 70}")
            print(f"Processing: {url}")
            print('=' * 70)
            
            try:
                downloaded = download_datasets_from_page(driver, url, download_dir)
                all_downloaded.extend(downloaded)
                print(f"\n✓ Completed: {len(downloaded)} files downloaded")
            except Exception as e:
                print(f"\n✗ Error processing {url}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'=' * 70}")
        print("Download Summary")
        print('=' * 70)
        print(f"Total files downloaded: {len(all_downloaded)}")
        print(f"Download directory: {download_dir}")
        
        # Save download log
        log_file = os.path.join(download_dir, 'download_log.json')
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': len(all_downloaded),
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'files': all_downloaded
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nDownload log saved to: {log_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed")

if __name__ == '__main__':
    main()
