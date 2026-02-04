#!/usr/bin/env python3
"""
Download TTC delay datasets from Toronto Open Data Portal using Playwright
Downloads datasets from:
- TTC Streetcar Delay Data
- TTC Bus Delay Data
- TTC LRT Delay Data
- TTC Subway Delay Data
"""

import os
import time
import json
import re
import asyncio
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

BASE_URL = "https://open.toronto.ca"
DATASET_URLS = [
    "https://open.toronto.ca/dataset/ttc-streetcar-delay-data/",
    "https://open.toronto.ca/dataset/ttc-bus-delay-data",
    "https://open.toronto.ca/dataset/ttc-lrt-delay-data/",
    "https://open.toronto.ca/dataset/ttc-subway-delay-data/",
]

DOWNLOAD_DIR = "../dataset"

async def extract_download_links(page, url):
    """Extract all download links from a dataset page"""
    print(f"  Loading page: {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # Wait for page to be fully loaded
    await page.wait_for_timeout(3000)
    
    # Wait for download links to appear - try multiple selectors
    try:
        await page.wait_for_selector('a[href*="download"], a:has-text("Download")', timeout=15000)
    except:
        try:
            await page.wait_for_selector('a', timeout=5000)
        except:
            pass
    
    # Wait a bit more for all content to load
    await page.wait_for_timeout(2000)
    
    # Scroll to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(1000)
    
    # Extract download links
    download_links = []
    
    # Find all links
    links = await page.query_selector_all('a')
    
    for link in links:
        try:
            link_text = await link.inner_text()
            href = await link.get_attribute('href')
            
            if not href:
                continue
            
            # Normalize link text
            link_text = link_text.strip() if link_text else ""
            
            # Check if it's a download link - be more lenient
            is_download = False
            link_text_lower = link_text.lower() if link_text else ""
            href_lower = href.lower() if href else ""
            
            # Primary check: has "download" in text and data file indicators
            if link_text and 'download' in link_text_lower:
                # Check for data file indicators - be very lenient
                if any(ext in link_text_lower for ext in ['xlsx', 'csv', 'json', 'xml', 'dataset', 'format', 'kb', 'mb']):
                    is_download = True
                # Also check if it mentions a year (datasets often have years)
                if re.search(r'20\d{2}', link_text):
                    is_download = True
            
            # Secondary check: href patterns
            if not is_download and href:
                if '/resource/' in href_lower:
                    is_download = True
                elif any(ext in href_lower for ext in ['.xlsx', '.csv', '.json', '.xml']):
                    is_download = True
            
            if is_download:
                full_url = urljoin(BASE_URL, href)
                
                # Extract filename from link text
                filename = None
                match = re.search(r'Download\s+(.+?)\s+(?:dataset|in)', link_text, re.IGNORECASE)
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
                    elif 'xml' in link_text.lower():
                        filename += '.xml'
                    else:
                        filename += '.xlsx'
                
                # If no filename extracted, try from href
                if not filename:
                    parsed = urlparse(href)
                    filename = os.path.basename(parsed.path)
                    if not filename or filename == '/' or '.' not in filename:
                        if '/resource/' in href:
                            resource_id = href.split('/resource/')[-1].split('/')[0]
                            format_type = 'xlsx'
                            if 'csv' in link_text.lower():
                                format_type = 'csv'
                            elif 'json' in link_text.lower():
                                format_type = 'json'
                            filename = f"{resource_id}.{format_type}"
                        else:
                            filename = "download.xlsx"
                
                # Clean filename
                filename = re.sub(r'[^\w\-\.]', '', filename)
                
                download_links.append({
                    'url': full_url,
                    'filename': filename,
                    'text': link_text
                })
        except Exception as e:
            # Skip links that cause errors
            continue
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_links = []
    for link in download_links:
        if link['url'] not in seen_urls:
            seen_urls.add(link['url'])
            unique_links.append(link)
    
    print(f"  Found {len(unique_links)} download links")
    return unique_links

def download_file_sync(url, filepath):
    """Download a file from URL using requests (synchronous)"""
    try:
        import requests
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

async def download_datasets_from_page(page, url, base_dir):
    """Download all datasets from a page"""
    # Extract dataset name from URL
    dataset_name = url.split('/dataset/')[-1].rstrip('/')
    dataset_dir = os.path.join(base_dir, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Get download links
    download_links = await extract_download_links(page, url)
    
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
        
        # Skip if file already exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            if file_size > 0:
                print(f"  [{i}/{len(download_links)}] ⊘ Skipping {filename} (already exists)")
                downloaded_files.append(filepath)
                continue
        
        print(f"  [{i}/{len(download_links)}] {filename}")
        
        # Use synchronous download in executor to avoid blocking
        loop = asyncio.get_event_loop()
        if await loop.run_in_executor(None, download_file_sync, url, filepath):
            downloaded_files.append(filepath)
            await asyncio.sleep(0.5)  # Be polite, wait between downloads
    
    return downloaded_files

async def main():
    """Main function to download all TTC datasets"""
    print("=" * 70)
    print("TTC Delay Datasets Downloader (Playwright)")
    print("=" * 70)
    
    # Create download directory
    download_dir = os.path.abspath(DOWNLOAD_DIR)
    os.makedirs(download_dir, exist_ok=True)
    print(f"\nDownload directory: {download_dir}")
    
    all_downloaded = []
    
    async with async_playwright() as p:
        # Launch browser - try chromium first, fallback to firefox
        print("\nLaunching browser...")
        browser = None
        try:
            browser = await p.chromium.launch(headless=True)
            print("  ✓ Using Chromium")
        except Exception as e:
            print(f"  ⚠ Chromium failed: {e}")
            try:
                browser = await p.firefox.launch(headless=True)
                print("  ✓ Using Firefox")
            except Exception as e2:
                print(f"  ⚠ Firefox failed: {e2}")
                browser = await p.webkit.launch(headless=True)
                print("  ✓ Using WebKit")
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Process each dataset URL
        for url in DATASET_URLS:
            print(f"\n{'=' * 70}")
            print(f"Processing: {url}")
            print('=' * 70)
            
            try:
                downloaded = await download_datasets_from_page(page, url, download_dir)
                all_downloaded.extend(downloaded)
                print(f"\n✓ Completed: {len(downloaded)} files downloaded")
            except Exception as e:
                print(f"\n✗ Error processing {url}: {e}")
                import traceback
                traceback.print_exc()
        
        await browser.close()
    
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

if __name__ == '__main__':
    asyncio.run(main())
