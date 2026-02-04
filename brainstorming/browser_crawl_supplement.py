#!/usr/bin/env python3
"""
Browser-based crawler to supplement dictionary and quality information
for datasets that don't have this info in the CKAN datastore.
This script uses Selenium to visit each dataset page and extract information.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pathlib import Path

BASE_URL = "https://open.toronto.ca"

def setup_driver(headless=True):
    """Setup Selenium WebDriver"""
    chrome_options = Options()
    if headless:
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
        return None

def extract_dictionary_from_page(driver):
    """Extract dictionary/columns from the Dictionary tab"""
    dictionary = []
    
    try:
        # Find and click Dictionary tab
        dict_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Dictionary')] | //tab[contains(text(), 'Dictionary')]"))
        )
        driver.execute_script("arguments[0].click();", dict_tab)
        time.sleep(2)
        
        # Find the dictionary table
        try:
            # Try multiple selectors for the table
            table = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, [role='table'], .dictionary-table"))
            )
            
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    col_name = cells[0].text.strip()
                    col_type = cells[1].text.strip() if len(cells) > 1 else ''
                    col_desc = cells[2].text.strip() if len(cells) > 2 else ''
                    
                    if col_name:  # Only add if we have a column name
                        dictionary.append({
                            'column_name': col_name,
                            'type': col_type,
                            'description': col_desc
                        })
        except TimeoutException:
            # Try to find dictionary info in other formats
            dict_panel = driver.find_element(By.CSS_SELECTOR, "[role='tabpanel']:not([hidden])")
            # Could parse text or other structures here
            pass
    
    except TimeoutException:
        pass
    except Exception as e:
        print(f"    Error extracting dictionary: {e}")
    
    return dictionary

def extract_quality_from_page(driver):
    """Extract quality information from the Quality tab"""
    quality = {}
    
    try:
        # Find and click Quality tab
        quality_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Quality')] | //tab[contains(text(), 'Quality')]"))
        )
        driver.execute_script("arguments[0].click();", quality_tab)
        time.sleep(2)
        
        # Extract quality information
        quality_panel = driver.find_element(By.CSS_SELECTOR, "[role='tabpanel']:not([hidden])")
        quality_text = quality_panel.text
        
        # Extract scores using regex
        import re
        
        # Overall score
        score_match = re.search(r'Overall score[:\s]+(\d+)%', quality_text, re.IGNORECASE)
        if score_match:
            quality['overall_score'] = score_match.group(1) + '%'
        
        # Grade
        grade_match = re.search(r'Grade[:\s]+([A-Za-z]+)', quality_text, re.IGNORECASE)
        if grade_match:
            quality['grade'] = grade_match.group(1)
        
        # Freshness
        freshness_match = re.search(r'Freshness[:\s]+(\d+)%', quality_text, re.IGNORECASE)
        if freshness_match:
            quality['freshness'] = freshness_match.group(1) + '%'
        
        # Other metrics
        metrics = ['Metadata', 'Accessibility', 'Completeness', 'Usability']
        for metric in metrics:
            match = re.search(f'{metric}[:\s]+(\\d+)%', quality_text, re.IGNORECASE)
            if match:
                quality[metric.lower()] = match.group(1) + '%'
        
        # Last refreshed
        refreshed_match = re.search(r'Last refreshed[:\s]+([^\n]+)', quality_text, re.IGNORECASE)
        if refreshed_match:
            quality['last_refreshed'] = refreshed_match.group(1).strip()
    
    except TimeoutException:
        pass
    except Exception as e:
        print(f"    Error extracting quality: {e}")
    
    return quality

def enhance_dataset_with_browser(driver, dataset):
    """Enhance a dataset by crawling its page"""
    enhanced = dataset.copy()
    
    # Only enhance if we don't already have dictionary or quality
    needs_dict = not enhanced.get('dictionary')
    needs_quality = not enhanced.get('quality')
    
    if not needs_dict and not needs_quality:
        return enhanced
    
    dataset_url = dataset.get('url', '')
    if not dataset_url:
        return enhanced
    
    try:
        print(f"    Visiting: {dataset_url}")
        driver.get(dataset_url)
        time.sleep(2)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Find the first CSV resource and expand it
        try:
            # Look for resource headings
            resources = driver.find_elements(By.CSS_SELECTOR, "h3, [role='heading'][level='3']")
            
            for resource_elem in resources:
                resource_text = resource_elem.text.strip()
                if not resource_text or 'readme' in resource_text.lower():
                    continue
                
                # Try to click the resource button to expand
                try:
                    resource_button = resource_elem.find_element(By.XPATH, "./following-sibling::button | ./button | ./parent::*/button")
                    if resource_button:
                        driver.execute_script("arguments[0].click();", resource_button)
                        time.sleep(1)
                except:
                    pass
                
                # Extract dictionary if needed
                if needs_dict:
                    dictionary = extract_dictionary_from_page(driver)
                    if dictionary:
                        enhanced['dictionary'] = dictionary
                        needs_dict = False
                        print(f"      Found {len(dictionary)} dictionary columns")
                
                # Extract quality if needed
                if needs_quality:
                    quality = extract_quality_from_page(driver)
                    if quality:
                        enhanced['quality'].update(quality)
                        needs_quality = False
                        print(f"      Found quality information")
                
                # If we got both, we can break
                if not needs_dict and not needs_quality:
                    break
        
        except Exception as e:
            print(f"    Error processing resources: {e}")
    
    except Exception as e:
        print(f"    Error loading page: {e}")
    
    return enhanced

def main():
    input_file = 'toronto_datasets_enhanced.json'
    output_file = 'toronto_datasets_enhanced.json'
    
    # Check if enhanced file exists, otherwise use original
    if not Path(input_file).exists():
        input_file = 'toronto_datasets.json'
        print(f"Enhanced file not found, using {input_file}")
    
    print(f"Loading datasets from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', [])
    
    # Filter datasets that need enhancement
    datasets_needing_dict = [d for d in datasets if not d.get('dictionary')]
    datasets_needing_quality = [d for d in datasets if not d.get('quality')]
    
    datasets_to_enhance = list(set(datasets_needing_dict + datasets_needing_quality))
    
    print(f"Found {len(datasets)} total datasets")
    print(f"Datasets needing dictionary: {len(datasets_needing_dict)}")
    print(f"Datasets needing quality: {len(datasets_needing_quality)}")
    print(f"Total to enhance: {len(datasets_to_enhance)}\n")
    
    if not datasets_to_enhance:
        print("All datasets already have dictionary and quality information!")
        return
    
    # Setup browser
    driver = setup_driver(headless=True)
    if not driver:
        print("Failed to setup browser driver. Please install ChromeDriver.")
        return
    
    try:
        enhanced_datasets = []
        
        for i, dataset in enumerate(datasets, 1):
            if dataset in datasets_to_enhance:
                print(f"[{i}/{len(datasets)}] Enhancing: {dataset['title'][:60]}")
                enhanced = enhance_dataset_with_browser(driver, dataset)
                enhanced_datasets.append(enhanced)
                time.sleep(2)  # Be polite
            else:
                enhanced_datasets.append(dataset)
        
        # Save result
        data['datasets'] = enhanced_datasets
        data['browser_enhanced_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nBrowser enhancement complete! Saved to {output_file}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        # Save what we have
        data['datasets'] = enhanced_datasets + datasets[len(enhanced_datasets):]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
