#!/usr/bin/env python3
"""
Test script to enhance a few datasets and see the structure
"""

import json
import requests
from datetime import datetime

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
    except Exception as e:
        print(f"Error getting dictionary: {e}")
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
        print(f"Error: {e}")
    return None

def enhance_dataset_info(dataset):
    """Enhance a dataset with dictionary and quality info"""
    enhanced = dataset.copy()
    enhanced['dictionary'] = []
    enhanced['quality'] = {}
    enhanced['resources_detail'] = []
    
    dataset_name = dataset.get('name', '')
    if not dataset_name:
        return enhanced
    
    print(f"Processing: {dataset['title']}")
    
    # Get full dataset info
    api_data = get_dataset_full_info(dataset_name)
    if not api_data:
        return enhanced
    
    resources = api_data.get('resources', [])
    
    for resource in resources:
        resource_id = resource.get('id', '')
        resource_format = resource.get('format', '').upper()
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
        
        # If it's CSV, try to get dictionary
        if 'CSV' in resource_format and resource_id:
            print(f"  Getting dictionary for resource: {resource_name}")
            dictionary = get_resource_dictionary(resource_id)
            if dictionary:
                enhanced['dictionary'].extend(dictionary)
                print(f"  Found {len(dictionary)} columns")
        
        # Extract quality info from resource
        if resource_id:
            # Check for quality-related fields
            quality_info = {}
            
            # Get resource details
            try:
                res_response = requests.get(
                    f"{CKAN_API_URL}/resource_show",
                    params={'id': resource_id},
                    timeout=30
                )
                res_response.raise_for_status()
                res_data = res_response.json()
                
                if res_data.get('success'):
                    res_result = res_data.get('result', {})
                    quality_info = {
                        'last_modified': res_result.get('last_modified', ''),
                        'created': res_result.get('created', ''),
                        'format': res_result.get('format', ''),
                        'size': res_result.get('size', ''),
                    }
            except:
                pass
            
            if quality_info:
                enhanced['quality'] = quality_info
    
    return enhanced

def main():
    # Load existing JSON
    input_file = 'toronto_datasets.json'
    output_file = 'toronto_datasets_enhanced.json'
    
    print("Loading datasets...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    datasets = data.get('datasets', [])
    
    # Test with first 3 datasets
    test_datasets = datasets[:3]
    print(f"Testing with {len(test_datasets)} datasets\n")
    
    enhanced_datasets = []
    for i, dataset in enumerate(test_datasets, 1):
        print(f"[{i}/{len(test_datasets)}] ", end='')
        enhanced = enhance_dataset_info(dataset)
        enhanced_datasets.append(enhanced)
        print()
    
    # Save test result
    test_data = data.copy()
    test_data['datasets'] = enhanced_datasets
    test_data['test_mode'] = True
    test_data['enhanced_at'] = datetime.now().isoformat()
    
    with open('test_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nTest complete! Saved to test_enhanced.json")
    
    # Show sample
    if enhanced_datasets:
        sample = enhanced_datasets[0]
        print(f"\nSample enhanced dataset: {sample['title']}")
        print(f"  Dictionary columns: {len(sample.get('dictionary', []))}")
        if sample.get('dictionary'):
            print(f"  First column: {sample['dictionary'][0]}")
        print(f"  Quality info: {bool(sample.get('quality', {}))}")
        if sample.get('quality'):
            print(f"  Quality details: {sample['quality']}")

if __name__ == '__main__':
    main()
