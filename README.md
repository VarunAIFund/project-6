# Slack Employee Engagement Pulse 📊

A comprehensive sentiment analysis system that monitors team engagement and mood across configurable Slack channels. The system analyzes messages, reactions, and emoji usage to generate weekly sentiment reports and identify potential burnout patterns.

## ✨ Features

- **🔐 Privacy-First**: Analyzes sentiment without storing personal messages or user identities
- **📊 Comprehensive Analytics**: Tracks sentiment, engagement, activity patterns, and burnout indicators
- **⚠️ Burnout Detection**: Identifies concerning patterns and provides actionable recommendations
- **📈 Interactive Dashboard**: Beautiful HTML dashboard with real-time charts
- **🔄 Multiple Export Formats**: JSON, CSV, and HTML reports
- **⚙️ Configurable**: Flexible configuration via JSON files and environment variables
- **🗄️ Data Retention**: SQLite storage with automatic cleanup of old data

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Slack Bot Token with appropriate permissions
- Required OAuth scopes: `channels:history`, `channels:read`, `users:read`, `reactions:read`

### 2. Installation

```bash
# Clone or download the project
cd project-6

# Install dependencies
pip install -r requirements.txt

# Set up your Slack bot token
cp .env.example .env
# Edit .env and add your SLACK_BOT_TOKEN
```

### 3. Configuration

Edit `config.json` to configure your monitored channels and settings:

```json
{
  "monitored_channels": ["#general", "#random", "#dev-team"],
  "analysis_days": 7,
  "burnout_threshold": -0.3,
  "min_messages_per_day": 5
}
```

### 4. Run Analysis

```bash
# Basic analysis
python src/engagement_analyzer.py

# Test Slack connection
python src/engagement_analyzer.py --test-connection

# Analyze specific number of days
python src/engagement_analyzer.py --days 14
```

## 🛡️ Privacy & Security

- **No Personal Data**: Only aggregated, anonymized metrics are stored
- **Message Content**: Original message text is never persisted
- **User Privacy**: No usernames or personal identifiers are stored
- **Data Retention**: Automatic cleanup of old data based on retention policy
- **Local Storage**: All data stays on your infrastructure

## 📂 Project Structure

```
project-6/
├── src/
│   ├── engagement_analyzer.py    # Main application
│   ├── slack_data_collector.py   # Slack API integration
│   ├── sentiment_analyzer.py     # Text & emoji sentiment analysis
│   ├── engagement_tracker.py     # Engagement metrics calculation
│   ├── burnout_detector.py       # Burnout pattern detection
│   ├── report_generator.py       # Report generation
│   ├── data_storage.py          # SQLite database operations
│   └── config_manager.py        # Configuration management
├── templates/
│   └── dashboard.html           # HTML dashboard template
├── data/                        # Database files (auto-created)
├── reports/                     # Generated reports (auto-created)
├── config.json                  # Configuration file
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```
