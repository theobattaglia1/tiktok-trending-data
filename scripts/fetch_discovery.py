#!/usr/bin/env python3
"""
Enhanced TikTok Discovery Data Fetcher
Fetches trending data from TikTok discovery endpoints with robust error handling and user-agent rotation.
"""

import requests
import json
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

# User agent rotation for better reliability
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

# TikTok discovery endpoints
DISCOVERY_ENDPOINTS = {
    'discover_www': 'https://www.tiktok.com/node/share/discover',
    'discover_us': 'https://us.tiktok.com/node/share/discover', 
    'discover_list_www': 'https://www.tiktok.com/node/share/discover/list',
    'discover_list_us': 'https://us.tiktok.com/node/share/discover/list',
    'api_feed': 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?version_name=26.1.3&version_code=260103&build_number=26.1.3&manifest_version_code=260103&update_version_code=260103&ts=1684811896&device_brand=Google&device_type=Pixel+7&device_platform=android&resolution=1080*2400&dpi=680&os_version=10&os_api=29&carrier_region=US&sys_region=US&region=US&app_name=trill&app_language=en&language=en&timezone_name=America%2FNew_York&timezone_offset=-14400&channel=googleplay&ac=wifi&mcc_mnc=310260&is_my_cn=0&aid=1180&ssmix=a'
}

class TikTokDiscoveryFetcher:
    def __init__(self, data_dir: str = 'data/snapshots'):
        self.data_dir = data_dir
        self.session = requests.Session()
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests."""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def fetch_endpoint(self, name: str, url: str, retries: int = 3) -> Optional[Dict]:
        """Fetch data from a single endpoint with retry logic."""
        for attempt in range(retries):
            try:
                headers = self.get_random_headers()
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    return data
                except json.JSONDecodeError:
                    print(f"Warning: {name} returned non-JSON data")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {name}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(1, 3))  # Random delay between retries
                    
        print(f"Failed to fetch {name} after {retries} attempts")
        return None
        
    def save_data(self, name: str, data: Dict) -> str:
        """Save data to timestamped file and latest file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save timestamped version
        timestamped_file = os.path.join(self.data_dir, f"{name}_{timestamp}.json")
        with open(timestamped_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Save as latest (for backward compatibility)
        latest_file = f"{name}.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return timestamped_file
        
    def extract_trending_items(self, data: Dict, source: str) -> List[Dict]:
        """Extract trending items from discovery data for analysis."""
        trending_items = []
        timestamp = datetime.now().isoformat()
        
        try:
            if 'body' in data and isinstance(data['body'], list):
                for section in data['body']:
                    if 'exploreList' in section:
                        for explore_item in section['exploreList']:
                            if 'cardItem' in explore_item:
                                card = explore_item['cardItem']
                                item = {
                                    'timestamp': timestamp,
                                    'source': source,
                                    'id': card.get('id'),
                                    'type': card.get('type'),
                                    'title': card.get('title', ''),
                                    'cover': card.get('cover', ''),
                                    'desc': card.get('desc', ''),
                                    'author': card.get('author', {}),
                                    'stats': card.get('stats', {}),
                                    'music': card.get('music', {}),
                                    'hashtags': self.extract_hashtags(card.get('desc', '')),
                                    'raw_data': card
                                }
                                trending_items.append(item)
        except Exception as e:
            print(f"Error extracting trending items from {source}: {e}")
            
        return trending_items
        
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags
        
    def fetch_all_discovery_data(self) -> Dict[str, Dict]:
        """Fetch data from all discovery endpoints."""
        results = {}
        all_trending_items = []
        
        print("Fetching TikTok discovery data...")
        
        for name, url in DISCOVERY_ENDPOINTS.items():
            print(f"Fetching {name}...")
            data = self.fetch_endpoint(name, url)
            
            if data:
                # Save raw data
                saved_file = self.save_data(name, data)
                results[name] = {
                    'data': data,
                    'file': saved_file,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Extract trending items for analysis
                trending_items = self.extract_trending_items(data, name)
                all_trending_items.extend(trending_items)
                
                print(f"✓ Saved {name} ({len(trending_items)} trending items)")
            else:
                print(f"✗ Failed to fetch {name}")
                
            # Rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
        # Save aggregated trending items
        if all_trending_items:
            trending_file = self.save_data('trending_items', {
                'items': all_trending_items,
                'count': len(all_trending_items),
                'timestamp': datetime.now().isoformat()
            })
            print(f"✓ Saved {len(all_trending_items)} trending items to {trending_file}")
            
        return results

def main():
    fetcher = TikTokDiscoveryFetcher()
    results = fetcher.fetch_all_discovery_data()
    
    success_count = len([r for r in results.values() if r is not None])
    total_count = len(DISCOVERY_ENDPOINTS)
    
    print(f"\nFetch complete: {success_count}/{total_count} endpoints successful")
    
    if success_count == 0:
        exit(1)  # Exit with error if no endpoints were successful

if __name__ == '__main__':
    main()