# 📊 PSX Autonomous Research Analyst

A Python-based system that scans the entire Pakistan Stock Exchange (PSX) daily, performs sentiment and technical analysis, and emails a professional Buy/Sell report before 9:00 AM PKT.

## 🌟 Features

- **Full Market Discovery**: Automatically scans 500+ active PSX tickers
- **Technical Analysis**: RSI(14), Volume Spikes, 52-Week High/Low analysis
- **Sentiment Analysis**: VADER-based NLP with financial keyword boosting
- **Smart Recommendations**: Buy Score (1-10) combining technical + sentiment signals
- **Professional Reports**: Styled HTML email with Top Opportunities, Red Alerts, and Watchlist
- **Automated Scheduling**: Runs daily at 8:15 AM PKT

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Buy Score Logic](#buy-score-logic)
- [Project Structure](#project-structure)

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download** this project to your machine

2. **Navigate to project directory**:
   ```bash
   cd psx_research_analyst
   ```

3. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Download NLTK data** (for sentiment analysis):
   ```python
   python -c "import nltk; nltk.download('vader_lexicon')"
   ```

## ⚙️ Configuration

### Email Setup (Required for email reports)

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with your email credentials:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENTS=recipient1@email.com,recipient2@email.com
   ```

### Gmail App Password

For Gmail, you need to use an **App Password** (not your regular password):

1. Go to [Google Account](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App Passwords**
4. Generate a new app password for "Mail"
5. Use this 16-character password in your `.env` file

### Customizing Watchlist

Edit `config.py` to set your personal watchlist:
```python
WATCHLIST = ["SAZEW", "GLAXO", "AIRLINK", "FFC", "MARI"]
```

## 🚀 Usage

### Run Immediately (One-time scan)

```bash
# Full market scan with email
python main.py --run-now

# Full scan without email (just generate report)
python main.py --run-now --no-email

# Test mode (only analyze watchlist + sample tickers)
python main.py --test
```

### Run with Scheduler (Daily automation)

```bash
# Starts scheduler, runs at 8:15 AM PKT daily
python main.py
```

### Test Email Configuration

```bash
python main.py --test-email
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--run-now` | Run the scan immediately |
| `--test` | Test mode with limited tickers |
| `--test-email` | Send a test email |
| `--no-email` | Skip sending email |

## 🧠 How It Works

### 1. Market Discovery
- Fetches all eligible scrips from PSX XML endpoint
- Builds dynamic list of 500+ active tickers
- Filters out ETFs, preference shares, rights (optional)

### 2. Price Data Collection
- Fetches intraday data for each ticker
- Calculates: Current Price, Volume, Day High/Low
- Stores historical data in SQLite for analysis

### 3. News Scraping
- Scrapes company pages for announcements
- Extracts headlines and PDF links
- Deduplicates to avoid processing same news twice

### 4. Technical Analysis
- **RSI(14)**: Relative Strength Index
- **Volume Spike**: Current Vol > 2.5x 20-day average
- **Support/Resistance**: 52-week high/low levels

### 5. Sentiment Analysis
- Uses NLTK VADER for sentiment scoring
- Boosts scores for positive keywords: "Dividend", "Bonus", "Profit"
- Penalizes for negative keywords: "Loss", "Default", "Investigation"

### 6. Recommendation Generation
- Combines technical (0-5) + sentiment (0-5) scores
- Applies bonuses/penalties for special conditions
- Outputs Buy Score (1-10) and recommendation

## 📊 Buy Score Logic

| Score | Recommendation | Conditions |
|-------|----------------|------------|
| 8-10 | **STRONG BUY** | Positive News + Volume Spike + RSI < 40 |
| 5-7 | **BUY** | Positive/Neutral News + Normal conditions |
| 4-5 | **HOLD** | Mixed signals |
| 1-3 | **SELL/AVOID** | Negative News + RSI > 70 + Below Support |

### Bonus Points
- +2: Positive sentiment + Volume spike + RSI oversold
- +1: Very positive news (dividend announcements)
- +1: Near 52W low but holding support

### Penalty Points
- -2: Negative news + RSI overbought
- -2: Broke 52W support level
- -1: Very negative news sentiment

## 📁 Project Structure

```
psx_research_analyst/
├── config.py              # Configuration settings
├── main.py                # Main orchestration script
├── requirements.txt       # Python dependencies
├── .env.example           # Email credentials template
├── README.md              # This file
│
├── database/
│   ├── models.py          # SQLite table definitions
│   └── db_manager.py      # Database CRUD operations
│
├── scraper/
│   ├── ticker_discovery.py    # PSX ticker list scraper
│   ├── price_scraper.py       # Price/volume data fetcher
│   └── announcements_scraper.py  # News announcement scraper
│
├── analysis/
│   ├── technical.py       # RSI, Volume Spike calculations
│   ├── sentiment.py       # VADER sentiment analysis
│   └── recommendation.py  # Buy Score engine
│
├── report/
│   ├── email_template.py  # HTML report generation
│   └── email_sender.py    # SMTP email sending
│
└── reports/               # Generated HTML reports (auto-created)
```

## 📧 Sample Report

The system generates a professional HTML report with:

1. **Market Summary**: Total analyzed, Strong Buys, Red Alerts
2. **Top 5 Opportunities**: Highest scoring stocks with analysis
3. **Red Alert Section**: Stocks to avoid/sell
4. **Watchlist Update**: Status of your personal watchlist

## 🔒 Data Storage

All data is stored locally in SQLite database (`psx_data.db`):
- Ticker information
- Historical price data
- Company announcements
- Analysis results

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. 

- Not financial advice
- Always do your own research before investing
- Past performance doesn't guarantee future results
- The creators are not responsible for any financial decisions

## 📝 License

MIT License - Feel free to modify and use for personal projects.

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

---

**Built with ❤️ for Pakistan Stock Exchange traders**
