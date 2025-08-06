#!/usr/bin/env python3
"""
TikTok A&R and Trends Analytics Dashboard
Interactive Streamlit dashboard for visualizing TikTok trends and A&R insights.
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.database import TrendsDatabase, ViralityStage
from analysis.compute_analytics import TrendsAnalytics

# Page configuration
st.set_page_config(
    page_title="TikTok A&R Analytics",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ff0050;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff0050;
    }
    .stage-new { border-left-color: #00ff00 !important; }
    .stage-early { border-left-color: #ff9900 !important; }
    .stage-steady { border-left-color: #0099ff !important; }
    .stage-massive { border-left-color: #ff0000 !important; }
</style>
""", unsafe_allow_html=True)

class TikTokDashboard:
    def __init__(self):
        self.db = TrendsDatabase()
        self.analytics = TrendsAnalytics()
        
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def load_data(_self):
        """Load data from database."""
        try:
            summary = _self.db.get_analytics_summary()
            
            # Get trends by stage
            trends_data = {}
            for stage in ViralityStage:
                trends_data[stage.value] = _self.db.get_trending_by_stage(stage, limit=100)
                
            # Get breakout trends
            breakout_trends = _self.db.get_breakout_trends(hours=24, min_growth_rate=50.0)
            
            return summary, trends_data, breakout_trends
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None, None, None
            
    def render_header(self):
        """Render main header."""
        st.markdown('<h1 class="main-header">🎵 TikTok A&R Analytics Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
    def render_metrics_overview(self, summary):
        """Render key metrics overview."""
        st.subheader("📊 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Trends",
                value=summary['total_trends'],
                delta=None
            )
            
        with col2:
            st.metric(
                label="Recent Activity (24h)",
                value=summary['recent_trends_24h'],
                delta=None
            )
            
        with col3:
            if summary['top_hashtags']:
                top_hashtag = summary['top_hashtags'][0]
                st.metric(
                    label="Top Hashtag",
                    value=f"#{top_hashtag['hashtag']}",
                    delta=f"{top_hashtag['usage_count']} uses"
                )
            else:
                st.metric(label="Top Hashtag", value="None", delta=None)
                
        with col4:
            st.metric(
                label="Last Updated",
                value=summary['last_updated'][:16] if summary['last_updated'] else "Never",
                delta=None
            )
            
    def render_virality_distribution(self, summary):
        """Render virality stage distribution chart."""
        st.subheader("🚀 Virality Stage Distribution")
        
        stage_counts = summary['stage_counts']
        
        if any(stage_counts.values()):
            # Create pie chart
            fig = px.pie(
                values=list(stage_counts.values()),
                names=list(stage_counts.keys()),
                title="Trends by Virality Stage",
                color_discrete_map={
                    'New': '#00ff00',
                    'Early Traction': '#ff9900',
                    'Steady': '#0099ff',
                    'Massive': '#ff0000'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data available yet.")
            
    def render_trends_table(self, trends_data, stage_filter):
        """Render trends table for specific stage."""
        if stage_filter == "All":
            all_trends = []
            for stage_trends in trends_data.values():
                all_trends.extend(stage_trends)
            trends = all_trends
        else:
            trends = trends_data.get(stage_filter, [])
            
        if not trends:
            st.info(f"No trends found for {stage_filter}")
            return
            
        # Convert to DataFrame
        df_data = []
        for trend in trends:
            df_data.append({
                'Title': trend.get('title', 'Unknown'),
                'Author': trend.get('author', 'Unknown'),
                'Views': trend.get('view_count', 0),
                'Likes': trend.get('like_count', 0),
                'Growth Rate': f"{trend.get('growth_rate', 0):.1f}%",
                'Stage': trend.get('virality_stage', ''),
                'Last Updated': trend.get('last_updated', '')[:16] if trend.get('last_updated') else ''
            })
            
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No trend data available.")
            
    def render_breakout_trends(self, breakout_trends):
        """Render breakout trends section."""
        st.subheader("🔥 Breakout Trends (A&R Alerts)")
        
        if not breakout_trends:
            st.info("No breakout trends detected in the last 24 hours.")
            return
            
        # Sort by growth rate
        breakout_trends.sort(key=lambda x: x.get('growth_rate', 0), reverse=True)
        
        for i, trend in enumerate(breakout_trends[:10]):  # Show top 10
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{trend.get('title', 'Unknown')}**")
                    st.markdown(f"by @{trend.get('author', 'Unknown')}")
                    if trend.get('description'):
                        st.markdown(f"*{trend.get('description', '')[:100]}...*")
                        
                with col2:
                    st.metric("Views", f"{trend.get('view_count', 0):,}")
                    st.metric("Likes", f"{trend.get('like_count', 0):,}")
                    
                with col3:
                    st.metric("Growth", f"{trend.get('growth_rate', 0):.1f}%")
                    st.metric("Stage", trend.get('virality_stage', ''))
                    
                st.markdown("---")
                
    def render_hashtag_analysis(self, summary):
        """Render hashtag analysis."""
        st.subheader("🏷️ Trending Hashtags")
        
        top_hashtags = summary['top_hashtags']
        
        if not top_hashtags:
            st.info("No hashtag data available.")
            return
            
        # Create bar chart
        hashtags = [f"#{h['hashtag']}" for h in top_hashtags[:10]]
        counts = [h['usage_count'] for h in top_hashtags[:10]]
        
        fig = px.bar(
            x=counts,
            y=hashtags,
            orientation='h',
            title="Top 10 Hashtags (24h)",
            labels={'x': 'Usage Count', 'y': 'Hashtag'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
    def render_sidebar(self):
        """Render sidebar controls."""
        st.sidebar.title("🎛️ Controls")
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
            
        st.sidebar.markdown("---")
        
        # Filters
        st.sidebar.subheader("Filters")
        
        stage_filter = st.sidebar.selectbox(
            "Virality Stage",
            ["All", "New", "Early Traction", "Steady", "Massive"]
        )
        
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"]
        )
        
        st.sidebar.markdown("---")
        
        # Info
        st.sidebar.subheader("ℹ️ About")
        st.sidebar.info(
            "This dashboard provides real-time analytics for TikTok trends, "
            "helping A&R professionals identify rising artists and breakout sounds."
        )
        
        return stage_filter, time_range
        
    def run(self):
        """Run the dashboard."""
        self.render_header()
        
        # Sidebar
        stage_filter, time_range = self.render_sidebar()
        
        # Load data
        summary, trends_data, breakout_trends = self.load_data()
        
        if summary is None:
            st.error("Failed to load data. Please check the database connection.")
            return
            
        # Main content
        self.render_metrics_overview(summary)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.render_virality_distribution(summary)
            
        with col2:
            self.render_hashtag_analysis(summary)
            
        # Breakout trends
        self.render_breakout_trends(breakout_trends)
        
        # Trends table
        st.subheader(f"📋 Trends ({stage_filter})")
        self.render_trends_table(trends_data, stage_filter)
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "TikTok A&R Analytics Dashboard • "
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            "</div>",
            unsafe_allow_html=True
        )

def main():
    """Main function."""
    dashboard = TikTokDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()