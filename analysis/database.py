#!/usr/bin/env python3
"""
TikTok Trends Database Schema and Management
Creates and manages SQLite database for trend analysis and virality classification.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ViralityStage(Enum):
    NEW = "New"
    EARLY_TRACTION = "Early Traction"
    STEADY = "Steady"
    MASSIVE = "Massive"

@dataclass
class TrendItem:
    id: str
    title: str
    author: str
    desc: str
    timestamp: datetime
    source: str
    view_count: int
    like_count: int
    share_count: int
    comment_count: int
    hashtags: List[str]
    music_id: Optional[str]
    virality_stage: ViralityStage
    growth_rate: float
    raw_data: Dict

class TrendsDatabase:
    def __init__(self, db_path: str = 'analysis/trends.db'):
        self.db_path = db_path
        self.ensure_db_dir()
        self.init_database()
        
    def ensure_db_dir(self):
        """Ensure database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
        
    def init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            # Trends table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trends (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    description TEXT,
                    timestamp DATETIME,
                    source TEXT,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    comment_count INTEGER DEFAULT 0,
                    music_id TEXT,
                    virality_stage TEXT,
                    growth_rate REAL DEFAULT 0.0,
                    first_seen DATETIME,
                    last_updated DATETIME,
                    raw_data TEXT
                )
            ''')
            
            # Hashtags table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS hashtags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hashtag TEXT,
                    trend_id TEXT,
                    timestamp DATETIME,
                    FOREIGN KEY (trend_id) REFERENCES trends (id)
                )
            ''')
            
            # Sounds/Music table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sounds (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    duration INTEGER,
                    usage_count INTEGER DEFAULT 0,
                    first_seen DATETIME,
                    last_updated DATETIME,
                    virality_stage TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Creators table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS creators (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    display_name TEXT,
                    follower_count INTEGER DEFAULT 0,
                    following_count INTEGER DEFAULT 0,
                    video_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    first_seen DATETIME,
                    last_updated DATETIME,
                    virality_stage TEXT,
                    raw_data TEXT
                )
            ''')
            
            # Analytics snapshots for trend tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analytics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trend_id TEXT,
                    timestamp DATETIME,
                    view_count INTEGER,
                    like_count INTEGER,
                    share_count INTEGER,
                    comment_count INTEGER,
                    growth_rate REAL,
                    virality_stage TEXT,
                    FOREIGN KEY (trend_id) REFERENCES trends (id)
                )
            ''')
            
            # Alerts log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trend_id TEXT,
                    alert_type TEXT,
                    message TEXT,
                    sent_at DATETIME,
                    webhook_url TEXT,
                    success BOOLEAN,
                    FOREIGN KEY (trend_id) REFERENCES trends (id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trends_timestamp ON trends (timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_trends_virality ON trends (virality_stage)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_hashtags_trend ON hashtags (trend_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_analytics_trend ON analytics_snapshots (trend_id)')
            
            conn.commit()
            
    def calculate_virality_stage(self, current_stats: Dict, historical_stats: List[Dict]) -> Tuple[ViralityStage, float]:
        """Calculate virality stage based on current and historical statistics."""
        view_count = current_stats.get('view_count', 0)
        like_count = current_stats.get('like_count', 0)
        
        # Calculate growth rate if we have historical data
        growth_rate = 0.0
        if historical_stats:
            # Get most recent previous data point
            prev_stats = historical_stats[-1]
            prev_views = prev_stats.get('view_count', 0)
            if prev_views > 0:
                growth_rate = (view_count - prev_views) / prev_views * 100
                
        # Virality classification logic
        if view_count < 10000:
            return ViralityStage.NEW, growth_rate
        elif view_count < 100000:
            if growth_rate > 50:  # High growth rate
                return ViralityStage.EARLY_TRACTION, growth_rate
            else:
                return ViralityStage.NEW, growth_rate
        elif view_count < 1000000:
            if growth_rate > 20:
                return ViralityStage.EARLY_TRACTION, growth_rate
            else:
                return ViralityStage.STEADY, growth_rate
        else:
            if growth_rate > 10:
                return ViralityStage.EARLY_TRACTION, growth_rate
            else:
                return ViralityStage.MASSIVE, growth_rate
                
    def insert_or_update_trend(self, trend_data: Dict) -> bool:
        """Insert new trend or update existing one."""
        try:
            with self.get_connection() as conn:
                trend_id = trend_data.get('id')
                if not trend_id:
                    return False
                    
                # Get historical data for this trend
                historical_stats = self.get_trend_history(trend_id)
                
                # Extract statistics
                stats = trend_data.get('stats', {})
                current_stats = {
                    'view_count': stats.get('playCount', 0),
                    'like_count': stats.get('diggCount', 0),
                    'share_count': stats.get('shareCount', 0),
                    'comment_count': stats.get('commentCount', 0),
                }
                
                # Calculate virality stage
                virality_stage, growth_rate = self.calculate_virality_stage(current_stats, historical_stats)
                
                # Check if trend exists
                existing = conn.execute('SELECT id FROM trends WHERE id = ?', (trend_id,)).fetchone()
                
                now = datetime.now()
                
                if existing:
                    # Update existing trend
                    conn.execute('''
                        UPDATE trends SET
                            title = ?, author = ?, description = ?, timestamp = ?,
                            source = ?, view_count = ?, like_count = ?, share_count = ?,
                            comment_count = ?, music_id = ?, virality_stage = ?,
                            growth_rate = ?, last_updated = ?, raw_data = ?
                        WHERE id = ?
                    ''', (
                        trend_data.get('title', ''),
                        trend_data.get('author', {}).get('uniqueId', ''),
                        trend_data.get('desc', ''),
                        trend_data.get('timestamp', now.isoformat()),
                        trend_data.get('source', ''),
                        current_stats['view_count'],
                        current_stats['like_count'],
                        current_stats['share_count'],
                        current_stats['comment_count'],
                        trend_data.get('music', {}).get('id'),
                        virality_stage.value,
                        growth_rate,
                        now,
                        json.dumps(trend_data.get('raw_data', {})),
                        trend_id
                    ))
                else:
                    # Insert new trend
                    conn.execute('''
                        INSERT INTO trends (
                            id, title, author, description, timestamp, source,
                            view_count, like_count, share_count, comment_count,
                            music_id, virality_stage, growth_rate, first_seen,
                            last_updated, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trend_id,
                        trend_data.get('title', ''),
                        trend_data.get('author', {}).get('uniqueId', ''),
                        trend_data.get('desc', ''),
                        trend_data.get('timestamp', now.isoformat()),
                        trend_data.get('source', ''),
                        current_stats['view_count'],
                        current_stats['like_count'],
                        current_stats['share_count'],
                        current_stats['comment_count'],
                        trend_data.get('music', {}).get('id'),
                        virality_stage.value,
                        growth_rate,
                        now,
                        now,
                        json.dumps(trend_data.get('raw_data', {}))
                    ))
                
                # Insert analytics snapshot
                conn.execute('''
                    INSERT INTO analytics_snapshots (
                        trend_id, timestamp, view_count, like_count, share_count,
                        comment_count, growth_rate, virality_stage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend_id, now, current_stats['view_count'], current_stats['like_count'],
                    current_stats['share_count'], current_stats['comment_count'],
                    growth_rate, virality_stage.value
                ))
                
                # Insert hashtags
                for hashtag in trend_data.get('hashtags', []):
                    conn.execute('''
                        INSERT INTO hashtags (hashtag, trend_id, timestamp)
                        VALUES (?, ?, ?)
                    ''', (hashtag, trend_id, now))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error inserting/updating trend {trend_id}: {e}")
            return False
            
    def get_trend_history(self, trend_id: str) -> List[Dict]:
        """Get historical statistics for a trend."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT view_count, like_count, share_count, comment_count, timestamp
                FROM analytics_snapshots
                WHERE trend_id = ?
                ORDER BY timestamp ASC
            ''', (trend_id,)).fetchall()
            
            return [dict(row) for row in rows]
            
    def get_trending_by_stage(self, stage: ViralityStage, limit: int = 50) -> List[Dict]:
        """Get trends by virality stage."""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM trends
                WHERE virality_stage = ?
                ORDER BY last_updated DESC
                LIMIT ?
            ''', (stage.value, limit)).fetchall()
            
            return [dict(row) for row in rows]
            
    def get_breakout_trends(self, hours: int = 24, min_growth_rate: float = 50.0) -> List[Dict]:
        """Get trends that are breaking out (high growth in recent period)."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM trends
                WHERE last_updated > ? 
                AND growth_rate > ?
                AND virality_stage = ?
                ORDER BY growth_rate DESC
            ''', (cutoff_time, min_growth_rate, ViralityStage.EARLY_TRACTION.value)).fetchall()
            
            return [dict(row) for row in rows]
            
    def get_analytics_summary(self) -> Dict:
        """Get overall analytics summary."""
        with self.get_connection() as conn:
            # Counts by virality stage
            stage_counts = {}
            for stage in ViralityStage:
                count = conn.execute(
                    'SELECT COUNT(*) FROM trends WHERE virality_stage = ?',
                    (stage.value,)
                ).fetchone()[0]
                stage_counts[stage.value] = count
                
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_count = conn.execute(
                'SELECT COUNT(*) FROM trends WHERE last_updated > ?',
                (recent_cutoff,)
            ).fetchone()[0]
            
            # Top hashtags
            top_hashtags = conn.execute('''
                SELECT hashtag, COUNT(*) as usage_count
                FROM hashtags
                WHERE timestamp > ?
                GROUP BY hashtag
                ORDER BY usage_count DESC
                LIMIT 10
            ''', (recent_cutoff,)).fetchall()
            
            return {
                'stage_counts': stage_counts,
                'recent_trends_24h': recent_count,
                'top_hashtags': [dict(row) for row in top_hashtags],
                'total_trends': sum(stage_counts.values()),
                'last_updated': datetime.now().isoformat()
            }

def main():
    """Initialize database and print summary."""
    db = TrendsDatabase()
    print("Database initialized successfully!")
    
    summary = db.get_analytics_summary()
    print(f"Total trends: {summary['total_trends']}")
    print(f"Recent trends (24h): {summary['recent_trends_24h']}")
    print("\nTrends by stage:")
    for stage, count in summary['stage_counts'].items():
        print(f"  {stage}: {count}")

if __name__ == '__main__':
    main()