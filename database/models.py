"""
PSX Research Analyst - Database Models (SQLAlchemy ORM)
Universal schema support for both SQLite (Local) and PostgreSQL (Supabase)
"""
import os
import sys
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime, 
    Text, ForeignKey, UniqueConstraint, Boolean, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from contextlib import contextmanager

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, DATABASE_URL

Base = declarative_base()

# ============================================================================
# ORM MODELS
# ============================================================================

class Ticker(Base):
    __tablename__ = 'tickers'
    
    symbol = Column(String, primary_key=True)
    name = Column(String)
    sector = Column(String)
    is_active = Column(Integer, default=1)
    last_updated = Column(DateTime, default=datetime.utcnow)

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_price_symbol_date'),)

class Announcement(Base):
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    announcement_date = Column(Date)
    headline = Column(String)
    content = Column(Text)
    pdf_url = Column(String)
    announcement_type = Column(String)
    sentiment_score = Column(Float)
    processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'headline', 'announcement_date', name='uq_announcement'),)

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    rsi = Column(Float)
    volume_spike = Column(Integer)
    sentiment_score = Column(Float)
    buy_score = Column(Integer)
    recommendation = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_analysis_symbol_date'),)

class Fundamentals(Base):
    __tablename__ = 'fundamentals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    eps = Column(Float)
    eps_growth = Column(Float)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    dividend_yield = Column(Float)
    payout_ratio = Column(Float)
    debt_equity = Column(Float)
    roe = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    market_cap = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_fundamentals_symbol_date'),)

class GlobalMarket(Base):
    __tablename__ = 'global_markets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    sp500 = Column(Float)
    sp500_change = Column(Float)
    nasdaq = Column(Float)
    nasdaq_change = Column(Float)
    dow = Column(Float)
    dow_change = Column(Float)
    nikkei = Column(Float)
    nikkei_change = Column(Float)
    hang_seng = Column(Float)
    hang_seng_change = Column(Float)
    shanghai = Column(Float)
    shanghai_change = Column(Float)
    wti_oil = Column(Float)
    wti_change = Column(Float)
    brent_oil = Column(Float)
    brent_change = Column(Float)
    usd_pkr = Column(Float)
    usd_pkr_change = Column(Float)
    gold = Column(Float)
    gold_change = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class KSE100Index(Base):
    __tablename__ = 'kse100_index'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    open_value = Column(Float)
    high_value = Column(Float)
    low_value = Column(Float)
    close_value = Column(Float)
    change_value = Column(Float)
    change_percent = Column(Float)
    volume = Column(Integer)
    value_traded = Column(Float)
    advancing = Column(Integer)
    declining = Column(Integer)
    unchanged = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class SectorIndex(Base):
    __tablename__ = 'sector_indices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    sector = Column(String, nullable=False)
    index_value = Column(Float)
    change_value = Column(Float)
    change_percent = Column(Float)
    top_gainer = Column(String)
    top_loser = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('date', 'sector', name='uq_sector_date'),)

class NewsHeadline(Base):
    __tablename__ = 'news_headlines'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    source = Column(String)
    headline = Column(String, nullable=False)
    url = Column(String)
    category = Column(String)
    sentiment_score = Column(Float)
    impact_level = Column(String)
    related_symbols = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('headline', 'source', name='uq_news_headline'),)

class StockScore(Base):
    __tablename__ = 'stock_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    financial_score = Column(Integer, default=0)
    valuation_score = Column(Integer, default=0)
    technical_score = Column(Integer, default=0)
    sector_macro_score = Column(Integer, default=0)
    news_score = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    rating = Column(String)
    score_details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_score_symbol_date'),)

class TechnicalIndicator(Base):
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    ma_10 = Column(Float)
    ma_50 = Column(Float)
    ma_200 = Column(Float)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    support_level = Column(Float)
    resistance_level = Column(Float)
    trend = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_tech_symbol_date'),)

class ReportHistory(Base):
    __tablename__ = 'report_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    sent_at = Column(DateTime)
    recipients = Column(Text)
    file_path = Column(Text)
    status = Column(String, default='pending')
    error_message = Column(Text)

class AlertHistory(Base):
    __tablename__ = 'alerts_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String, nullable=False)
    symbol = Column(String)
    message = Column(String, nullable=False)
    trigger_value = Column(Float)
    threshold_value = Column(Float)
    sent_at = Column(DateTime, default=datetime.utcnow)
    channel = Column(String, default='email')
    acknowledged = Column(Integer, default=0)

class AIDecision(Base):
    __tablename__ = 'ai_decisions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, ForeignKey('tickers.symbol'), nullable=False)
    date = Column(Date, nullable=False)
    action = Column(String) # BUY, SELL, WAIT
    conviction = Column(String) # High, Medium, Low
    score = Column(Integer) # -100 to 100
    reasoning = Column(Text)
    catalyst = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('symbol', 'date', name='uq_ai_decision_date'),)

# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

def get_engine():
    """Get SQLAlchemy engine (PostgreSQL if available, else SQLite)"""
    if DATABASE_URL:
        # PostgreSQL Connection (Supabase)
        return create_engine(DATABASE_URL)
    else:
        # SQLite Connection (Local)
        return create_engine(f'sqlite:///{DATABASE_PATH}')

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database tables"""
    print(f"Initializing database... Using {'PostgreSQL/Supabase' if DATABASE_URL else 'SQLite/Local'}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
