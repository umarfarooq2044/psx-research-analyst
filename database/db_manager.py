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
    ReportHistory, AlertHistory, Fundamentals, AIDecision, LeverageData
)

class DBManager:
    """Database manager for PSX Research Analyst (ORM version)"""
    
    def __init__(self):
        """Initialize database manager"""
        # Ensure tables exist on startup
        init_database()
        
    def _ensure_ticker_exists(self, session, symbol: str):
        """Helper to ensure a ticker exists before inserting related data (FK safety)"""
        ticker = session.query(Ticker).filter_by(symbol=symbol).first()
        if not ticker:
            # Auto-register missing ticker to satisfy Foreign Key constraints
            new_ticker = Ticker(symbol=symbol, name=symbol, is_active=1)
            session.add(new_ticker)
            session.flush() # Ensure it's in the DB before proceeding
    
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
            # FK safety
            self._ensure_ticker_exists(session, symbol)
            
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

    def bulk_upsert_prices(self, price_records: List[Dict]):
        """Bulk insert or update price records for a single date"""
        if not price_records:
            return
            
        with get_db_session() as session:
            today = datetime.now().date()
            
            # FK safety: Ensure all symbols exist
            symbols = [p['symbol'] for p in price_records]
            for sym in set(symbols):
                self._ensure_ticker_exists(session, sym)
            
            # Fetch all existing prices for these symbols on this date to minimize queries
            symbols = [p['symbol'] for p in price_records]
            existing_prices = session.query(PriceHistory).filter(
                PriceHistory.symbol.in_(symbols),
                PriceHistory.date == today
            ).all()
            
            existing_map = {p.symbol: p for p in existing_prices}
            
            for p_data in price_records:
                sym = p_data['symbol']
                if sym in existing_map:
                    price_obj = existing_map[sym]
                    if 'open_price' in p_data: price_obj.open_price = p_data['open_price']
                    if 'high_price' in p_data: price_obj.high_price = p_data['high_price']
                    if 'low_price' in p_data: price_obj.low_price = p_data['low_price']
                    if 'close_price' in p_data: price_obj.close_price = p_data['close_price']
                    if 'volume' in p_data: price_obj.volume = p_data['volume']
                else:
                    new_price = PriceHistory(
                        symbol=sym,
                        date=today,
                        open_price=p_data.get('open_price'),
                        high_price=p_data.get('high_price'),
                        low_price=p_data.get('low_price'),
                        close_price=p_data.get('close_price'),
                        volume=p_data.get('volume')
                    )
                    session.add(new_price)
            
            # Commit happens automatically with get_db_session() context manager
    
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
    
    def get_latest_kse100(self) -> Optional[Dict]:
        """Get latest KSE-100 index data"""
        with get_db_session() as session:
            h = session.query(KSE100Index).order_by(desc(KSE100Index.date)).first()
            if h:
                return {
                    'date': h.date.strftime('%Y-%m-%d'),
                    'close_value': h.close_value,
                    'change_percent': h.change_percent,
                    'volume': h.volume,
                    'advancing': h.advancing,
                    'declining': h.declining,
                    'sentiment': h.sentiment
                }
            return None

    def save_kse100_index(self, data: Dict):
        """Save KSE-100 index data"""
        with get_db_session() as session:
            today = datetime.now().date()
            index = session.query(KSE100Index).filter_by(date=today).first()
            
            if index:
                index.close_value = data.get('close_value')
                index.change_percent = data.get('change_percent')
                index.volume = data.get('volume')
                index.advancing = data.get('advancing')
                index.declining = data.get('declining')
                index.sentiment = data.get('sentiment')
            else:
                index = KSE100Index(
                    date=today,
                    close_value=data.get('close_value'),
                    change_percent=data.get('change_percent'),
                    volume=data.get('volume'),
                    advancing=data.get('advancing'),
                    declining=data.get('declining'),
                    sentiment=data.get('sentiment')
                )
                session.add(index)

    def get_kse100_history(self, days: int = 30) -> List[Dict]:
        """Get KSE-100 history"""
        with get_db_session() as session:
            history = session.query(KSE100Index).order_by(desc(KSE100Index.date)).limit(days).all()
            return [{
                'date': h.date.strftime('%Y-%m-%d'),
                'close_value': h.close_value,
                'change_percent': h.change_percent,
                'volume': h.volume,
                'advancing': h.advancing,
                'declining': h.declining,
                'high_value': h.close_value, 
                'low_value': h.close_value
            } for h in history]

    def get_sector_indices(self) -> List[Dict]:
        """Get all sector indices"""
        with get_db_session() as session:
            sectors = session.query(SectorIndex).all()
            return [{
                'sector': s.sector,
                'index_value': s.index_value,
                'change_percent': s.change_percent
            } for s in sectors]

    def save_sector_index(self, sector: str, index_value: float, change_percent: float = 0):
        """Save sector index data"""
        with get_db_session() as session:
            today = datetime.now().date()
            idx = session.query(SectorIndex).filter_by(sector=sector, date=today).first()
            
            if idx:
                idx.index_value = index_value
                idx.change_percent = change_percent
            else:
                idx = SectorIndex(
                    sector=sector,
                    date=today,
                    index_value=index_value,
                    change_percent=change_percent
                )
                session.add(idx)
    
    def save_analysis(self, symbol: str, date_str: str, rsi: float = None,
                      volume_spike: bool = False, sentiment_score: float = None,
                      buy_score: int = None, recommendation: str = None, notes: str = None):
        """Save analysis results"""
        with get_db_session() as session:
            self._ensure_ticker_exists(session, symbol)
            
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
            self._ensure_ticker_exists(session, symbol)
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

    def get_stock_scores(self, limit: int = 20) -> List[Dict]:
        """Get top stock scores"""
        with get_db_session() as session:
            scores = session.query(StockScore).order_by(desc(StockScore.total_score)).limit(limit).all()
            return [{
                'symbol': s.symbol,
                'total_score': s.total_score,
                'rating': s.rating,
                'components': json.loads(s.score_details) if s.score_details else {}
            } for s in scores]
    
    def save_fundamentals(self, symbol: str, data: Dict):
        """Save fundamental data"""
        with get_db_session() as session:
            self._ensure_ticker_exists(session, symbol)
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
            self._ensure_ticker_exists(session, symbol)
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
                    trend=indicators.get('trend'),
                    obv=indicators.get('obv'),
                    accumulation_distribution=indicators.get('accumulation_distribution'),
                    atr=indicators.get('atr'),
                    volume_acceleration=indicators.get('volume_acceleration')
                )
                session.add(tech)

    def save_leverage_data(self, symbol: str, data: Dict):
        """Save MTS and Futures Open Interest data"""
        with get_db_session() as session:
            self._ensure_ticker_exists(session, symbol)
            today = datetime.now().date()
            leverage = session.query(LeverageData).filter_by(symbol=symbol, date=today).first()
            
            if leverage:
                leverage.mts_volume = data.get('mts_volume')
                leverage.mts_amount = data.get('mts_amount')
                leverage.futures_oi = data.get('futures_oi')
                leverage.futures_oi_change = data.get('futures_oi_change')
                leverage.leverage_ratio = data.get('leverage_ratio')
                leverage.risk_level = data.get('risk_level')
            else:
                leverage = LeverageData(
                    symbol=symbol, date=today,
                    mts_volume=data.get('mts_volume'),
                    mts_amount=data.get('mts_amount'),
                    futures_oi=data.get('futures_oi'),
                    futures_oi_change=data.get('futures_oi_change'),
                    leverage_ratio=data.get('leverage_ratio'),
                    risk_level=data.get('risk_level')
                )
                session.add(leverage)

    def get_latest_leverage(self, symbol: str) -> Optional[Dict]:
        """Get latest leverage data for a ticker"""
        with get_db_session() as session:
            leverage = session.query(LeverageData).filter_by(symbol=symbol)\
                .order_by(desc(LeverageData.date)).first()
            
            if leverage:
                return {
                    'mts_volume': leverage.mts_volume,
                    'futures_oi': leverage.futures_oi,
                    'leverage_ratio': leverage.leverage_ratio,
                    'risk_level': leverage.risk_level
                }
            return None

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
                    'resistance': tech.resistance_level,
                    'obv': tech.obv,
                    'ad': tech.accumulation_distribution,
                    'atr': tech.atr,
                    'volume_accel': tech.volume_acceleration
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
                self._ensure_ticker_exists(session, d['ticker'])
                # Upsert based on symbol + date
                existing = session.query(AIDecision).filter_by(
                    symbol=d['ticker'], 
                    date=datetime.now().date()
                ).first()
                
                # Normalize keys (SMI-v1 uses 'signal', 'future_path', 'black_swan')
                action_val = d.get('signal') or d.get('action')
                
                if existing:
                    existing.action = action_val
                    existing.conviction = d.get('conviction')
                    existing.score = d.get('score', 0)
                    existing.reasoning = d.get('reasoning')
                    existing.future_path = d.get('future_path')
                    existing.black_swan = d.get('black_swan')
                    existing.catalyst = d.get('catalyst')
                    existing.created_at = datetime.utcnow()
                else:
                    new_decision = AIDecision(
                        symbol=d['ticker'],
                        date=datetime.now().date(),
                        action=action_val,
                        conviction=d.get('conviction'),
                        score=d.get('score', 0),
                        reasoning=d.get('reasoning'),
                        future_path=d.get('future_path'),
                        black_swan=d.get('black_swan'),
                        catalyst=d.get('catalyst')
                    )
                    session.add(new_decision)

    def get_recent_ai_decisions(self, limit: int = 10) -> List[Dict]:
        """Get latest AI decisions"""
        with get_db_session() as session:
            decisions = session.query(AIDecision).order_by(desc(AIDecision.date), desc(AIDecision.id)).limit(limit).all()
            return [{
                'symbol': d.symbol,
                'date': d.date.strftime('%Y-%m-%d'),
                'action': d.action,
                'conviction': d.conviction,
                'score': d.score,
                'reasoning': d.reasoning,
                'future_path': d.future_path,
                'black_swan': d.black_swan,
                'catalyst': d.catalyst
            } for d in decisions]

    def save_global_markets(self, data: Dict):
        """Save or update global market data for today"""
        with get_db_session() as session:
            today = datetime.now().date()
            gm = session.query(GlobalMarket).filter_by(date=today).first()
            
            if gm:
                # Update existing
                if data.get('sp500'): gm.sp500 = data['sp500']
                if data.get('sp500_change'): gm.sp500_change = data['sp500_change']
                if data.get('nasdaq'): gm.nasdaq = data['nasdaq']
                if data.get('nasdaq_change'): gm.nasdaq_change = data['nasdaq_change']
                if data.get('dow'): gm.dow = data['dow']
                if data.get('dow_change'): gm.dow_change = data['dow_change']
                if data.get('nikkei'): gm.nikkei = data['nikkei']
                if data.get('nikkei_change'): gm.nikkei_change = data['nikkei_change']
                if data.get('hang_seng'): gm.hang_seng = data['hang_seng']
                if data.get('hang_seng_change'): gm.hang_seng_change = data['hang_seng_change']
                if data.get('shanghai'): gm.shanghai = data['shanghai']
                if data.get('shanghai_change'): gm.shanghai_change = data['shanghai_change']
                if data.get('wti_oil'): gm.wti_oil = data['wti_oil']
                if data.get('wti_change'): gm.wti_change = data['wti_change']
                if data.get('brent_oil'): gm.brent_oil = data['brent_oil']
                if data.get('brent_change'): gm.brent_change = data['brent_change']
                if data.get('usd_pkr'): gm.usd_pkr = data['usd_pkr']
                if data.get('usd_pkr_change'): gm.usd_pkr_change = data['usd_pkr_change']
                if data.get('gold'): gm.gold = data['gold']
                if data.get('gold_change'): gm.gold_change = data['gold_change']
            else:
                # Create new
                gm = GlobalMarket(
                    date=today,
                    sp500=data.get('sp500'),
                    sp500_change=data.get('sp500_change'),
                    nasdaq=data.get('nasdaq'),
                    nasdaq_change=data.get('nasdaq_change'),
                    dow=data.get('dow'),
                    dow_change=data.get('dow_change'),
                    nikkei=data.get('nikkei'),
                    nikkei_change=data.get('nikkei_change'),
                    hang_seng=data.get('hang_seng'),
                    hang_seng_change=data.get('hang_seng_change'),
                    shanghai=data.get('shanghai'),
                    shanghai_change=data.get('shanghai_change'),
                    wti_oil=data.get('wti_oil'),
                    wti_change=data.get('wti_change'),
                    brent_oil=data.get('brent_oil'),
                    brent_change=data.get('brent_change'),
                    usd_pkr=data.get('usd_pkr'),
                    usd_pkr_change=data.get('usd_pkr_change'),
                    gold=data.get('gold'),
                    gold_change=data.get('gold_change')
                )
                session.add(gm)

    def get_latest_global_markets(self) -> Optional[Dict]:
        """Get latest global market data"""
        with get_db_session() as session:
            gm = session.query(GlobalMarket).order_by(desc(GlobalMarket.date)).first()
            if gm:
                return {
                    'date': gm.date.strftime('%Y-%m-%d'),
                    'sp500': gm.sp500,
                    'sp500_change': gm.sp500_change,
                    'nasdaq': gm.nasdaq,
                    'nasdaq_change': gm.nasdaq_change,
                    'dow': gm.dow,
                    'dow_change': gm.dow_change,
                    'nikkei': gm.nikkei,
                    'nikkei_change': gm.nikkei_change,
                    'hang_seng': gm.hang_seng,
                    'hang_seng_change': gm.hang_seng_change,
                    'shanghai': gm.shanghai,
                    'shanghai_change': gm.shanghai_change,
                    'wti_oil': gm.wti_oil,
                    'wti_change': gm.wti_change,
                    'brent_oil': gm.brent_oil,
                    'brent_change': gm.brent_change,
                    'usd_pkr': gm.usd_pkr,
                    'usd_pkr_change': gm.usd_pkr_change,
                    'gold': gm.gold,
                    'gold_change': gm.gold_change
                }
            return None

    def insert_announcement(self, symbol: str, headline: str, pdf_url: str = None, 
                            announcement_type: str = None, announcement_date: str = None) -> bool:
        """Insert a corporate announcement, avoid duplicates based on symbol + headline"""
        with get_db_session() as session:
            self._ensure_ticker_exists(session, symbol)
            # Check for existing
            existing = session.query(Announcement).filter_by(
                symbol=symbol, 
                headline=headline
            ).first()
            
            if existing:
                return False
            
            # Create new
            new_ann = Announcement(
                symbol=symbol,
                headline=headline,
                pdf_url=pdf_url,
                announcement_type=announcement_type,
                announcement_date=datetime.strptime(announcement_date, '%Y-%m-%d').date() if announcement_date else datetime.now().date(),
                created_at=datetime.now()
            )
            session.add(new_ann)
            return True

    def get_recent_announcements(self, symbol: str = None, days: int = 7) -> List[Dict]:
        """Get latest corporate announcements"""
        with get_db_session() as session:
            since = datetime.now() - timedelta(days=days)
            query = session.query(Announcement).filter(
                Announcement.created_at >= since
            )
            
            if symbol:
                query = query.filter_by(symbol=symbol)
                
            announcements = query.order_by(desc(Announcement.created_at)).all()
            
            return [{
                'id': a.id,
                'symbol': a.symbol,
                'headline': a.headline,
                'announcement_type': a.announcement_type,
                'sentiment_score': a.sentiment_score,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for a in announcements]

    def get_unprocessed_announcements(self) -> List[Dict]:
        """Get announcements that haven't been sentiment analyzed"""
        with get_db_session() as session:
            announcements = session.query(Announcement).filter(
                Announcement.sentiment_score == None
            ).all()
            
            return [{
                'id': a.id,
                'symbol': a.symbol,
                'headline': a.headline,
                'announcement_type': a.announcement_type
            } for a in announcements]

    def update_announcement_sentiment(self, announcement_id: int, sentiment: float):
        """Update sentiment score for an announcement"""
        with get_db_session() as session:
            ann = session.query(Announcement).get(announcement_id)
            if ann:
                ann.sentiment_score = sentiment

    def get_recent_news_for_ticker(self, symbol: str, days: int = 7) -> List[str]:
        """Get the last 7 days of news headlines for narrative clustering"""
        with get_db_session() as session:
            since = datetime.now() - timedelta(days=days)
            # Find news where the symbol is mentioned in related_symbols
            headlines = session.query(NewsHeadline).filter(
                NewsHeadline.date >= since,
                NewsHeadline.related_symbols.contains(symbol)
            ).order_by(desc(NewsHeadline.date)).all()
            
            return [h.headline for h in headlines]

# Singleton instance
db = DBManager()
