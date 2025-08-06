#!/usr/bin/env python3
"""
TikTok Trends Analytics Processor
Processes raw trending data and feeds it into the analytics database.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.database import TrendsDatabase, ViralityStage

class TrendsAnalytics:
    def __init__(self, db_path: str = 'analysis/trends.db'):
        self.db = TrendsDatabase(db_path)
        
    def process_trending_items_file(self, file_path: str) -> int:
        """Process a trending items JSON file and insert into database."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'items' not in data:
                print(f"No 'items' key found in {file_path}")
                return 0
                
            items = data['items']
            processed_count = 0
            
            for item in items:
                if self.db.insert_or_update_trend(item):
                    processed_count += 1
                    
            print(f"Processed {processed_count}/{len(items)} items from {file_path}")
            return processed_count
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return 0
            
    def process_all_trending_files(self, data_dir: str = 'data/snapshots') -> int:
        """Process all trending items files in the data directory."""
        total_processed = 0
        
        # Look for trending items files
        pattern = "trending_items_*.json"
        data_path = Path(data_dir)
        
        if not data_path.exists():
            print(f"Data directory {data_dir} does not exist")
            return 0
            
        trending_files = list(data_path.glob(pattern))
        
        # Also check for the main trending_items.json file
        main_file = Path("trending_items.json")
        if main_file.exists():
            trending_files.append(main_file)
            
        if not trending_files:
            print(f"No trending items files found in {data_dir}")
            return 0
            
        print(f"Found {len(trending_files)} trending items files to process")
        
        for file_path in sorted(trending_files):
            processed = self.process_trending_items_file(str(file_path))
            total_processed += processed
            
        return total_processed
        
    def identify_breakout_trends(self, hours: int = 6, min_growth_rate: float = 100.0) -> list:
        """Identify trends that are breaking out and should trigger alerts."""
        breakout_trends = self.db.get_breakout_trends(hours=hours, min_growth_rate=min_growth_rate)
        
        # Filter for A&R relevant trends (new artists, rising sounds)
        ar_relevant = []
        for trend in breakout_trends:
            # Focus on trends from newer or smaller creators
            author = trend.get('author', '')
            view_count = trend.get('view_count', 0)
            
            # Criteria for A&R relevance:
            # 1. High growth rate
            # 2. Not already massive (gives room for discovery)
            # 3. Has music/sound component
            if (trend.get('growth_rate', 0) > min_growth_rate and 
                view_count < 500000 and  # Not already massive
                trend.get('music_id')):  # Has music component
                ar_relevant.append(trend)
                
        return ar_relevant
        
    def generate_analytics_report(self) -> dict:
        """Generate comprehensive analytics report."""
        summary = self.db.get_analytics_summary()
        
        # Get breakout trends for different time windows
        breakout_1h = self.identify_breakout_trends(hours=1, min_growth_rate=200.0)
        breakout_6h = self.identify_breakout_trends(hours=6, min_growth_rate=100.0)
        breakout_24h = self.identify_breakout_trends(hours=24, min_growth_rate=50.0)
        
        # Get trends by stage
        new_trends = self.db.get_trending_by_stage(ViralityStage.NEW, limit=20)
        early_traction = self.db.get_trending_by_stage(ViralityStage.EARLY_TRACTION, limit=20)
        steady_trends = self.db.get_trending_by_stage(ViralityStage.STEADY, limit=20)
        massive_trends = self.db.get_trending_by_stage(ViralityStage.MASSIVE, limit=20)
        
        report = {
            'summary': summary,
            'breakout_trends': {
                '1_hour': breakout_1h,
                '6_hours': breakout_6h,
                '24_hours': breakout_24h
            },
            'trends_by_stage': {
                'new': new_trends,
                'early_traction': early_traction,
                'steady': steady_trends,
                'massive': massive_trends
            },
            'ar_alerts': {
                'high_priority': breakout_1h,  # Very recent breakouts
                'medium_priority': [t for t in breakout_6h if t not in breakout_1h],
                'low_priority': [t for t in breakout_24h if t not in breakout_6h]
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return report
        
    def save_analytics_report(self, report: dict, output_path: str = 'analysis/latest_report.json'):
        """Save analytics report to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Analytics report saved to {output_path}")
        
    def print_summary(self, report: dict):
        """Print a summary of the analytics report."""
        summary = report['summary']
        breakouts = report['breakout_trends']
        alerts = report['ar_alerts']
        
        print("\n" + "="*60)
        print("TIKTOK TRENDS ANALYTICS SUMMARY")
        print("="*60)
        
        print(f"Total Trends: {summary['total_trends']}")
        print(f"Recent Activity (24h): {summary['recent_trends_24h']}")
        
        print(f"\nTrends by Virality Stage:")
        for stage, count in summary['stage_counts'].items():
            print(f"  {stage}: {count}")
            
        print(f"\nBreakout Trends:")
        print(f"  Last 1 hour: {len(breakouts['1_hour'])}")
        print(f"  Last 6 hours: {len(breakouts['6_hours'])}")
        print(f"  Last 24 hours: {len(breakouts['24_hours'])}")
        
        print(f"\nA&R Alerts:")
        print(f"  High Priority: {len(alerts['high_priority'])}")
        print(f"  Medium Priority: {len(alerts['medium_priority'])}")
        print(f"  Low Priority: {len(alerts['low_priority'])}")
        
        if alerts['high_priority']:
            print(f"\nHigh Priority Breakouts:")
            for trend in alerts['high_priority'][:3]:  # Show top 3
                print(f"  • {trend.get('title', 'Unknown')} by {trend.get('author', 'Unknown')}")
                print(f"    Growth: {trend.get('growth_rate', 0):.1f}% | Views: {trend.get('view_count', 0):,}")
                
        print(f"\nTop Hashtags (24h):")
        for hashtag in summary['top_hashtags'][:5]:
            print(f"  #{hashtag['hashtag']}: {hashtag['usage_count']} uses")
            
        print("="*60)

def main():
    """Main analytics processing function."""
    analytics = TrendsAnalytics()
    
    # Process all trending data files
    print("Processing trending data files...")
    processed_count = analytics.process_all_trending_files()
    
    if processed_count == 0:
        print("No trends were processed. Make sure trending data files exist.")
        return
        
    # Generate analytics report
    print(f"\nGenerating analytics report for {processed_count} processed trends...")
    report = analytics.generate_analytics_report()
    
    # Save report
    analytics.save_analytics_report(report)
    
    # Print summary
    analytics.print_summary(report)
    
    return report

if __name__ == '__main__':
    main()