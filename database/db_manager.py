"""
PSX Research Analyst - Database Manager (SQLAlchemy Version)
CRUD operations for both SQLite (Local) and PostgreSQL (Supabase)
"""
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple, Any
import os
import sys
from sqlalchemy import desc, func, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import (
    get_db_session, init_database,
    Ticker, PriceHistory, Announcement, AnalysisResult, GlobalMarket,
    KSE100Index, SectorIndex, NewsHeadline, StockScore, TechnicalIndicator,
    ReportHistory, AlertHistory, Fundamentals, AIDecision
)

class DBManager:
    """Database manager for PSX Research Analyst (ORM version)"""
    
    def __init__(self):
        """Initialize database manager"""
        # Ensure tables exist on startup
        init_database()
    
    # ==================== TICKER OPERATIONS ====================
    
    def upsert_ticker(self, symbol: str, name: str, sector: str = None):
        """Insert or update a ticker"""
        with get_db_session() as session:
            ticker = session.query(Ticker).filter_by(symbol=symbol).first()
            if ticker:
                ticker.name = name
                if sector:
                    ticker.sector = sector
                ticker.last_updated = datetime.now()
            else:
                ticker = Ticker(symbol=symbol, name=name, sector=sector)
                session.add(ticker)
    
    def bulk_upsert_tickers(self, tickers_data: List[Dict]):
        """Bulk insert or update tickers"""
        with get_db_session() as session:
            for item in tickers_data:
                ticker = session.query(Ticker).filter_by(symbol=item['symbol']).first()
                if ticker:
                    ticker.name = item['name']
                    if item.get('sector'):
                        ticker.sector = item.get('sector')
                    ticker.last_updated = datetime.now()
                else:
                    ticker = Ticker(
                        symbol=item['symbol'], 
                        name=item['name'], 
                        sector=item.get('sector')
                    )
                    session.add(ticker)
    
    def get_all_tickers(self) -> List[Dict]:
        """Get all active tickers"""
        with get_db_session() as session:
            tickers = session.query(Ticker).filter_by(is_active=1).all()
            return [{'symbol': t.symbol, 'name': t.name, 'sector': t.sector} for t in tickers]
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get a specific ticker"""
        with get_db_session() as session:
            ticker = session.query(Ticker).filter_by(symbol=symbol).first()
            if ticker:
                return {'symbol': ticker.symbol, 'name': ticker.name, 'sector': ticker.sector}
            return None
    
    # ==================== PRICE OPERATIONS ====================
    
    def insert_price(self, symbol: str, date_str: str, open_price: float = None,
                     high_price: float = None, low_price: float = None,
                     close_price: float = None, volume: int = None):
        """Insert price data for a ticker"""
        with get_db_session() as session:
            # Parse date string to object if needed
            if isinstance(date_str, str):
                price_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                price_date = date_str
                
            price = session.query(PriceHistory).filter_by(symbol=symbol, date=price_date).first()
            
            if price:
                if open_price: price.open_price = open_price
                if high_price: price.high_price = high_price
                if low_price: price.low_price = low_price
                if close_price: price.close_price = close_price
                if volume: price.volume = volume
            else:
                price = PriceHistory(
                    symbol=symbol, date=price_date,
                    open_price=open_price, high_price=high_price,
                    low_price=low_price, close_price=close_price,
                    volume=volume
                )
                session.add(price)
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get price history for a ticker"""
        with get_db_session() as session:
            history = session.query(PriceHistory).filter_by(symbol=symbol)\
                .order_by(desc(PriceHistory.date))\
                .limit(days).all()
                
            return [{
                'date': h.date.strftime('%Y-%m-%d'),
                'open_price': h.open_price,
                'high_price': h.high_price,
                'low_price': h.low_price,
                'close_price': h.close_price,
                'volume': h.volume
            } for h in history]
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get the latest price for a ticker"""
        with get_db_session() as session:
            price = session.query(PriceHistory).filter_by(symbol=symbol)\
                .order_by(desc(PriceHistory.date)).first()
            
            if price:
                return {
                    'date': price.date.strftime('%Y-%m-%d'),
                    'close_price': price.close_price,
                    'volume': price.volume,
                    'high_price': price.high_price,
                    'low_price': price.low_price,
                    'open_price': price.open_price,
                    'change_percent': 0  # To be calculated separately if needed
                }
            return None
    
    def get_52_week_high_low(self, symbol: str) -> Tuple[float, float]:
        """Get 52-week high and low for a ticker"""
        with get_db_session() as session:
            one_year_ago = datetime.now().date() - timedelta(days=365)
            
            result = session.query(
                func.max(PriceHistory.high_price), 
                func.min(PriceHistory.low_price)
            ).filter(
                PriceHistory.symbol == symbol,
                PriceHistory.date >= one_year_ago
            ).first()
            
            if result:
                return result[0], result[1]
            return None, None
    
    # ==================== ANALYSIS OPERATIONS ====================
    
    def save_analysis(self, symbol: str, date_str: str, rsi: float = None,
                      volume_spike: bool = False, sentiment_score: float = None,
                      buy_score: int = None, recommendation: str = None, notes: str = None):
        """Save analysis results"""
        with get_db_session() as session:
            if isinstance(date_str, str):
                analysis_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                analysis_date = date_str
            
            analysis = session.query(AnalysisResult).filter_by(symbol=symbol, date=analysis_date).first()
            
            if analysis:
                analysis.rsi = rsi
                analysis.volume_spike = 1 if volume_spike else 0
                analysis.sentiment_score = sentiment_score
                analysis.buy_score = buy_score
                analysis.recommendation = recommendation
                analysis.notes = description = notes
            else:
                analysis = AnalysisResult(
                    symbol=symbol, date=analysis_date,
                    rsi=rsi, volume_spike=1 if volume_spike else 0,
                    sentiment_score=sentiment_score, buy_score=buy_score,
                    recommendation=recommendation, notes=notes
                )
                session.add(analysis)

    def save_stock_score(self, symbol: str, scores: Dict):
        """Save 100-point stock score"""
        with get_db_session() as session:
            today = datetime.now().date()
            score = session.query(StockScore).filter_by(symbol=symbol, date=today).first()
            
            total = sum([
                scores.get('financial', 0), scores.get('valuation', 0),
                scores.get('technical', 0), scores.get('sector_macro', 0),
                scores.get('news', 0)
            ])
            
            if total >= 85: rating = "STRONG BUY"
            elif total >= 70: rating = "BUY"
            elif total >= 55: rating = "HOLD"
            elif total >= 40: rating = "REDUCE"
            else: rating = "SELL/AVOID"
            
            details = json.dumps(scores.get('details', {}))
            
            if score:
                score.financial_score = scores.get('financial', 0)
                score.valuation_score = scores.get('valuation', 0)
                score.technical_score = scores.get('technical', 0)
                score.sector_macro_score = scores.get('sector_macro', 0)
                score.news_score = scores.get('news', 0)
                score.total_score = total
                score.rating = rating
                score.score_details = details
            else:
                score = StockScore(
                    symbol=symbol, date=today,
                    financial_score=scores.get('financial', 0),
                    valuation_score=scores.get('valuation', 0),
                    technical_score=scores.get('technical', 0),
                    sector_macro_score=scores.get('sector_macro', 0),
                    news_score=scores.get('news', 0),
                    total_score=total,
                    rating=rating,
                    score_details=details
                )
                session.add(score)
                
    def get_stock_score(self, symbol: str) -> Optional[Dict]:
        """Get latest stock score"""
        with get_db_session() as session:
            score = session.query(StockScore).filter_by(symbol=symbol)\
                .order_by(desc(StockScore.date)).first()
            
            if score:
                # Assuming you want the object attributes as a dict
                return {
                    'symbol': score.symbol,
                    'date': score.date.strftime('%Y-%m-%d'),
                    'total_score': score.total_score,
                    'rating': score.rating,
                    'technical_score': score.technical_score,
                    'fundamental_score': score.financial_score + score.valuation_score, # Approximation
                    'sentiment_score': score.news_score,
                    'momentum_score': score.technical_score, # Approximation
                    'details': json.loads(score.score_details) if score.score_details else {}
                }
            return None

    # ==================== FUNDAMENTALS OPERATIONS ====================
    
    def save_fundamentals(self, symbol: str, data: Dict):
        """Save fundamental data"""
        with get_db_session() as session:
            # Import Fundamentals model inside method to avoid circular import issues if any
            # (Though top-level import is better, adhering to file structure)
            from database.models import Fundamentals # Assuming model name is Fundamentals
            
            # Check for today's entry (or update latest)
            # Actually fundamentals don't change daily, but we can store snapshots
            # Or just update a single record per symbol?
            # Model definition had 'date', so typically snapshot.
            
            today = datetime.now().date()
            fund = session.query(Fundamentals).filter_by(symbol=symbol, date=today).first()
            
            if fund:
                fund.eps = data.get('eps')
                fund.pe_ratio = data.get('pe_ratio')
                fund.pb_ratio = data.get('pb_ratio')
                fund.roe = data.get('roe')
                fund.net_margin = data.get('net_margin')
                fund.market_cap = data.get('market_cap')
                fund.dividend_yield = data.get('dividend_yield')
            else:
                fund = Fundamentals(
                    symbol=symbol,
                    date=today,
                    eps=data.get('eps'),
                    pe_ratio=data.get('pe_ratio'),
                    pb_ratio=data.get('pb_ratio'),
                    roe=data.get('roe'),
                    net_margin=data.get('net_margin'),
                    market_cap=data.get('market_cap'),
                    dividend_yield=data.get('dividend_yield')
                )
                session.add(fund)

    def get_latest_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get latest fundamentals"""
        with get_db_session() as session:
            from database.models import Fundamentals
            fund = session.query(Fundamentals).filter_by(symbol=symbol)\
                .order_by(desc(Fundamentals.date)).first()
            
            if fund:
                return {
                    'eps': fund.eps,
                    'pe_ratio': fund.pe_ratio,
                    'pb_ratio': fund.pb_ratio,
                    'roe': fund.roe,
                    'net_margin': fund.net_margin,
                    'market_cap': fund.market_cap,
                    'dividend_yield': fund.dividend_yield
                }
            return {}

    # ==================== TECHNICAL INDICATORS ====================

    def save_technical_indicators(self, symbol: str, indicators: Dict):
        """Save technical indicators"""
        with get_db_session() as session:
            today = datetime.now().date()
            tech = session.query(TechnicalIndicator).filter_by(symbol=symbol, date=today).first()
            
            if tech:
                tech.ma_10 = indicators.get('ma_10')
                tech.ma_50 = indicators.get('ma_50')
                tech.ma_200 = indicators.get('ma_200')
                tech.rsi = indicators.get('rsi')
                tech.macd = indicators.get('macd')
                tech.macd_signal = indicators.get('macd_signal')
                tech.macd_histogram = indicators.get('macd_histogram')
                tech.bollinger_upper = indicators.get('bollinger_upper')
                tech.bollinger_middle = indicators.get('bollinger_middle')
                tech.bollinger_lower = indicators.get('bollinger_lower')
                tech.support_level = indicators.get('support_level')
                tech.resistance_level = indicators.get('resistance_level')
                tech.trend = indicators.get('trend')
            else:
                tech = TechnicalIndicator(
                    symbol=symbol, date=today,
                    ma_10=indicators.get('ma_10'),
                    ma_50=indicators.get('ma_50'),
                    ma_200=indicators.get('ma_200'),
                    rsi=indicators.get('rsi'),
                    macd=indicators.get('macd'),
                    macd_signal=indicators.get('macd_signal'),
                    macd_histogram=indicators.get('macd_histogram'),
                    bollinger_upper=indicators.get('bollinger_upper'),
                    bollinger_middle=indicators.get('bollinger_middle'),
                    bollinger_lower=indicators.get('bollinger_lower'),
                    support_level=indicators.get('support_level'),
                    resistance_level=indicators.get('resistance_level'),
                    trend=indicators.get('trend')
                )
                session.add(tech)

    def get_technical_indicators(self, symbol: str) -> Optional[Dict]:
        """Get latest technical indicators"""
        with get_db_session() as session:
            tech = session.query(TechnicalIndicator).filter_by(symbol=symbol)\
                .order_by(desc(TechnicalIndicator.date)).first()
            
            if tech:
                return {
                    'rsi': tech.rsi,
                    'sma_20': tech.bollinger_middle,
                    'sma_50': tech.ma_50,
                    'macd': tech.macd,
                    'macd_signal': tech.macd_signal,
                    'support': tech.support_level,
                    'resistance': tech.resistance_level
                }
            return None

    # ==================== REPORT HISTORY ====================

    def save_report_history(self, report_type: str, file_path: str = None, 
                           recipients: str = None, status: str = 'sent'):
        """Save report history"""
        with get_db_session() as session:
            history = ReportHistory(
                report_type=report_type,
                date=datetime.now().date(),
                sent_at=datetime.now(),
                recipients=recipients,
                file_path=file_path,
                status=status
            )
            session.add(history)

    # ==================== AI DECISIONS ====================
    
    def save_ai_decisions(self, decisions: List[Dict]):
        """Save AI analysis results"""
        with get_db_session() as session:
            for d in decisions:
                # Upsert based on symbol + date
                existing = session.query(AIDecision).filter_by(
                    symbol=d['ticker'], 
                    date=datetime.now().date()
                ).first()
                
                if existing:
                    existing.action = d.get('action')
                    existing.conviction = d.get('conviction')
                    existing.score = d.get('score')
                    existing.reasoning = d.get('reasoning')
                    existing.catalyst = d.get('catalyst')
                    existing.created_at = datetime.utcnow()
                else:
                    new_decision = AIDecision(
                        symbol=d['ticker'],
                        date=datetime.now().date(),
                        action=d.get('action'),
                        conviction=d.get('conviction'),
                        score=d.get('score'),
                        reasoning=d.get('reasoning'),
                        catalyst=d.get('catalyst')
                    )
                    session.add(new_decision)

# Singleton instance
db = DBManager()
