#!/usr/bin/env python3
"""
Enhance the Toronto datasets JSON with dictionary (columns) and quality information
by crawling each dataset page
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin

BASE_URL = "https://open.toronto.ca"
CKAN_API_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"

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

def get_dataset_details_from_api(dataset_name):
    """Get dataset details from CKAN API"""
    try:
        response = requests.get(
            f"{CKAN_API_URL}/package_show",
            params={'id': dataset_name},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            return data.get('result', {})
    except Exception as e:
        print(f"Error fetching from API for {dataset_name}: {e}")
    return None

def extract_dictionary_from_api(resource_id):
    """Extract dictionary/columns from CKAN API"""
    try:
        response = requests.get(
            f"{CKAN_API_URL}/datastore_search",
            params={
                'resource_id': resource_id,
                'limit': 0  # Just get schema
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            result = data.get('result', {})
            fields = result.get('fields', [])
            
            dictionary = []
            for field in fields:
                dictionary.append({
                    'column_name': field.get('id', ''),
                    'type': field.get('type', ''),
                    'description': field.get('info', {}).get('notes', '') if field.get('info') else ''
                })
            
            return dictionary
    except Exception as e:
        print(f"Error extracting dictionary from API: {e}")
    return None

def extract_quality_from_api(resource_id):
    """Extract quality information from CKAN API"""
    try:
        # Try to get quality information
        response = requests.get(
            f"{CKAN_API_URL}/resource_show",
            params={'id': resource_id},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            resource = data.get('result', {})
            
            quality = {
                'last_refreshed': resource.get('last_modified', ''),
                'format': resource.get('format', ''),
                'size': resource.get('size', ''),
            }
            
            # Check for quality scores in extras
            extras = resource.get('extras', [])
            for extra in extras:
                key = extra.get('key', '')
                value = extra.get('value', '')
                if 'quality' in key.lower() or 'score' in key.lower():
                    quality[key] = value
            
            return quality
    except Exception as e:
        print(f"Error extracting quality from API: {e}")
    return None

def extract_dictionary_from_page(driver, resource_name):
    """Extract dictionary information from the dataset page"""
    dictionary = []
    
    try:
        # Find the resource section
        resource_heading = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//h3[contains(text(), '{resource_name}')]"))
        )
        
        # Click on the resource to expand it
        resource_button = resource_heading.find_element(By.XPATH, "./following-sibling::button | ./button")
        if resource_button:
            driver.execute_script("arguments[0].click();", resource_button)
            time.sleep(1)
        
        # Find and click Dictionary tab
        try:
            dict_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Dictionary')] | //tab[contains(text(), 'Dictionary')]"))
            )
            driver.execute_script("arguments[0].click();", dict_tab)
            time.sleep(2)
            
            # Extract dictionary table
            try:
                dict_table = driver.find_element(By.CSS_SELECTOR, "table, .dictionary-table, [role='table']")
                rows = dict_table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows[1:]:  # Skip header
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        dictionary.append({
                            'column_name': cells[0].text.strip(),
                            'type': cells[1].text.strip() if len(cells) > 1 else '',
                            'description': cells[2].text.strip() if len(cells) > 2 else ''
                        })
            except NoSuchElementException:
                # Try alternative structure
                dict_content = driver.find_element(By.CSS_SELECTOR, "[role='tabpanel']:not([hidden])")
                # Parse content for dictionary info
                pass
        except TimeoutException:
            print(f"  Dictionary tab not found for {resource_name}")
    
    except Exception as e:
        print(f"  Error extracting dictionary: {e}")
    
    return dictionary

def extract_quality_from_page(driver, resource_name):
    """Extract quality information from the dataset page"""
    quality = {}
    
    try:
        # Find the resource section
        resource_heading = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//h3[contains(text(), '{resource_name}')]"))
        )
        
        # Click on the resource to expand it
        resource_button = resource_heading.find_element(By.XPATH, "./following-sibling::button | ./button")
        if resource_button:
            driver.execute_script("arguments[0].click();", resource_button)
            time.sleep(1)
        
        # Find and click Quality tab
        try:
            quality_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Quality')] | //tab[contains(text(), 'Quality')]"))
            )
            driver.execute_script("arguments[0].click();", quality_tab)
            time.sleep(2)
            
            # Extract quality information
            quality_panel = driver.find_element(By.CSS_SELECTOR, "[role='tabpanel']:not([hidden])")
            
            # Look for quality scores
            quality_text = quality_panel.text
            
            # Extract overall score
            if 'Overall score' in quality_text or 'score' in quality_text.lower():
                # Try to find score percentage
                import re
                score_match = re.search(r'(\d+)%', quality_text)
                if score_match:
                    quality['overall_score'] = score_match.group(1) + '%'
            
            # Extract grade
            grade_match = re.search(r'Grade[:\s]+([A-Za-z]+)', quality_text)
            if grade_match:
                quality['grade'] = grade_match.group(1)
            
            # Extract freshness
            freshness_match = re.search(r'Freshness[:\s]+(\d+)%', quality_text)
            if freshness_match:
                quality['freshness'] = freshness_match.group(1) + '%'
            
            # Extract other metrics
            metrics = ['Metadata', 'Accessibility', 'Completeness', 'Usability']
            for metric in metrics:
                match = re.search(f'{metric}[:\s]+(\\d+)%', quality_text)
                if match:
                    quality[metric.lower()] = match.group(1) + '%'
            
        except TimeoutException:
            print(f"  Quality tab not found for {resource_name}")
    
    except Exception as e:
        print(f"  Error extracting quality: {e}")
    
    return quality

def enhance_dataset(driver, dataset, use_api=True):
    """Enhance a single dataset with dictionary and quality information"""
    print(f"Processing: {dataset['title']}")
    
    enhanced = dataset.copy()
    enhanced['dictionary'] = []
    enhanced['quality'] = {}
    enhanced['resources'] = []
    
    dataset_name = dataset.get('name', '')
    dataset_url = dataset.get('url', '')
    
    if use_api and dataset_name:
        # Try API first
        api_data = get_dataset_details_from_api(dataset_name)
        if api_data:
            resources = api_data.get('resources', [])
            
            for resource in resources:
                resource_info = {
                    'name': resource.get('name', ''),
                    'format': resource.get('format', ''),
                    'url': resource.get('url', ''),
                    'size': resource.get('size', ''),
                    'last_modified': resource.get('last_modified', '')
                }
                enhanced['resources'].append(resource_info)
                
                # If it's a CSV resource, try to get dictionary
                if 'CSV' in resource.get('format', '').upper():
                    resource_id = resource.get('id', '')
                    if resource_id:
                        # Try to get dictionary from datastore
                        dictionary = extract_dictionary_from_api(resource_id)
                        if dictionary:
                            enhanced['dictionary'].extend(dictionary)
                        
                        # Get quality info
                        quality = extract_quality_from_api(resource_id)
                        if quality:
                            enhanced['quality'].update(quality)
    
    # If API didn't work or we need more info, use browser
    if not enhanced['dictionary'] or not enhanced['quality']:
        try:
            driver.get(dataset_url)
            time.sleep(2)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            # Find CSV resources
            resources = driver.find_elements(By.CSS_SELECTOR, "h3, [role='heading'][level='3']")
            
            for resource_elem in resources:
                resource_text = resource_elem.text.strip()
                if not resource_text or 'readme' in resource_text.lower():
                    continue
                
                # Try to extract dictionary
                if not enhanced['dictionary']:
                    dict_info = extract_dictionary_from_page(driver, resource_text)
                    if dict_info:
                        enhanced['dictionary'] = dict_info
                
                # Try to extract quality
                if not enhanced['quality']:
                    quality_info = extract_quality_from_page(driver, resource_text)
                    if quality_info:
                        enhanced['quality'] = quality_info
                
                # If we got both, we can break
                if enhanced['dictionary'] and enhanced['quality']:
                    break
        
        except Exception as e:
            print(f"  Error processing page: {e}")
    
    return enhanced

def main():
    # Load existing JSON
    input_file = 'toronto_datasets.json'
    output_file = 'toronto_datasets_enhanced.json'
    
    print(f"Loading datasets from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', [])
    total = len(datasets)
    print(f"Found {total} datasets to enhance")
    
    # Setup driver
    driver = None
    try:
        driver = setup_driver()
        print("Browser driver initialized")
        
        enhanced_datasets = []
        
        for i, dataset in enumerate(datasets, 1):
            print(f"\n[{i}/{total}] ", end='')
            try:
                enhanced = enhance_dataset(driver, dataset, use_api=True)
                enhanced_datasets.append(enhanced)
                
                # Save progress every 10 datasets
                if i % 10 == 0:
                    print(f"\nSaving progress... ({i}/{total})")
                    temp_data = data.copy()
                    temp_data['datasets'] = enhanced_datasets + datasets[i:]
                    with open(output_file + '.tmp', 'w', encoding='utf-8') as f:
                        json.dump(temp_data, f, indent=2, ensure_ascii=False)
                
                time.sleep(1)  # Be polite with rate limiting
                
            except Exception as e:
                print(f"Error processing dataset {i}: {e}")
                enhanced_datasets.append(dataset)  # Keep original if enhancement fails
        
        # Save final result
        data['datasets'] = enhanced_datasets
        data['enhanced_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n\nEnhancement complete! Saved to {output_file}")
        print(f"Enhanced {len(enhanced_datasets)} datasets")
        
        # Show sample
        if enhanced_datasets:
            sample = enhanced_datasets[0]
            print("\nSample enhanced dataset:")
            print(f"  Title: {sample['title']}")
            print(f"  Dictionary entries: {len(sample.get('dictionary', []))}")
            print(f"  Quality info: {bool(sample.get('quality', {}))}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main()
