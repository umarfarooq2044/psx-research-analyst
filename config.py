"""
PSX Research Analyst - Configuration Settings
Comprehensive Market Intelligence System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PSX DATA SOURCE URLs
# ============================================================================
PSX_BASE_URL = "https://dps.psx.com.pk"
ELIGIBLE_SCRIPS_URL = f"{PSX_BASE_URL}/data/eligible-scrips/REG.xml"
COMPANY_URL_TEMPLATE = f"{PSX_BASE_URL}/company/{{ticker}}"
TIMESERIES_URL_TEMPLATE = f"{PSX_BASE_URL}/timeseries/int/{{ticker}}"
KSE100_URL = f"{PSX_BASE_URL}/market-watch"

# ============================================================================
# GLOBAL MARKET DATA SOURCES (Free APIs)
# ============================================================================
# Exchange Rate
FOREX_API_URL = "https://open.er-api.com/v6/latest/USD"

# Oil Prices (using free API)
OIL_API_URL = "https://api.oilpriceapi.com/v1/prices/latest"

# Global Indices (Yahoo Finance scraping)
YAHOO_FINANCE_URL = "https://finance.yahoo.com/quote/{symbol}"

# News Sources
NEWS_SOURCES = {
    "dawn": "https://www.dawn.com/business",
    "business_recorder": "https://www.brecorder.com/business",
    "tribune": "https://tribune.com.pk/business"
}

# ============================================================================
# DATABASE SETTINGS
# ============================================================================
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "psx_data.db")

# ============================================================================
# WATCHLIST - Stocks to always include in report
# ============================================================================
WATCHLIST = ["SAZEW", "GLAXO", "AIRLINK", "FFC", "MARI"]

# Top 50 liquid stocks for deep analysis
TOP_STOCKS = [
    "OGDC", "PPL", "PSO", "HBL", "MCB", "UBL", "NBP", "BOP", "ABL", "MEBL",
    "FFC", "EFERT", "ENGRO", "LUCK", "DGKC", "MLCF", "KOHC", "CHCC", "FCCL",
    "MARI", "POL", "HUBC", "KEL", "KAPCO", "NPL", "PAEL", "SEARL", "GLAXO",
    "COLG", "NESTLE", "UNILEVER", "SYS", "HCAR", "INDU", "PSMC", "MTL",
    "PIOC", "INIL", "TRG", "AVN", "UNITY", "ATRL", "NRL", "BYCO", "HASCOL",
    "APL", "SHEL", "PKGS", "THALL", "LOTCHEM"
]

# Sector definitions for PSX
SECTORS = {
    "banking": ["HBL", "MCB", "UBL", "NBP", "BOP", "ABL", "MEBL", "BAFL", "AKBL", "JSBL"],
    "oil_gas": ["OGDC", "PPL", "PSO", "POL", "MARI", "APL", "SHEL", "HASCOL", "BYCO", "ATRL"],
    "fertilizer": ["FFC", "EFERT", "ENGRO", "FATIMA", "DAWH"],
    "cement": ["LUCK", "DGKC", "MLCF", "KOHC", "CHCC", "FCCL", "PIOC", "ACPL"],
    "power": ["HUBC", "KEL", "KAPCO", "NPL", "PKGP", "NCPL"],
    "pharma": ["GLAXO", "SEARL", "AGP", "IBL", "HINOON", "FEROZ"],
    "auto": ["HCAR", "INDU", "PSMC", "MTL", "GHNL", "ATLH"],
    "telecom": ["PTC", "TRG", "SYS", "NETSOL"],
    "food": ["NESTLE", "COLG", "UNILEVER", "QUICE", "FCEPL"],
    "textile": ["NML", "NCL", "GATM", "KTML", "CEPB"]
}

# ============================================================================
# TECHNICAL ANALYSIS PARAMETERS
# ============================================================================
RSI_PERIOD = 14
VOLUME_SPIKE_MULTIPLIER = 2.5
VOLUME_AVERAGE_DAYS = 20

# Moving Averages
MA_SHORT = 10
MA_MEDIUM = 50
MA_LONG = 200

# MACD Parameters
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# RSI Thresholds
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# ============================================================================
# SENTIMENT ANALYSIS KEYWORDS
# ============================================================================
POSITIVE_KEYWORDS = [
    "bonus", "dividend", "profit", "discovery", "growth",
    "record", "milestone", "expansion", "acquisition", "partnership",
    "increase", "surge", "breakthrough", "approval", "contract",
    "upgrade", "outperform", "beat", "exceed", "strong"
]

NEGATIVE_KEYWORDS = [
    "loss", "decline", "default", "penalty", "investigation",
    "lawsuit", "fraud", "suspension", "warning", "debt",
    "layoff", "closure", "violation", "fine", "bankruptcy",
    "downgrade", "underperform", "miss", "weak", "risk"
]

KEYWORD_BOOST = 0.3
KEYWORD_PENALTY = -0.3

# ============================================================================
# 100-POINT STOCK SCORING SYSTEM THRESHOLDS
# ============================================================================
SCORE_WEIGHTS = {
    "financial": 35,      # Financial Health
    "valuation": 25,      # Valuation
    "technical": 20,      # Technical Momentum
    "sector_macro": 15,   # Sector & Macro
    "news": 5             # News & Catalysts
}

# Score interpretation
SCORE_RATINGS = {
    85: "STRONG BUY",
    70: "BUY",
    55: "HOLD",
    40: "REDUCE",
    0: "SELL/AVOID"
}

# Buy Score Thresholds (legacy 10-point system)
STRONG_BUY_THRESHOLD = 8
MODERATE_BUY_THRESHOLD = 5
SELL_THRESHOLD = 4

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

# ============================================================================
# TELEGRAM CONFIGURATION (Optional)
# ============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = False  # Email-only mode

# ============================================================================
# SCRAPING SETTINGS
# ============================================================================
REQUEST_DELAY = 0.5
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# ============================================================================
# REPORT SETTINGS
# ============================================================================
TOP_OPPORTUNITIES_COUNT = 10
RED_ALERT_THRESHOLD = 4
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# ============================================================================
# ALERT THRESHOLDS
# ============================================================================
ALERT_THRESHOLDS = {
    'price_move': 5.0,       # Alert on 5%+ price move
    'volume_spike': 2.0,     # Alert when volume 2x+ average
    'rsi_oversold': 30,      # RSI below this = oversold alert
    'rsi_overbought': 70,    # RSI above this = overbought alert
}

# ============================================================================
# MULTI-SCHEDULE CONFIGURATION (Pakistan Standard Time)
# ============================================================================
SCHEDULES = {
    "pre_market": {
        "time": "06:00",
        "description": "Pre-Market Briefing",
        "enabled": True
    },
    "mid_day": {
        "time": "13:00",
        "description": "Mid-Day Market Update",
        "enabled": True
    },
    "post_market": {
        "time": "16:30",
        "description": "Post-Market Deep Analysis",
        "enabled": True
    },
    "weekly": {
        "time": "17:00",
        "day": "friday",
        "description": "Weekly Strategy Report",
        "enabled": True
    }
}

# Legacy single schedule (for backward compatibility)
DAILY_SCAN_TIME = "08:15"

# ============================================================================
# MARKET TIMING (PSX Market Hours)
# ============================================================================
MARKET_OPEN = "09:32"
MARKET_CLOSE = "15:30"
PRE_MARKET_START = "09:15"

# ============================================================================
# ALERT THRESHOLDS
# ============================================================================
PRICE_ALERT_THRESHOLD = 5.0       # Alert if price moves 5%+
VOLUME_ALERT_THRESHOLD = 150      # Alert if volume > 150% of 20-day avg
SUPPORT_BREAK_THRESHOLD = 2.0     # Alert if price breaks support by 2%+
RESISTANCE_BREAK_THRESHOLD = 2.0  # Alert if price breaks resistance by 2%+
