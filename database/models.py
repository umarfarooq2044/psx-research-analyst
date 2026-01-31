"""
PSX Research Analyst - Database Models
SQLite database schema for storing ticker data, prices, announcements,
global market data, sector indices, alerts, and comprehensive stock scores
"""
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # ========================================================================
    # CORE TABLES (Existing)
    # ========================================================================
    
    # Tickers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickers (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            is_active INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Price history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # Announcements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            announcement_date DATE,
            headline TEXT,
            content TEXT,
            pdf_url TEXT,
            announcement_type TEXT,
            sentiment_score REAL,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, headline, announcement_date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # Analysis results table (for caching daily analysis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            rsi REAL,
            volume_spike INTEGER,
            sentiment_score REAL,
            buy_score INTEGER,
            recommendation TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # ========================================================================
    # NEW TABLES FOR COMPREHENSIVE MARKET INTELLIGENCE
    # ========================================================================
    
    # Global market data (overnight markets, oil, forex)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            sp500 REAL,
            sp500_change REAL,
            nasdaq REAL,
            nasdaq_change REAL,
            dow REAL,
            dow_change REAL,
            nikkei REAL,
            nikkei_change REAL,
            hang_seng REAL,
            hang_seng_change REAL,
            shanghai REAL,
            shanghai_change REAL,
            wti_oil REAL,
            wti_change REAL,
            brent_oil REAL,
            brent_change REAL,
            usd_pkr REAL,
            usd_pkr_change REAL,
            gold REAL,
            gold_change REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date)
        )
    """)
    
    # KSE-100 Index data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kse100_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            open_value REAL,
            high_value REAL,
            low_value REAL,
            close_value REAL,
            change_value REAL,
            change_percent REAL,
            volume INTEGER,
            value_traded REAL,
            advancing INTEGER,
            declining INTEGER,
            unchanged INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date)
        )
    """)
    
    # Sector indices
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sector_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            sector TEXT NOT NULL,
            index_value REAL,
            change_value REAL,
            change_percent REAL,
            top_gainer TEXT,
            top_loser TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, sector)
        )
    """)
    
    # News and headlines
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            source TEXT,
            headline TEXT NOT NULL,
            url TEXT,
            category TEXT,
            sentiment_score REAL,
            impact_level TEXT,
            related_symbols TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(headline, source)
        )
    """)
    
    # Geopolitical events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS geopolitical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            event_type TEXT,
            description TEXT,
            risk_level TEXT,
            affected_sectors TEXT,
            market_impact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Alert history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            symbol TEXT,
            message TEXT NOT NULL,
            trigger_value REAL,
            threshold_value REAL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            channel TEXT DEFAULT 'email',
            acknowledged INTEGER DEFAULT 0
        )
    """)
    
    # 100-point stock scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            financial_score INTEGER DEFAULT 0,
            valuation_score INTEGER DEFAULT 0,
            technical_score INTEGER DEFAULT 0,
            sector_macro_score INTEGER DEFAULT 0,
            news_score INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            rating TEXT,
            score_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # Technical indicators cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technical_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            ma_10 REAL,
            ma_50 REAL,
            ma_200 REAL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            macd_histogram REAL,
            bollinger_upper REAL,
            bollinger_middle REAL,
            bollinger_lower REAL,
            support_level REAL,
            resistance_level REAL,
            trend TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # Fundamental data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            eps REAL,
            eps_growth REAL,
            pe_ratio REAL,
            pb_ratio REAL,
            dividend_yield REAL,
            payout_ratio REAL,
            debt_equity REAL,
            roe REAL,
            gross_margin REAL,
            operating_margin REAL,
            net_margin REAL,
            market_cap REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES tickers(symbol)
        )
    """)
    
    # Report history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            date DATE NOT NULL,
            sent_at TIMESTAMP,
            recipients TEXT,
            file_path TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT
        )
    """)
    
    # ========================================================================
    # CREATE INDEXES
    # ========================================================================
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_date ON price_history(symbol, date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_announcements_symbol ON announcements(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_date ON global_markets(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kse100_date ON kse100_index(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector_date ON sector_indices(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news_headlines(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_date ON alerts_history(sent_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_symbol_date ON stock_scores(symbol, date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_technical_symbol_date ON technical_indicators(symbol, date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fundamentals_symbol ON fundamentals(symbol)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DATABASE_PATH}")


if __name__ == "__main__":
    init_database()
