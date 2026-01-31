"""
PSX Research Analyst - Database Manager
CRUD operations for all database tables including global markets,
sector indices, alerts, stock scores, and technical indicators
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import get_connection, init_database


class DBManager:
    """Database manager for PSX Research Analyst"""
    
    def __init__(self):
        """Initialize database manager and ensure tables exist"""
        init_database()
    
    # ==================== TICKER OPERATIONS ====================
    
    def upsert_ticker(self, symbol: str, name: str, sector: str = None):
        """Insert or update a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickers (symbol, name, sector, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                name = excluded.name,
                sector = COALESCE(excluded.sector, tickers.sector),
                last_updated = excluded.last_updated
        """, (symbol, name, sector, datetime.now()))
        conn.commit()
        conn.close()
    
    def bulk_upsert_tickers(self, tickers: List[Dict]):
        """Bulk insert or update tickers"""
        conn = get_connection()
        cursor = conn.cursor()
        for ticker in tickers:
            cursor.execute("""
                INSERT INTO tickers (symbol, name, sector, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name = excluded.name,
                    last_updated = excluded.last_updated
            """, (ticker['symbol'], ticker['name'], ticker.get('sector'), datetime.now()))
        conn.commit()
        conn.close()
    
    def get_all_tickers(self) -> List[Dict]:
        """Get all active tickers"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, name, sector FROM tickers WHERE is_active = 1")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get a specific ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, name, sector FROM tickers WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # ==================== PRICE OPERATIONS ====================
    
    def insert_price(self, symbol: str, date: str, open_price: float = None,
                     high_price: float = None, low_price: float = None,
                     close_price: float = None, volume: int = None):
        """Insert price data for a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO price_history (symbol, date, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, date) DO UPDATE SET
                    open_price = COALESCE(excluded.open_price, price_history.open_price),
                    high_price = COALESCE(excluded.high_price, price_history.high_price),
                    low_price = COALESCE(excluded.low_price, price_history.low_price),
                    close_price = COALESCE(excluded.close_price, price_history.close_price),
                    volume = COALESCE(excluded.volume, price_history.volume)
            """, (symbol, date, open_price, high_price, low_price, close_price, volume))
            conn.commit()
        except Exception as e:
            print(f"Error inserting price for {symbol}: {e}")
        finally:
            conn.close()
    
    def get_price_history(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get price history for a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, open_price, high_price, low_price, close_price, volume
            FROM price_history
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
        """, (symbol, days))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get the latest price for a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, close_price, volume, high_price, low_price, open_price
            FROM price_history
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
        """, (symbol,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_52_week_high_low(self, symbol: str) -> Tuple[float, float]:
        """Get 52-week high and low for a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT MAX(high_price) as high_52w, MIN(low_price) as low_52w
            FROM price_history
            WHERE symbol = ? AND date >= ?
        """, (symbol, one_year_ago))
        row = cursor.fetchone()
        conn.close()
        if row and row['high_52w']:
            return row['high_52w'], row['low_52w']
        return None, None
    
    # ==================== ANNOUNCEMENT OPERATIONS ====================
    
    def insert_announcement(self, symbol: str, headline: str, content: str = None,
                           pdf_url: str = None, announcement_type: str = None,
                           announcement_date: str = None) -> bool:
        """Insert an announcement if it doesn't exist (deduplication)"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO announcements (symbol, headline, content, pdf_url, announcement_type, announcement_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol, headline, content, pdf_url, announcement_type, 
                  announcement_date or datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_recent_announcements(self, symbol: str = None, days: int = 7) -> List[Dict]:
        """Get recent announcements, optionally filtered by symbol"""
        conn = get_connection()
        cursor = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if symbol:
            cursor.execute("""
                SELECT id, symbol, headline, content, pdf_url, announcement_type, 
                       announcement_date, sentiment_score, processed
                FROM announcements
                WHERE symbol = ? AND announcement_date >= ?
                ORDER BY announcement_date DESC
            """, (symbol, since_date))
        else:
            cursor.execute("""
                SELECT id, symbol, headline, content, pdf_url, announcement_type,
                       announcement_date, sentiment_score, processed
                FROM announcements
                WHERE announcement_date >= ?
                ORDER BY announcement_date DESC
            """, (since_date,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_unprocessed_announcements(self) -> List[Dict]:
        """Get announcements that haven't been sentiment analyzed"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, symbol, headline, content
            FROM announcements
            WHERE processed = 0
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_announcement_sentiment(self, announcement_id: int, sentiment_score: float):
        """Update sentiment score for an announcement"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE announcements
            SET sentiment_score = ?, processed = 1
            WHERE id = ?
        """, (sentiment_score, announcement_id))
        conn.commit()
        conn.close()
    
    # ==================== ANALYSIS OPERATIONS ====================
    
    def save_analysis(self, symbol: str, date: str, rsi: float = None,
                      volume_spike: bool = False, sentiment_score: float = None,
                      buy_score: int = None, recommendation: str = None, notes: str = None):
        """Save analysis results for a ticker"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_results (symbol, date, rsi, volume_spike, sentiment_score, 
                                         buy_score, recommendation, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                rsi = excluded.rsi,
                volume_spike = excluded.volume_spike,
                sentiment_score = excluded.sentiment_score,
                buy_score = excluded.buy_score,
                recommendation = excluded.recommendation,
                notes = excluded.notes
        """, (symbol, date, rsi, 1 if volume_spike else 0, sentiment_score,
              buy_score, recommendation, notes))
        conn.commit()
        conn.close()
    
    def get_today_analysis(self) -> List[Dict]:
        """Get all analysis results for today"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT ar.*, t.name as company_name
            FROM analysis_results ar
            JOIN tickers t ON ar.symbol = t.symbol
            WHERE ar.date = ?
            ORDER BY ar.buy_score DESC
        """, (today,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_top_opportunities(self, limit: int = 5) -> List[Dict]:
        """Get top buy opportunities from today's analysis"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT ar.*, t.name as company_name
            FROM analysis_results ar
            JOIN tickers t ON ar.symbol = t.symbol
            WHERE ar.date = ?
            ORDER BY ar.buy_score DESC
            LIMIT ?
        """, (today, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_red_alerts(self, threshold: int = 4) -> List[Dict]:
        """Get stocks with sell signals (low buy scores)"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT ar.*, t.name as company_name
            FROM analysis_results ar
            JOIN tickers t ON ar.symbol = t.symbol
            WHERE ar.date = ? AND ar.buy_score <= ?
            ORDER BY ar.buy_score ASC
            LIMIT 10
        """, (today, threshold))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_watchlist_analysis(self, watchlist: List[str]) -> List[Dict]:
        """Get analysis for watchlist stocks"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        placeholders = ','.join('?' * len(watchlist))
        cursor.execute(f"""
            SELECT ar.*, t.name as company_name
            FROM analysis_results ar
            JOIN tickers t ON ar.symbol = t.symbol
            WHERE ar.date = ? AND ar.symbol IN ({placeholders})
        """, [today] + watchlist)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== GLOBAL MARKETS OPERATIONS ====================
    
    def save_global_markets(self, data: Dict):
        """Save global market data"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO global_markets (
                date, sp500, sp500_change, nasdaq, nasdaq_change, dow, dow_change,
                nikkei, nikkei_change, hang_seng, hang_seng_change, shanghai, shanghai_change,
                wti_oil, wti_change, brent_oil, brent_change, usd_pkr, usd_pkr_change,
                gold, gold_change
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                sp500 = excluded.sp500, sp500_change = excluded.sp500_change,
                nasdaq = excluded.nasdaq, nasdaq_change = excluded.nasdaq_change,
                dow = excluded.dow, dow_change = excluded.dow_change,
                nikkei = excluded.nikkei, nikkei_change = excluded.nikkei_change,
                hang_seng = excluded.hang_seng, hang_seng_change = excluded.hang_seng_change,
                shanghai = excluded.shanghai, shanghai_change = excluded.shanghai_change,
                wti_oil = excluded.wti_oil, wti_change = excluded.wti_change,
                brent_oil = excluded.brent_oil, brent_change = excluded.brent_change,
                usd_pkr = excluded.usd_pkr, usd_pkr_change = excluded.usd_pkr_change,
                gold = excluded.gold, gold_change = excluded.gold_change
        """, (
            today,
            data.get('sp500'), data.get('sp500_change'),
            data.get('nasdaq'), data.get('nasdaq_change'),
            data.get('dow'), data.get('dow_change'),
            data.get('nikkei'), data.get('nikkei_change'),
            data.get('hang_seng'), data.get('hang_seng_change'),
            data.get('shanghai'), data.get('shanghai_change'),
            data.get('wti_oil'), data.get('wti_change'),
            data.get('brent_oil'), data.get('brent_change'),
            data.get('usd_pkr'), data.get('usd_pkr_change'),
            data.get('gold'), data.get('gold_change')
        ))
        conn.commit()
        conn.close()
    
    def get_latest_global_markets(self) -> Optional[Dict]:
        """Get latest global market data"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM global_markets ORDER BY date DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== KSE-100 INDEX OPERATIONS ====================
    
    def save_kse100_index(self, data: Dict):
        """Save KSE-100 index data"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO kse100_index (
                date, open_value, high_value, low_value, close_value,
                change_value, change_percent, volume, value_traded,
                advancing, declining, unchanged
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                open_value = excluded.open_value,
                high_value = excluded.high_value,
                low_value = excluded.low_value,
                close_value = excluded.close_value,
                change_value = excluded.change_value,
                change_percent = excluded.change_percent,
                volume = excluded.volume,
                value_traded = excluded.value_traded,
                advancing = excluded.advancing,
                declining = excluded.declining,
                unchanged = excluded.unchanged
        """, (
            today,
            data.get('open_value'), data.get('high_value'),
            data.get('low_value'), data.get('close_value'),
            data.get('change_value'), data.get('change_percent'),
            data.get('volume'), data.get('value_traded'),
            data.get('advancing'), data.get('declining'), data.get('unchanged')
        ))
        conn.commit()
        conn.close()
    
    def get_kse100_history(self, days: int = 30) -> List[Dict]:
        """Get KSE-100 index history"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM kse100_index ORDER BY date DESC LIMIT ?
        """, (days,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_latest_kse100(self) -> Optional[Dict]:
        """Get latest KSE-100 data"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kse100_index ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== SECTOR INDEX OPERATIONS ====================
    
    def save_sector_index(self, sector: str, data: Dict):
        """Save sector index data"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO sector_indices (
                date, sector, index_value, change_value, change_percent,
                top_gainer, top_loser
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, sector) DO UPDATE SET
                index_value = excluded.index_value,
                change_value = excluded.change_value,
                change_percent = excluded.change_percent,
                top_gainer = excluded.top_gainer,
                top_loser = excluded.top_loser
        """, (
            today, sector,
            data.get('index_value'), data.get('change_value'),
            data.get('change_percent'), data.get('top_gainer'), data.get('top_loser')
        ))
        conn.commit()
        conn.close()
    
    def get_sector_indices(self, date: str = None) -> List[Dict]:
        """Get all sector indices for a date"""
        conn = get_connection()
        cursor = conn.cursor()
        target_date = date or datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT * FROM sector_indices WHERE date = ? ORDER BY change_percent DESC
        """, (target_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== NEWS OPERATIONS ====================
    
    def save_news(self, headline: str, source: str, url: str = None,
                  category: str = None, sentiment_score: float = None,
                  impact_level: str = None, related_symbols: List[str] = None):
        """Save news headline"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        symbols_str = ','.join(related_symbols) if related_symbols else None
        try:
            cursor.execute("""
                INSERT INTO news_headlines (
                    date, source, headline, url, category, sentiment_score,
                    impact_level, related_symbols
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (today, source, headline, url, category, sentiment_score,
                  impact_level, symbols_str))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Duplicate headline
        finally:
            conn.close()
    
    def get_recent_news(self, days: int = 1) -> List[Dict]:
        """Get recent news headlines"""
        conn = get_connection()
        cursor = conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT * FROM news_headlines WHERE date >= ? ORDER BY created_at DESC
        """, (since_date,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== ALERT OPERATIONS ====================
    
    def save_alert(self, alert_type: str, message: str, symbol: str = None,
                   trigger_value: float = None, threshold_value: float = None,
                   channel: str = 'email'):
        """Save alert to history"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts_history (
                alert_type, symbol, message, trigger_value, threshold_value, channel
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (alert_type, symbol, message, trigger_value, threshold_value, channel))
        conn.commit()
        conn.close()
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        conn = get_connection()
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT * FROM alerts_history WHERE sent_at >= ? ORDER BY sent_at DESC
        """, (since,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 100-POINT STOCK SCORE OPERATIONS ====================
    
    def save_stock_score(self, symbol: str, scores: Dict):
        """Save 100-point stock score"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        total = sum([
            scores.get('financial', 0),
            scores.get('valuation', 0),
            scores.get('technical', 0),
            scores.get('sector_macro', 0),
            scores.get('news', 0)
        ])
        
        # Determine rating
        if total >= 85:
            rating = "STRONG BUY"
        elif total >= 70:
            rating = "BUY"
        elif total >= 55:
            rating = "HOLD"
        elif total >= 40:
            rating = "REDUCE"
        else:
            rating = "SELL/AVOID"
        
        cursor.execute("""
            INSERT INTO stock_scores (
                symbol, date, financial_score, valuation_score, technical_score,
                sector_macro_score, news_score, total_score, rating, score_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                financial_score = excluded.financial_score,
                valuation_score = excluded.valuation_score,
                technical_score = excluded.technical_score,
                sector_macro_score = excluded.sector_macro_score,
                news_score = excluded.news_score,
                total_score = excluded.total_score,
                rating = excluded.rating,
                score_details = excluded.score_details
        """, (
            symbol, today,
            scores.get('financial', 0), scores.get('valuation', 0),
            scores.get('technical', 0), scores.get('sector_macro', 0),
            scores.get('news', 0), total, rating,
            json.dumps(scores.get('details', {}))
        ))
        conn.commit()
        conn.close()
    
    def get_stock_scores(self, date: str = None, limit: int = 50) -> List[Dict]:
        """Get stock scores for a date"""
        conn = get_connection()
        cursor = conn.cursor()
        target_date = date or datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT ss.*, t.name as company_name
            FROM stock_scores ss
            LEFT JOIN tickers t ON ss.symbol = t.symbol
            WHERE ss.date = ?
            ORDER BY ss.total_score DESC
            LIMIT ?
        """, (target_date, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== TECHNICAL INDICATORS OPERATIONS ====================
    
    def save_technical_indicators(self, symbol: str, indicators: Dict):
        """Save technical indicators for a symbol"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO technical_indicators (
                symbol, date, ma_10, ma_50, ma_200, rsi, macd, macd_signal,
                macd_histogram, bollinger_upper, bollinger_middle, bollinger_lower,
                support_level, resistance_level, trend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                ma_10 = excluded.ma_10, ma_50 = excluded.ma_50, ma_200 = excluded.ma_200,
                rsi = excluded.rsi, macd = excluded.macd, macd_signal = excluded.macd_signal,
                macd_histogram = excluded.macd_histogram,
                bollinger_upper = excluded.bollinger_upper,
                bollinger_middle = excluded.bollinger_middle,
                bollinger_lower = excluded.bollinger_lower,
                support_level = excluded.support_level,
                resistance_level = excluded.resistance_level,
                trend = excluded.trend
        """, (
            symbol, today,
            indicators.get('ma_10'), indicators.get('ma_50'), indicators.get('ma_200'),
            indicators.get('rsi'), indicators.get('macd'), indicators.get('macd_signal'),
            indicators.get('macd_histogram'),
            indicators.get('bollinger_upper'), indicators.get('bollinger_middle'),
            indicators.get('bollinger_lower'),
            indicators.get('support_level'), indicators.get('resistance_level'),
            indicators.get('trend')
        ))
        conn.commit()
        conn.close()
    
    def get_technical_indicators(self, symbol: str) -> Optional[Dict]:
        """Get latest technical indicators for a symbol"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM technical_indicators
            WHERE symbol = ?
            ORDER BY date DESC LIMIT 1
        """, (symbol,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== REPORT HISTORY ====================
    
    def save_report_history(self, report_type: str, file_path: str = None,
                           recipients: str = None, status: str = 'sent'):
        """Save report generation history"""
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO report_history (
                report_type, date, sent_at, recipients, file_path, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (report_type, today, datetime.now(), recipients, file_path, status))
        conn.commit()
        conn.close()


# Singleton instance
db = DBManager()
