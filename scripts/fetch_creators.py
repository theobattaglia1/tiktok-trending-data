#!/usr/bin/env python3
"""
TikTok Creators Data Fetcher
Specialized script for fetching and analyzing creator/artist trends.
"""

import requests
import json
import os
import time
import random
from datetime import datetime
from typing import Dict, List, Optional

class TikTokCreatorsFetcher:
    def __init__(self, data_dir: str = 'data/snapshots'):
        self.data_dir = data_dir
        self.session = requests.Session()
        
    def get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers for requests."""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
    def fetch_trending_creators(self) -> Optional[Dict]:
        """Fetch trending creators data."""
        # Note: In a real implementation, you would use TikTok's actual creators API
        # This is a placeholder for the structure
        
        print("Fetching trending creators...")
        
        # Mock data for demonstration with A&R focus
        mock_creators = {
            'creators': [
                {
                    'id': 'creator_001',
                    'username': 'risingartist2025',
                    'display_name': 'Rising Artist',
                    'follower_count': 125000,
                    'following_count': 450,
                    'video_count': 89,
                    'total_likes': 2500000,
                    'growth_rate': 185.5,
                    'category': 'music',
                    'location': 'Los Angeles, CA',
                    'verified': False,
                    'recent_viral_videos': 3,
                    'avg_views_per_video': 85000,
                    'engagement_rate': 8.5,
                    'a_r_score': 92.3,  # A&R relevance score
                    'notable_sounds': ['original_song_001', 'cover_002'],
                    'collaboration_potential': 'high'
                },
                {
                    'id': 'creator_002',
                    'username': 'indiemusician',
                    'display_name': 'Indie Musician',
                    'follower_count': 67000,
                    'following_count': 320,
                    'video_count': 45,
                    'total_likes': 950000,
                    'growth_rate': 156.8,
                    'category': 'music',
                    'location': 'Nashville, TN',
                    'verified': False,
                    'recent_viral_videos': 2,
                    'avg_views_per_video': 45000,
                    'engagement_rate': 12.3,
                    'a_r_score': 87.6,
                    'notable_sounds': ['acoustic_demo_001'],
                    'collaboration_potential': 'medium'
                },
                {
                    'id': 'creator_003',
                    'username': 'newtalent2025',
                    'display_name': 'New Talent',
                    'follower_count': 28000,
                    'following_count': 180,
                    'video_count': 23,
                    'total_likes': 350000,
                    'growth_rate': 245.2,
                    'category': 'music',
                    'location': 'Atlanta, GA',
                    'verified': False,
                    'recent_viral_videos': 1,
                    'avg_views_per_video': 32000,
                    'engagement_rate': 15.7,
                    'a_r_score': 95.1,  # High score due to high growth + engagement
                    'notable_sounds': ['rap_freestyle_001'],
                    'collaboration_potential': 'very_high'
                }
            ],
            'timestamp': datetime.now().isoformat(),
            'total_count': 3,
            'analysis': {
                'fastest_growing': 'newtalent2025',
                'highest_engagement': 'newtalent2025',
                'top_a_r_prospect': 'newtalent2025',
                'trending_genres': ['hip-hop', 'indie', 'pop'],
                'emerging_markets': ['Atlanta', 'Nashville', 'Los Angeles']
            }
        }
        
        return mock_creators
        
    def save_creators_data(self, data: Dict) -> str:
        """Save creators data to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save timestamped version
        filename = f"creators_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        os.makedirs(self.data_dir, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Save as latest
        latest_file = "creators_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return filepath
        
    def run(self):
        """Run the creators fetcher."""
        creators_data = self.fetch_trending_creators()
        
        if creators_data:
            saved_file = self.save_creators_data(creators_data)
            print(f"✓ Saved creators data to {saved_file}")
            print(f"Found {len(creators_data.get('creators', []))} trending creators")
            
            # Print A&R insights
            analysis = creators_data.get('analysis', {})
            if analysis:
                print(f"\nA&R Insights:")
                print(f"Top A&R Prospect: @{analysis.get('top_a_r_prospect', 'N/A')}")
                print(f"Fastest Growing: @{analysis.get('fastest_growing', 'N/A')}")
                print(f"Trending Genres: {', '.join(analysis.get('trending_genres', []))}")
                
            # Show top creators by A&R score
            creators = creators_data.get('creators', [])
            if creators:
                top_creators = sorted(creators, key=lambda x: x.get('a_r_score', 0), reverse=True)
                print(f"\nTop A&R Prospects:")
                for i, creator in enumerate(top_creators[:3], 1):
                    print(f"{i}. @{creator.get('username', 'Unknown')} - Score: {creator.get('a_r_score', 0):.1f}")
                    print(f"   Growth: {creator.get('growth_rate', 0):.1f}% | Followers: {creator.get('follower_count', 0):,}")
        else:
            print("✗ Failed to fetch creators data")

def main():
    fetcher = TikTokCreatorsFetcher()
    fetcher.run()

if __name__ == '__main__':
    main()