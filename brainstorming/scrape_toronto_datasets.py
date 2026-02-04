#!/usr/bin/env python3
"""
Scrape Toronto Open Data CSV datasets and create a JSON file
Uses Selenium to handle JavaScript-rendered content
"""

import json
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

BASE_URL = "https://open.toronto.ca"
CATALOGUE_URL = f"{BASE_URL}/catalogue/?formats=CSV"

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

def extract_dataset_info(dataset_element, soup=None):
    """Extract information from a dataset element"""
    dataset = {}
    
    if soup is None:
        soup = BeautifulSoup(dataset_element.get_attribute('outerHTML'), 'html.parser')
        dataset_elem = soup
    else:
        dataset_elem = dataset_element
    
    # Title and URL
    heading = dataset_elem.find('h3')
    if heading:
        link = heading.find('a')
        if link:
            dataset['title'] = link.get_text(strip=True)
            href = link.get('href', '')
            dataset['url'] = urljoin(BASE_URL, href) if href else ''
        else:
            dataset['title'] = heading.get_text(strip=True)
            dataset['url'] = ''
    else:
        return None
    
    # Description
    desc = dataset_elem.find('p')
    dataset['description'] = desc.get_text(strip=True) if desc else ''
    
    # Extract metadata - look for divs with specific structure
    metadata = {}
    meta_divs = dataset_elem.find_all('div', class_=lambda x: x and 'dataset' in x.lower())
    
    # Try to find metadata in the structure
    # Look for text patterns like "Refresh Rate", "Publisher", etc.
    text_content = dataset_elem.get_text()
    
    # Find metadata fields
    metadata_fields = {
        'refresh_rate': ['Refresh Rate'],
        'last_refreshed': ['Last Refreshed'],
        'publisher': ['Publisher'],
        'type': ['Type'],
        'formats': ['Formats'],
        'topics': ['Topics']
    }
    
    for key, labels in metadata_fields.items():
        for label in labels:
            # Try to find the label and extract the value after it
            pattern = f"{label}"
            if pattern in text_content:
                # Find the span or div containing this
                for elem in dataset_elem.find_all(['span', 'div', 'p']):
                    text = elem.get_text()
                    if label in text:
                        # Get the next sibling or extract from text
                        parts = text.split(label, 1)
                        if len(parts) > 1:
                            value = parts[1].strip().split('\n')[0].strip()
                            if value:
                                metadata[key] = value
                                break
                        # Try next sibling
                        next_sib = elem.find_next_sibling()
                        if next_sib:
                            value = next_sib.get_text(strip=True)
                            if value:
                                metadata[key] = value
                                break
    
    # Update dataset with metadata
    for key, value in metadata.items():
        dataset[key] = value if value else ''
    
    # Set defaults if not found
    for key in metadata_fields.keys():
        if key not in dataset:
            dataset[key] = ''
    
    return dataset

def scrape_all_datasets():
    """Scrape all datasets from all pages using Selenium"""
    driver = None
    all_datasets = []
    
    try:
        driver = setup_driver()
        print("Loading initial page...")
        driver.get(CATALOGUE_URL)
        
        # Wait for page to load
        time.sleep(3)
        
        page = 1
        max_pages = 50
        
        while page <= max_pages:
            print(f"Scraping page {page}...")
            
            # Wait for datasets to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h3"))
                )
            except TimeoutException:
                print("Timeout waiting for page to load")
                break
            
            # Get page source and parse with BeautifulSoup
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find dataset containers - they appear to be in a list or div structure
            # Look for h3 headings with links to /dataset/
            dataset_headings = soup.find_all('h3')
            dataset_elements = []
            
            for heading in dataset_headings:
                link = heading.find('a', href=lambda x: x and '/dataset/' in x)
                if link:
                    # Find the parent container (usually article, div, or li)
                    parent = heading.find_parent(['article', 'div', 'li', 'section'])
                    if parent and parent not in dataset_elements:
                        dataset_elements.append(parent)
            
            if not dataset_elements:
                print(f"No datasets found on page {page}. Stopping.")
                break
            
            print(f"Found {len(dataset_elements)} datasets on page {page}")
            
            # Extract data from each dataset
            for elem in dataset_elements:
                dataset = extract_dataset_info(elem, soup)
                if dataset and dataset.get('title'):
                    all_datasets.append(dataset)
            
            # Check for next page
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a[aria-label*="next"], a:contains("»"), nav a:contains("»")')
                if next_button and next_button.is_enabled():
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    page += 1
                else:
                    break
            except NoSuchElementException:
                # Try alternative selectors
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, 'nav[aria-label*="page"]')
                    next_links = pagination.find_elements(By.PARTIAL_LINK_TEXT, '»')
                    if next_links and len(next_links) > 0:
                        next_links[0].click()
                        time.sleep(2)
                        page += 1
                    else:
                        break
                except:
                    print("No next page found. Stopping.")
                    break
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
    
    return all_datasets

def main():
    print("Starting to scrape Toronto Open Data CSV datasets...")
    print("This may take a while as we need to load JavaScript content...")
    
    datasets = scrape_all_datasets()
    
    print(f"\nTotal datasets scraped: {len(datasets)}")
    
    # Save to JSON
    output_file = 'toronto_datasets.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_datasets': len(datasets),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_url': CATALOGUE_URL,
            'datasets': datasets
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {output_file}")
    
    # Print sample
    if datasets:
        print("\nSample dataset:")
        print(json.dumps(datasets[0], indent=2))

if __name__ == '__main__':
    main()
