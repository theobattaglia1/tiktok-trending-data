# TikTok A&R and Trend Analysis Engine

An AI-powered, fully automated TikTok A&R and trend analysis system that performs high-frequency data scraping, identifies rising sounds and artists, classifies virality stages, and provides real-time alerts for breakout trends.

## 🚀 Features

### High-Frequency Data Ingestion
- Scrapes TikTok discovery endpoints every 5 minutes via GitHub Actions
- Robust data collection with proxy rotation and error handling
- Expanded metadata capture for sounds, hashtags, and creators

### AI-Powered Analytics
- **Virality Stage Classification**: Automatically categorizes trends into:
  - 🌱 **New**: Fresh content with potential
  - 🚀 **Early Traction**: Rising trends worth watching  
  - 📈 **Steady**: Consistent performance
  - 🔥 **Massive**: Viral content at scale

### Real-Time A&R Alerts
- Instant notifications via Discord/Slack webhooks
- Focus on breakout trends with high growth potential
- A&R-specific filtering for new artists and rising sounds

### Interactive Analytics Dashboard
- **Streamlit-powered** web interface
- Real-time trend visualization and growth charts
- Comprehensive A&R insights and artist rankings

### Automated ETL Pipeline
- **SQLite database** for structured trend storage
- Automated data processing and analytics computation
- Historical trend tracking and growth rate analysis

## 📁 Repository Structure

```
.github/workflows/main.yml       # GitHub Actions pipeline (5-min frequency)
scripts/
  ├── fetch_discovery.py         # Enhanced TikTok data scraping
data/snapshots/                  # Timestamped data snapshots
analysis/
  ├── database.py                # SQLite schema & analytics database
  ├── compute_analytics.py       # Trend processing & classification
  └── trends.db                  # SQLite database (auto-created)
alerts/
  └── push_alerts.py             # Discord/Slack webhook alerts
dashboard/
  ├── app.py                     # Streamlit dashboard
  └── Dockerfile                 # Container deployment
requirements.txt                 # Python dependencies
README.md                        # This file
.gitignore                      # Git ignore rules
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.9+
- Git
- (Optional) Docker for dashboard deployment

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tiktok-trending-data
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python analysis/database.py
   ```

4. **Run the data pipeline manually**
   ```bash
   # Fetch TikTok data
   python scripts/fetch_discovery.py
   
   # Process analytics
   python analysis/compute_analytics.py
   
   # Check for alerts
   python alerts/push_alerts.py
   ```

5. **Launch the dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```

### Automated Pipeline (GitHub Actions)

The repository includes a GitHub Actions workflow that automatically:
- Runs every 5 minutes
- Fetches fresh TikTok data
- Processes analytics and updates the database
- Sends alerts for breakout trends
- Commits results back to the repository

#### Required Secrets
Configure these in your GitHub repository settings:

- `DISCORD_WEBHOOK_URL`: Discord webhook for alerts (optional)
- `SLACK_WEBHOOK_URL`: Slack webhook for alerts (optional)

## 📊 Analytics & Classification

### Virality Stages
The system automatically classifies trends based on view counts and growth rates:

| Stage | Criteria | Description |
|-------|----------|-------------|
| **New** | < 10K views | Fresh content with potential |
| **Early Traction** | 10K-100K views + high growth | Rising trends worth watching |
| **Steady** | 100K-1M views + moderate growth | Consistent performance |
| **Massive** | > 1M views | Viral content at scale |

### A&R Focus Areas
- **New Artists**: Emerging creators with high growth potential
- **Rising Sounds**: Music tracks gaining viral traction
- **Breakout Detection**: Real-time identification of exploding trends
- **Growth Analysis**: Historical performance tracking

## 🔔 Alert System

### Alert Types
- **High Priority**: Trends with >200% growth in last hour
- **Medium Priority**: Trends with >100% growth in 6 hours  
- **Low Priority**: Trends with >50% growth in 24 hours

### Alert Channels
- **Discord**: Rich embeds with trend details and metrics
- **Slack**: Formatted messages with engagement stats

## 🐳 Docker Deployment

Deploy the dashboard using Docker:

```bash
# Build the image
docker build -t tiktok-ar-dashboard ./dashboard

# Run the container
docker run -p 8501:8501 -v $(pwd):/app tiktok-ar-dashboard
```

Access the dashboard at `http://localhost:8501`

## 📈 Dashboard Features

### Overview Metrics
- Total trends tracked
- Recent activity (24h)
- Top hashtags
- Real-time updates

### Visualization
- **Virality distribution** pie charts
- **Growth rate** trends over time
- **Hashtag popularity** analysis
- **A&R alerts** priority ranking

### Interactive Filters
- Filter by virality stage
- Time range selection
- Creator and sound filtering

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Webhook URLs for alerts
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### Customization
- **Alert thresholds**: Modify in `alerts/push_alerts.py`
- **Scraping frequency**: Update in `.github/workflows/main.yml`
- **Classification logic**: Adjust in `analysis/database.py`

## 📝 API Data Sources

Currently scrapes from TikTok's public discovery endpoints:
- `www.tiktok.com/node/share/discover`
- `us.tiktok.com/node/share/discover`
- TikTok API feed endpoints
- Discovery list endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect TikTok's terms of service and rate limits.

---

## 🎯 A&R Use Cases

### For Record Labels
- **Talent Scouting**: Identify rising artists before they explode
- **Sound Tracking**: Monitor which songs are gaining traction
- **Market Analysis**: Understand viral content patterns

### For Artists & Managers  
- **Trend Monitoring**: Stay ahead of viral challenges and sounds
- **Competitive Analysis**: Track performance vs. similar artists
- **Timing Strategy**: Optimal release timing based on trends

### For Music Industry
- **Investment Decisions**: Data-driven A&R investments
- **Marketing Intelligence**: Viral content insights
- **Predictive Analytics**: Early trend identification

---

**Generated on**: Tuesday, August 6, 2025  
**Last Updated**: Auto-updated via GitHub Actions every 5 minutes
