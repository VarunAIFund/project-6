# Slack Employee Engagement Pulse 📊

A comprehensive AI-powered sentiment analysis system that monitors team engagement and mood across Slack channels. Features both a web application interface and CLI tools for analyzing team communication patterns, detecting burnout risks, and generating actionable insights.

## ✨ Features

- **🌐 Live Web Application**: Real-time dashboard with one-click report generation
- **🧠 AI-Powered Analysis**: GPT-based sentiment analysis for nuanced understanding
- **🔐 Privacy-First**: Analyzes sentiment without storing personal messages or user identities
- **📊 Comprehensive Analytics**: Tracks sentiment, engagement, activity patterns, and burnout indicators
- **⚠️ Burnout Detection**: Identifies concerning patterns and provides actionable recommendations
- **📈 Interactive Dashboard**: Beautiful web interface with real-time progress tracking
- **🔄 Multiple Export Formats**: JSON and HTML reports with downloadable files
- **⚙️ Configurable**: Flexible configuration via JSON files and environment variables
- **🗄️ Data Retention**: SQLite storage with automatic cleanup of old data

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Slack Bot Token with appropriate permissions
- OpenAI API key for GPT sentiment analysis
- Required OAuth scopes: `channels:history`, `channels:read`, `users:read`, `reactions:read`

### 2. Installation

```bash
# Clone or download the project
cd project-6

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
# Create .env file and add:
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
OPENAI_API_KEY=sk-your-openai-api-key
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

### 4. Run the Web Application

```bash
# Start the live web application
python app.py

# Open your browser to http://localhost:5000
# Click "Generate Report" to analyze team engagement
```

### 5. Alternative CLI Usage

```bash
# Basic CLI analysis
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

## 🌐 Web Application Features

The live web application provides:

- **Real-Time Status Monitoring**: Dashboard showing Slack connection, GPT analyzer, and database status
- **One-Click Analysis**: Generate reports for 7, 14, or 30 days with a single button click
- **Live Progress Updates**: Real-time WebSocket updates during analysis with progress bars
- **Report Management**: View and download generated HTML and JSON reports
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices
- **Interactive Metrics**: Visual display of sentiment scores, engagement levels, and burnout alerts

## 🤖 AI-Powered Sentiment Analysis

- **GPT Integration**: Uses OpenAI's GPT-3.5-turbo for sophisticated sentiment understanding
- **Context-Aware**: Analyzes workplace communication nuances and context
- **Fallback Support**: Automatically falls back to VADER sentiment analysis if GPT is unavailable
- **Emotional Intelligence**: Detects subtle emotional patterns in team communications

## 📂 Project Structure

```
project-6/
├── app.py                       # Flask web application
├── src/
│   ├── engagement_analyzer.py   # Main CLI application
│   ├── slack_data_collector.py  # Slack API integration
│   ├── sentiment_analyzer.py    # Text & emoji sentiment analysis
│   ├── gpt_sentiment_analyzer.py # GPT-powered sentiment analysis
│   ├── engagement_tracker.py    # Engagement metrics calculation
│   ├── burnout_detector.py      # Burnout pattern detection
│   ├── report_generator.py      # Report generation
│   ├── data_storage.py          # SQLite database operations
│   └── config_manager.py        # Configuration management
├── templates/
│   └── dashboard.html           # Web application frontend
├── data/                        # Database files (auto-created)
├── logs/                        # Application logs (auto-created)
├── reports/                     # Generated reports (auto-created)
├── config.json                  # Configuration file
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API keys)
└── README.md                   # This file
```

## 🔧 API Endpoints

The web application exposes several API endpoints:

- `GET /` - Main dashboard interface
- `GET /api/status` - System status and health check
- `POST /api/analyze` - Start engagement analysis
- `GET /api/results` - Get latest analysis results
- `GET /api/reports` - List available reports
- `GET /api/reports/<filename>` - Download specific report
- `GET /api/reports/<filename>/view` - View report in browser
