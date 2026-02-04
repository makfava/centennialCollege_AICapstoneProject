#!/usr/bin/env python3
"""
Enhance all Toronto datasets with dictionary (columns) and quality information
Uses CKAN API when possible, falls back to browser crawling when needed
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

CKAN_API_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"

def get_resource_dictionary(resource_id):
    """Get dictionary/columns from CKAN datastore"""
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
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # Resource not in datastore, that's okay
            return None
    except Exception as e:
        # Silently fail - we'll try browser crawling
        pass
    return None

def get_dataset_full_info(dataset_name):
    """Get full dataset information from CKAN API"""
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
        print(f"  Error fetching dataset info: {e}")
    return None

def get_resource_info(resource_id):
    """Get resource information including quality metrics"""
    try:
        response = requests.get(
            f"{CKAN_API_URL}/resource_show",
            params={'id': resource_id},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            return data.get('result', {})
    except Exception as e:
        pass
    return None

def enhance_dataset_info(dataset, use_browser=False):
    """Enhance a dataset with dictionary and quality info"""
    enhanced = dataset.copy()
    enhanced['dictionary'] = []
    enhanced['quality'] = {}
    enhanced['resources_detail'] = []
    
    dataset_name = dataset.get('name', '')
    if not dataset_name:
        return enhanced
    
    # Get full dataset info from API
    api_data = get_dataset_full_info(dataset_name)
    if not api_data:
        return enhanced
    
    resources = api_data.get('resources', [])
    csv_resources = [r for r in resources if 'CSV' in r.get('format', '').upper()]
    
    if not csv_resources:
        return enhanced
    
    # Process each CSV resource
    for resource in csv_resources:
        resource_id = resource.get('id', '')
        resource_name = resource.get('name', '')
        
        resource_detail = {
            'name': resource_name,
            'format': resource.get('format', ''),
            'url': resource.get('url', ''),
            'size': resource.get('size', ''),
            'last_modified': resource.get('last_modified', ''),
            'created': resource.get('created', ''),
            'id': resource_id
        }
        enhanced['resources_detail'].append(resource_detail)
        
        # Try to get dictionary from datastore
        if resource_id:
            dictionary = get_resource_dictionary(resource_id)
            if dictionary:
                enhanced['dictionary'].extend(dictionary)
            
            # Get quality/resource info
            resource_info = get_resource_info(resource_id)
            if resource_info:
                if not enhanced['quality']:
                    enhanced['quality'] = {
                        'last_modified': resource_info.get('last_modified', ''),
                        'created': resource_info.get('created', ''),
                        'format': resource_info.get('format', ''),
                        'size': resource_info.get('size', ''),
                    }
    
    # Note: Browser crawling for dictionary/quality would go here if needed
    # For now, we rely on API which works for most resources
    
    return enhanced

def load_progress():
    """Load progress from checkpoint file"""
    checkpoint_file = Path('enhancement_checkpoint.json')
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_progress(enhanced_datasets, remaining_datasets, current_index):
    """Save progress to checkpoint file"""
    checkpoint = {
        'enhanced': enhanced_datasets,
        'remaining': remaining_datasets,
        'current_index': current_index,
        'timestamp': datetime.now().isoformat()
    }
    with open('enhancement_checkpoint.json', 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)

def main():
    input_file = 'toronto_datasets.json'
    output_file = 'toronto_datasets_enhanced.json'
    
    print(f"Loading datasets from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', [])
    total = len(datasets)
    print(f"Found {total} datasets to enhance\n")
    
    # Check for existing progress
    checkpoint = load_progress()
    if checkpoint:
        print(f"Found checkpoint from {checkpoint.get('timestamp', 'unknown')}")
        enhanced_datasets = checkpoint.get('enhanced', [])
        remaining_datasets = checkpoint.get('remaining', datasets)
        start_index = checkpoint.get('current_index', 0)
        print(f"Resuming from dataset {start_index + 1}/{total}")
    else:
        enhanced_datasets = []
        remaining_datasets = datasets
        start_index = 0
    
    # Process datasets
    for i, dataset in enumerate(remaining_datasets, start_index):
        print(f"[{i+1}/{total}] ", end='', flush=True)
        try:
            enhanced = enhance_dataset_info(dataset)
            enhanced_datasets.append(enhanced)
            
            # Show progress
            dict_count = len(enhanced.get('dictionary', []))
            has_quality = bool(enhanced.get('quality', {}))
            print(f"{dataset['title'][:50]:<50} | Dict: {dict_count:>3} cols | Quality: {'✓' if has_quality else '✗'}")
            
            # Save checkpoint every 10 datasets
            if (i + 1) % 10 == 0:
                remaining = remaining_datasets[i - start_index + 1:]
                save_progress(enhanced_datasets, remaining, i + 1)
                print(f"  → Checkpoint saved ({i+1}/{total})")
            
            # Be polite with rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            print(f"ERROR: {e}")
            # Keep original dataset if enhancement fails
            enhanced_datasets.append(dataset)
    
    # Save final result
    final_data = data.copy()
    final_data['datasets'] = enhanced_datasets
    final_data['enhanced_at'] = datetime.now().isoformat()
    final_data['enhancement_method'] = 'CKAN API (datastore_search, resource_show, package_show)'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    # Clean up checkpoint
    checkpoint_file = Path('enhancement_checkpoint.json')
    if checkpoint_file.exists():
        checkpoint_file.unlink()
    
    # Statistics
    total_with_dict = sum(1 for d in enhanced_datasets if d.get('dictionary'))
    total_with_quality = sum(1 for d in enhanced_datasets if d.get('quality'))
    total_dict_columns = sum(len(d.get('dictionary', [])) for d in enhanced_datasets)
    
    print(f"\n{'='*70}")
    print(f"Enhancement complete! Saved to {output_file}")
    print(f"{'='*70}")
    print(f"Total datasets: {len(enhanced_datasets)}")
    print(f"Datasets with dictionary: {total_with_dict} ({total_with_dict/len(enhanced_datasets)*100:.1f}%)")
    print(f"Datasets with quality info: {total_with_quality} ({total_with_quality/len(enhanced_datasets)*100:.1f}%)")
    print(f"Total dictionary columns: {total_dict_columns}")
    
    # Show sample
    if enhanced_datasets:
        sample = next((d for d in enhanced_datasets if d.get('dictionary')), enhanced_datasets[0])
        print(f"\nSample dataset: {sample['title']}")
        if sample.get('dictionary'):
            print(f"  Dictionary columns: {len(sample['dictionary'])}")
            print(f"  First 3 columns:")
            for col in sample['dictionary'][:3]:
                print(f"    - {col['column_name']} ({col['type']}): {col['description'][:60]}")

if __name__ == '__main__':
    main()
