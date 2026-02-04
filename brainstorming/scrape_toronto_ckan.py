#!/usr/bin/env python3
"""
Scrape Toronto Open Data CSV datasets using CKAN API
Toronto Open Data uses CKAN, which typically has an API endpoint
"""

import requests
import json
import time
from datetime import datetime

# CKAN API endpoint (common pattern for CKAN installations)
CKAN_API_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
BASE_URL = "https://open.toronto.ca"

def get_all_datasets_with_csv():
    """Get all datasets that have CSV format using CKAN API"""
    all_datasets = []
    offset = 0
    limit = 100  # CKAN typically allows up to 1000, but 100 is safer
    
    print("Fetching datasets from CKAN API...")
    
    while True:
        try:
            # CKAN package_search action - request more fields
            params = {
                'q': 'res_format:CSV',  # Search for CSV format
                'rows': limit,
                'start': offset,
                'facet': 'true',
                'facet.field': ['organization', 'groups', 'tags', 'res_format', 'license_id'],
                'include_private': 'false'
            }
            
            response = requests.get(
                f"{CKAN_API_URL}/package_search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                print(f"API returned success=False: {data}")
                break
            
            results = data.get('result', {})
            datasets = results.get('results', [])
            count = results.get('count', 0)
            
            print(f"Fetched {len(datasets)} datasets (offset {offset}, total: {count})")
            
            if not datasets:
                break
            
            # Process each dataset
            for i, dataset in enumerate(datasets):
                dataset_info = extract_dataset_info(dataset)
                if dataset_info:
                    all_datasets.append(dataset_info)
                # Show progress every 10 datasets
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(datasets)} datasets...")
            
            # Check if we've got all datasets
            if offset + len(datasets) >= count:
                break
            
            offset += limit
            time.sleep(0.5)  # Be polite with rate limiting
            
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            break
        except Exception as e:
            print(f"Error processing data: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return all_datasets

def extract_dataset_info(dataset):
    """Extract relevant information from CKAN dataset"""
    try:
        # Get title and URL
        title = dataset.get('title', '')
        name = dataset.get('name', '')
        dataset_url = f"{BASE_URL}/dataset/{name}/" if name else ''
        
        # Get description
        notes = dataset.get('notes', '')
        
        # Get metadata from extras
        metadata = {}
        extras = dataset.get('extras', [])
        extras_dict = {}
        for extra in extras:
            key = extra.get('key', '')
            value = extra.get('value', '')
            extras_dict[key] = value
            
            # Map common CKAN extra fields
            if key == 'refresh_rate':
                metadata['refresh_rate'] = value
            elif key == 'date_modified' or key == 'metadata_modified':
                metadata['last_refreshed'] = value
            elif key == 'dataset_category':
                metadata['type'] = value
        
        # Try to get refresh rate from other fields
        if not metadata.get('refresh_rate'):
            # Check common variations
            for key in ['refresh_rate', 'update_frequency', 'frequency']:
                if key in extras_dict:
                    metadata['refresh_rate'] = extras_dict[key]
                    break
        
        # Get last modified date
        if not metadata.get('last_refreshed'):
            metadata_modified = dataset.get('metadata_modified', '')
            if metadata_modified:
                # Format date
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(metadata_modified.replace('Z', '+00:00'))
                    metadata['last_refreshed'] = dt.strftime('%b %d, %Y')
                except:
                    metadata['last_refreshed'] = metadata_modified
        
        # Get organization (publisher)
        organization = dataset.get('organization', {})
        publisher = organization.get('title', '') if organization else ''
        
        # Get groups (topics)
        groups = dataset.get('groups', [])
        topics = [g.get('title', '') for g in groups if g.get('title')]
        
        # Get tags
        tags = dataset.get('tags', [])
        tag_names = [t.get('name', '') for t in tags if t.get('name')]
        
        # Get resources and check for CSV format
        resources = dataset.get('resources', [])
        formats = []
        has_csv = False
        for resource in resources:
            fmt = resource.get('format', '').upper()
            if fmt:
                formats.append(fmt)
                if 'CSV' in fmt:
                    has_csv = True
        
        # Only include if it has CSV
        if not has_csv:
            return None
        
        # Get type - check dataset_category or use default
        dataset_type = metadata.get('type', '')
        if not dataset_type:
            # Infer from resources or use default
            dataset_type = 'Table'  # Default for CSV datasets
        
        # Get license
        license_title = dataset.get('license_title', '')
        if not license_title:
            license_id = dataset.get('license_id', '')
            if license_id:
                license_title = license_id
        
        return {
            'title': title,
            'url': dataset_url,
            'description': notes.strip() if notes else '',
            'refresh_rate': metadata.get('refresh_rate', ''),
            'last_refreshed': metadata.get('last_refreshed', ''),
            'publisher': publisher,
            'type': dataset_type,
            'formats': ' | '.join(sorted(set(formats))),
            'topics': ' | '.join(topics) if topics else '',
            'tags': ' | '.join(tag_names) if tag_names else '',
            'license': license_title if license_title else None,
            'name': name  # CKAN internal name
        }
    except Exception as e:
        print(f"Error extracting dataset info: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("Starting to scrape Toronto Open Data CSV datasets using CKAN API...")
    
    datasets = get_all_datasets_with_csv()
    
    print(f"\nTotal datasets with CSV format: {len(datasets)}")
    
    # Save to JSON
    output_file = 'toronto_datasets.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_datasets': len(datasets),
            'scraped_at': datetime.now().isoformat(),
            'source_url': f"{BASE_URL}/catalogue/?formats=CSV",
            'api_endpoint': CKAN_API_URL,
            'datasets': datasets
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Data saved to {output_file}")
    
    # Print sample
    if datasets:
        print("\nSample dataset:")
        print(json.dumps(datasets[0], indent=2))
    else:
        print("\nNo datasets found. The API endpoint might be different.")
        print("Trying alternative approach...")

if __name__ == '__main__':
    main()
