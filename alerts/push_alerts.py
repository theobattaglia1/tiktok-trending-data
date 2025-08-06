#!/usr/bin/env python3
"""
TikTok Trends Alert System
Sends real-time alerts for breakout trends via Discord/Slack webhooks.
"""

import json
import os
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.database import TrendsDatabase

class AlertManager:
    def __init__(self):
        self.db = TrendsDatabase()
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        
    def format_trend_for_alert(self, trend: Dict) -> Dict:
        """Format trend data for alert message."""
        return {
            'title': trend.get('title', 'Unknown Title'),
            'author': trend.get('author', 'Unknown Author'),
            'description': trend.get('description', '')[:200] + '...' if len(trend.get('description', '')) > 200 else trend.get('description', ''),
            'view_count': trend.get('view_count', 0),
            'like_count': trend.get('like_count', 0),
            'growth_rate': trend.get('growth_rate', 0),
            'virality_stage': trend.get('virality_stage', ''),
            'timestamp': trend.get('last_updated', ''),
            'source': trend.get('source', ''),
            'id': trend.get('id', '')
        }
        
    def create_discord_embed(self, trend: Dict, alert_type: str = "Breakout Trend") -> Dict:
        """Create Discord embed for trend alert."""
        formatted = self.format_trend_for_alert(trend)
        
        # Color based on virality stage
        color_map = {
            'New': 0x00ff00,           # Green
            'Early Traction': 0xff9900,  # Orange  
            'Steady': 0x0099ff,        # Blue
            'Massive': 0xff0000        # Red
        }
        color = color_map.get(formatted['virality_stage'], 0x808080)
        
        embed = {
            "title": f"🚀 {alert_type}: {formatted['title']}",
            "description": formatted['description'],
            "color": color,
            "thumbnail": {
                "url": "https://cdn-icons-png.flaticon.com/512/3938/3938026.png"  # TikTok icon
            },
            "fields": [
                {
                    "name": "👤 Creator",
                    "value": f"@{formatted['author']}",
                    "inline": True
                },
                {
                    "name": "📊 Stats",
                    "value": f"👀 {formatted['view_count']:,}\n❤️ {formatted['like_count']:,}",
                    "inline": True
                },
                {
                    "name": "📈 Growth",
                    "value": f"{formatted['growth_rate']:.1f}%",
                    "inline": True
                },
                {
                    "name": "🎯 Stage",
                    "value": formatted['virality_stage'],
                    "inline": True
                },
                {
                    "name": "🕒 Detected",
                    "value": formatted['timestamp'][:16],
                    "inline": True
                },
                {
                    "name": "📍 Source",
                    "value": formatted['source'],
                    "inline": True
                }
            ],
            "footer": {
                "text": f"TikTok A&R Alert System • Trend ID: {formatted['id'][:8]}",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/3938/3938026.png"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "embeds": [embed],
            "username": "TikTok A&R Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/3938/3938026.png"
        }
        
    def create_slack_message(self, trend: Dict, alert_type: str = "Breakout Trend") -> Dict:
        """Create Slack message for trend alert."""
        formatted = self.format_trend_for_alert(trend)
        
        # Emoji based on virality stage
        stage_emoji = {
            'New': '🌱',
            'Early Traction': '🚀',
            'Steady': '📈',
            'Massive': '🔥'
        }
        emoji = stage_emoji.get(formatted['virality_stage'], '📊')
        
        text = f"{emoji} *{alert_type}*: {formatted['title']}"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert_type} Alert"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{formatted['title']}*\nby @{formatted['author']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Views:*\n{formatted['view_count']:,}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Likes:*\n{formatted['like_count']:,}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Growth Rate:*\n{formatted['growth_rate']:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Stage:*\n{formatted['virality_stage']}"
                    }
                ]
            }
        ]
        
        if formatted['description']:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{formatted['description']}"
                }
            })
            
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Source: {formatted['source']} | Detected: {formatted['timestamp'][:16]} | ID: {formatted['id'][:8]}"
                }
            ]
        })
        
        return {
            "text": text,
            "blocks": blocks,
            "username": "TikTok A&R Bot",
            "icon_emoji": ":rocket:"
        }
        
    def send_discord_alert(self, trend: Dict, alert_type: str = "Breakout Trend") -> bool:
        """Send alert to Discord webhook."""
        if not self.discord_webhook:
            print("Discord webhook URL not configured")
            return False
            
        try:
            message = self.create_discord_embed(trend, alert_type)
            response = requests.post(
                self.discord_webhook,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            # Log to database
            self.log_alert(trend['id'], 'discord', alert_type, self.discord_webhook, True)
            return True
            
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")
            self.log_alert(trend['id'], 'discord', alert_type, self.discord_webhook, False, str(e))
            return False
            
    def send_slack_alert(self, trend: Dict, alert_type: str = "Breakout Trend") -> bool:
        """Send alert to Slack webhook."""
        if not self.slack_webhook:
            print("Slack webhook URL not configured")
            return False
            
        try:
            message = self.create_slack_message(trend, alert_type)
            response = requests.post(
                self.slack_webhook,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            # Log to database
            self.log_alert(trend['id'], 'slack', alert_type, self.slack_webhook, True)
            return True
            
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            self.log_alert(trend['id'], 'slack', alert_type, self.slack_webhook, False, str(e))
            return False
            
    def log_alert(self, trend_id: str, platform: str, alert_type: str, webhook_url: str, success: bool, error_msg: str = None):
        """Log alert to database."""
        try:
            with self.db.get_connection() as conn:
                message = f"{alert_type} alert via {platform}"
                if error_msg:
                    message += f" - Error: {error_msg}"
                    
                conn.execute('''
                    INSERT INTO alerts (trend_id, alert_type, message, sent_at, webhook_url, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (trend_id, alert_type, message, datetime.now(), webhook_url[:100], success))
                conn.commit()
        except Exception as e:
            print(f"Failed to log alert: {e}")
            
    def check_for_breakout_trends(self, hours: int = 1, min_growth_rate: float = 100.0) -> List[Dict]:
        """Check for new breakout trends that haven't been alerted yet."""
        breakout_trends = self.db.get_breakout_trends(hours=hours, min_growth_rate=min_growth_rate)
        
        # Filter out trends we've already alerted about recently
        new_breakouts = []
        with self.db.get_connection() as conn:
            for trend in breakout_trends:
                # Check if we've sent an alert for this trend in the last 6 hours
                recent_alerts = conn.execute('''
                    SELECT COUNT(*) FROM alerts 
                    WHERE trend_id = ? AND sent_at > datetime('now', '-6 hours') AND success = 1
                ''', (trend['id'],)).fetchone()[0]
                
                if recent_alerts == 0:
                    new_breakouts.append(trend)
                    
        return new_breakouts
        
    def send_breakout_alerts(self, hours: int = 1, min_growth_rate: float = 100.0) -> int:
        """Check for and send alerts for new breakout trends."""
        new_breakouts = self.check_for_breakout_trends(hours, min_growth_rate)
        
        if not new_breakouts:
            print("No new breakout trends to alert about")
            return 0
            
        alerts_sent = 0
        
        for trend in new_breakouts:
            alert_type = f"Early Traction Alert"
            print(f"Sending alert for: {trend.get('title', 'Unknown')} by {trend.get('author', 'Unknown')}")
            
            # Send to both Discord and Slack if configured
            discord_success = self.send_discord_alert(trend, alert_type)
            slack_success = self.send_slack_alert(trend, alert_type)
            
            if discord_success or slack_success:
                alerts_sent += 1
                
        print(f"Sent {alerts_sent}/{len(new_breakouts)} breakout alerts")
        return alerts_sent
        
    def send_summary_alert(self, report: Dict) -> bool:
        """Send daily/periodic summary alert."""
        summary = report['summary']
        breakouts = report['breakout_trends']
        
        summary_trend = {
            'id': 'summary',
            'title': 'Daily TikTok Trends Summary',
            'author': 'TikTok A&R System',
            'description': f"Total trends: {summary['total_trends']} | Recent (24h): {summary['recent_trends_24h']} | Breakouts: {len(breakouts['24_hours'])}",
            'view_count': summary['total_trends'],
            'like_count': len(breakouts['24_hours']),
            'growth_rate': 0,
            'virality_stage': 'Summary',
            'last_updated': summary['last_updated'],
            'source': 'analytics'
        }
        
        alert_type = "Daily Summary"
        discord_success = self.send_discord_alert(summary_trend, alert_type)
        slack_success = self.send_slack_alert(summary_trend, alert_type)
        
        return discord_success or slack_success

def main():
    """Main alerting function."""
    alert_manager = AlertManager()
    
    # Check for breakout trends in the last hour
    print("Checking for breakout trends...")
    alerts_sent = alert_manager.send_breakout_alerts(hours=1, min_growth_rate=150.0)
    
    if alerts_sent > 0:
        print(f"✓ Sent {alerts_sent} breakout alerts")
    else:
        print("No breakout alerts needed")

if __name__ == '__main__':
    main()