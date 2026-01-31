"""
PSX Research Analyst - Multi-Schedule Orchestrator
Manages pre-market, mid-day, post-market, and weekly report scheduling
"""
import os
import sys
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCHEDULES, MARKET_OPEN, MARKET_CLOSE
from database.db_manager import db

# Import scrapers
from scraper.ticker_discovery import discover_and_save_tickers
from scraper.price_scraper import fetch_all_prices
from scraper.announcements_scraper import scrape_all_announcements
from scraper.kse100_scraper import get_kse100_summary, get_kse100_support_resistance

# Import global data
from global_data.forex_scraper import fetch_usd_pkr
from global_data.oil_prices import fetch_oil_prices, get_oil_summary
from global_data.global_indices import get_us_markets_summary, get_asian_markets_summary, save_global_markets_data

# Import news
from news.news_scraper import get_market_news_summary

# Import analysis
from analysis.technical import analyze_ticker_technical
from analysis.stock_scoring import calculate_stock_score, score_all_stocks
from analysis.sentiment import analyze_all_announcements

# Import reports
from report.premarket_template import generate_premarket_report
from report.postmarket_template import generate_postmarket_report

# Import alerts
from alerts.alert_manager import check_and_send_alerts


class ScheduleOrchestrator:
    """Orchestrates all scheduled market analysis tasks"""
    
    def __init__(self):
        self.is_running = False
        self.last_run = {}
    
    # ==================== PRE-MARKET BRIEFING (6:00 AM) ====================
    
    def run_premarket_analysis(self) -> Dict:
        """
        Run pre-market analysis and generate briefing
        Scheduled for 6:00 AM before market opens
        """
        print("\n" + "="*60)
        print("🌅 RUNNING PRE-MARKET ANALYSIS")
        print("="*60)
        
        try:
            # 1. Fetch overnight global markets
            print("\n[1/5] Fetching global markets...")
            global_markets = save_global_markets_data()
            us_markets = get_us_markets_summary()
            asian_markets = get_asian_markets_summary()
            
            # Combine for report
            global_summary = {
                **global_markets,
                'sentiment': us_markets.get('sentiment', 'mixed'),
                'impact': us_markets.get('impact', 'neutral')
            }
            
            # 2. Get previous day KSE-100 data
            print("[2/5] Getting previous day recap...")
            previous_day = db.get_latest_kse100() or {}
            
            # 3. Calculate technical outlook
            print("[3/5] Calculating technical outlook...")
            sr_levels = get_kse100_support_resistance()
            technical_outlook = {
                'support_1': sr_levels.get('support_1', 0),
                'resistance_1': sr_levels.get('resistance_1', 0),
                'expected_low': sr_levels.get('support_1', 0) * 0.995 if sr_levels.get('support_1') else 0,
                'expected_high': sr_levels.get('resistance_1', 0) * 1.005 if sr_levels.get('resistance_1') else 0,
                'trend': 'Awaiting market open'
            }
            
            # 4. Get corporate events (from announcements)
            print("[4/5] Fetching corporate events...")
            announcements = db.get_recent_announcements(days=1)
            corporate_events = [
                {
                    'symbol': ann['symbol'],
                    'event_type': ann.get('announcement_type', 'Announcement'),
                    'impact': 'positive' if (ann.get('sentiment_score', 0) or 0) > 0.1 else (
                        'negative' if (ann.get('sentiment_score', 0) or 0) < -0.1 else 'neutral'
                    )
                }
                for ann in announcements[:10]
            ]
            
            # 5. Identify stocks to watch
            print("[5/5] Identifying stocks to watch...")
            scores = db.get_stock_scores(limit=20)
            stocks_to_watch = [
                {
                    'symbol': s['symbol'],
                    'reason': f"Score {s['total_score']}/100 - {s['rating']}",
                    'action': 'BUY' if s['rating'] in ['STRONG BUY', 'BUY'] else (
                        'SELL' if s['rating'] == 'SELL/AVOID' else 'HOLD'
                    )
                }
                for s in scores[:10]
            ]
            
            # Risk warnings
            risk_warnings = []
            
            if us_markets.get('sentiment') == 'negative':
                risk_warnings.append("US markets closed negative - caution advised")
            
            oil_summary = get_oil_summary()
            if oil_summary.get('trend') == 'falling':
                risk_warnings.append("Oil prices declining - energy sector may be weak")
            
            forex = fetch_usd_pkr()
            if forex and forex.get('usd_pkr', 0) > 280:
                risk_warnings.append("PKR weakness may impact import-heavy stocks")
            
            # Trading strategy
            bias = 'bullish' if us_markets.get('sentiment') == 'positive' else (
                'bearish' if us_markets.get('sentiment') == 'negative' else 'neutral'
            )
            
            trading_strategy = {
                'bias': bias,
                'action': 'Accumulate quality stocks' if bias == 'bullish' else (
                    'Be defensive' if bias == 'bearish' else 'Wait for direction'
                ),
                'buy_level': sr_levels.get('support_1', 0),
                'sell_level': sr_levels.get('resistance_1', 0)
            }
            
            # Generate report
            html = generate_premarket_report(
                global_markets=global_summary,
                previous_day=previous_day,
                technical_outlook=technical_outlook,
                corporate_events=corporate_events,
                stocks_to_watch=stocks_to_watch,
                risk_warnings=risk_warnings,
                trading_strategy=trading_strategy
            )
            
            # Send email
            from report.email_sender import send_email
            send_email(
                subject=f"🌅 PSX Pre-Market Briefing - {datetime.now().strftime('%B %d, %Y')}",
                html_content=html
            )
            
            # Log
            db.save_report_history('pre_market')
            self.last_run['pre_market'] = datetime.now()
            
            print("\n✅ Pre-market analysis complete!")
            
            return {
                'status': 'success',
                'report_type': 'pre_market',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"\n❌ Pre-market analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ==================== MID-DAY UPDATE (1:00 PM) ====================
    
    def run_midday_analysis(self) -> Dict:
        """
        Run mid-day market update
        Quick pulse check during trading hours
        """
        print("\n" + "="*60)
        print("☀️ RUNNING MID-DAY ANALYSIS")
        print("="*60)
        
        try:
            # 1. Fetch current prices
            print("\n[1/4] Fetching current prices...")
            tickers = db.get_all_tickers()
            fetch_all_prices([t['symbol'] for t in tickers[:50]])  # Top 50
            
            # 2. Get KSE-100 status
            print("[2/4] Getting market status...")
            kse100 = get_kse100_summary()
            
            # 3. Quick sector scan
            print("[3/4] Scanning sectors...")
            sector_indices = db.get_sector_indices()
            
            # 4. Check for alerts
            print("[4/4] Checking alert conditions...")
            for ticker in tickers[:30]:
                analysis = analyze_ticker_technical(ticker['symbol'])
                if analysis:
                    check_and_send_alerts({
                        'symbol': ticker['symbol'],
                        'price': analysis['current_price'],
                        'change_percent': 0,  # Would need to calculate
                        'volume': analysis['current_volume'],
                        'volume_ratio': analysis['volume_analysis']['volume_ratio'],
                        'support_resistance': analysis['support_resistance']
                    })
            
            # Generate simple update email
            subject = f"☀️ PSX Mid-Day Update - KSE-100: {kse100.get('close_value', 'N/A'):,.0f} ({kse100.get('change_percent', 0):.2f}%)"
            
            body = f"""
            <h2>Mid-Day Market Pulse</h2>
            <p><strong>KSE-100:</strong> {kse100.get('close_value', 'N/A'):,.0f} ({'+' if (kse100.get('change_percent', 0) or 0) > 0 else ''}{kse100.get('change_percent', 0):.2f}%)</p>
            <p><strong>Market Sentiment:</strong> {kse100.get('sentiment', 'N/A')}</p>
            <p><strong>Volume:</strong> {kse100.get('volume', 0):,} shares</p>
            <p><strong>Breadth:</strong> {kse100.get('advancing', 0)} advancing / {kse100.get('declining', 0)} declining</p>
            <hr>
            <p><em>Full analysis coming after market close.</em></p>
            """
            
            from report.email_sender import send_email
            send_email(
                subject=subject,
                html_content=body
            )
            
            db.save_report_history('mid_day')
            self.last_run['mid_day'] = datetime.now()
            
            print("\n✅ Mid-day analysis complete!")
            
            return {'status': 'success', 'report_type': 'mid_day'}
            
        except Exception as e:
            print(f"\n❌ Mid-day analysis failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ==================== POST-MARKET DEEP ANALYSIS (4:30 PM) ====================
    
    def run_postmarket_analysis(self) -> Dict:
        """
        Run comprehensive post-market analysis
        The main daily deep scan after market close
        """
        print("\n" + "="*60)
        print("🌙 RUNNING POST-MARKET DEEP ANALYSIS")
        print("="*60)
        
        try:
            # 1. Discover and refresh all tickers
            print("\n[1/8] Discovering tickers...")
            discover_and_save_tickers()
            tickers = db.get_all_tickers()
            
            # 2. Fetch final prices
            print("[2/8] Fetching final prices...")
            fetch_all_prices([t['symbol'] for t in tickers])
            
            # 3. Scrape announcements
            print("[3/8] Scraping announcements...")
            symbols = [t['symbol'] for t in tickers[:50]]  # Top 50
            scrape_all_announcements(symbols, show_progress=True)
            analyze_all_announcements()
            
            # 4. Get KSE-100 final data
            print("[4/8] Getting KSE-100 data...")
            kse100 = get_kse100_summary()
            market_summary = {
                'close_value': kse100.get('close_value', 0),
                'change_percent': kse100.get('change_percent', 0),
                'volume': kse100.get('volume', 0),
                'advancing': kse100.get('advancing', 0),
                'declining': kse100.get('declining', 0)
            }
            
            # 5. Score all stocks
            print("[5/8] Running 100-point stock analysis...")
            symbols = [t['symbol'] for t in tickers[:100]]  # Top 100
            scores = score_all_stocks(symbols, show_progress=True)
            
            # Top stocks for report
            top_stocks = [
                {
                    'symbol': s['symbol'],
                    'price': s['components']['technical'].get('details', {}).get('price', 0),
                    'change_percent': 0,  # Would calculate from price history
                    'score': s['total_score'],
                    'rating': s['rating']
                }
                for s in scores[:15]
            ]
            
            # 6. Get sector performance
            print("[6/8] Analyzing sectors...")
            sector_indices = db.get_sector_indices()
            sector_performance = [
                {
                    'name': s['sector'],
                    'change_percent': s.get('change_percent', 0)
                }
                for s in sector_indices
            ]
            
            # 7. Compile technical analysis
            print("[7/8] Compiling technical analysis...")
            sr_levels = get_kse100_support_resistance()
            technical_analysis = {
                'rsi': 55,  # Would calculate from index data
                'macd_trend': 'neutral',
                'trend': kse100.get('sentiment', 'Neutral'),
                'support': sr_levels.get('support_1', 0),
                'resistance': sr_levels.get('resistance_1', 0),
                'bollinger_signal': 'Neutral'
            }
            
            # 8. Get news summary
            print("[8/8] Analyzing news sentiment...")
            news = get_market_news_summary(limit=20)
            news_summary = {
                'total': news.get('total_headlines', 0),
                'positive': news.get('positive_count', 0),
                'negative': news.get('negative_count', 0),
                'sentiment': news.get('overall_sentiment', 'mixed'),
                'top_headlines': [h['headline'] for h in news.get('high_impact_news', [])][:5]
            }
            
            # Risk assessment
            risk_assessment = {
                'market_risk': 'low' if (kse100.get('change_percent', 0) or 0) > 0 else 'medium',
                'currency_risk': 'medium',
                'global_risk': 'low',
                'key_warning': None
            }
            
            # Tomorrow's outlook
            bias = 'bullish' if news.get('overall_sentiment') == 'bullish' and (kse100.get('change_percent', 0) or 0) > 0 else (
                'bearish' if news.get('overall_sentiment') == 'bearish' else 'neutral'
            )
            
            tomorrow_outlook = {
                'bias': bias,
                'range_low': sr_levels.get('support_1', 0),
                'range_high': sr_levels.get('resistance_1', 0),
                'confidence': 60,
                'narrative': f"Market expected to {'continue positive momentum' if bias == 'bullish' else 'face some pressure' if bias == 'bearish' else 'consolidate'}."
            }
            
            # Action items
            action_items = []
            for stock in scores[:3]:
                if stock['rating'] == 'STRONG BUY':
                    action_items.append(f"Consider accumulating {stock['symbol']} (Score: {stock['total_score']}/100)")
            
            if sr_levels.get('support_1'):
                action_items.append(f"Set stop-loss at {sr_levels['support_1']:,.0f} for index positions")
            
            if not action_items:
                action_items = ['Monitor market for direction', 'Maintain existing positions']
            
            # Generate report
            html = generate_postmarket_report(
                market_summary=market_summary,
                top_stocks=top_stocks,
                sector_performance=sector_performance,
                technical_analysis=technical_analysis,
                news_summary=news_summary,
                risk_assessment=risk_assessment,
                tomorrow_outlook=tomorrow_outlook,
                action_items=action_items
            )
            
            # Send email
            from report.email_sender import send_email
            send_email(
                subject=f"📊 PSX Post-Market Analysis - {datetime.now().strftime('%B %d, %Y')} | KSE-100: {market_summary['close_value']:,.0f}",
                html_content=html
            )
            
            db.save_report_history('post_market')
            self.last_run['post_market'] = datetime.now()
            
            print("\n✅ Post-market analysis complete!")
            
            return {'status': 'success', 'report_type': 'post_market'}
            
        except Exception as e:
            print(f"\n❌ Post-market analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'error': str(e)}
    
    # ==================== WEEKLY STRATEGY REPORT (Friday 5:00 PM) ====================
    
    def run_weekly_analysis(self) -> Dict:
        """
        Generate weekly strategy report
        Comprehensive weekly review and outlook
        """
        print("\n" + "="*60)
        print("📅 RUNNING WEEKLY STRATEGY ANALYSIS")
        print("="*60)
        
        # TODO: Implement weekly report
        # This would include:
        # - Week's performance summary
        # - Sector rotation analysis
        # - Top/worst performers
        # - Technical outlook for next week
        # - Strategy recommendations
        
        print("Weekly analysis - Coming soon!")
        
        return {'status': 'pending', 'report_type': 'weekly'}
    
    # ==================== SCHEDULER ====================
    
    def setup_schedule(self):
        """Set up the scheduled tasks"""
        
        # Pre-market briefing
        if SCHEDULES.get('pre_market', {}).get('enabled', True):
            schedule.every().day.at(SCHEDULES['pre_market']['time']).do(
                self.run_premarket_analysis
            )
            print(f"✓ Pre-market briefing scheduled for {SCHEDULES['pre_market']['time']}")
        
        # Mid-day update
        if SCHEDULES.get('mid_day', {}).get('enabled', True):
            schedule.every().day.at(SCHEDULES['mid_day']['time']).do(
                self.run_midday_analysis
            )
            print(f"✓ Mid-day update scheduled for {SCHEDULES['mid_day']['time']}")
        
        # Post-market analysis
        if SCHEDULES.get('post_market', {}).get('enabled', True):
            schedule.every().day.at(SCHEDULES['post_market']['time']).do(
                self.run_postmarket_analysis
            )
            print(f"✓ Post-market analysis scheduled for {SCHEDULES['post_market']['time']}")
        
        # Weekly report (Friday)
        if SCHEDULES.get('weekly', {}).get('enabled', True):
            schedule.every().friday.at(SCHEDULES['weekly']['time']).do(
                self.run_weekly_analysis
            )
            print(f"✓ Weekly report scheduled for Friday {SCHEDULES['weekly']['time']}")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        print("\n" + "="*60)
        print("🚀 PSX RESEARCH ANALYST - SCHEDULER STARTED")
        print("="*60)
        
        self.setup_schedule()
        self.is_running = True
        
        print(f"\nScheduler running. Press Ctrl+C to stop.")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        print("Scheduler stopped.")


# Create singleton instance
orchestrator = ScheduleOrchestrator()


def run_now(report_type: str = 'post_market'):
    """Run a specific report immediately"""
    if report_type == 'pre_market':
        return orchestrator.run_premarket_analysis()
    elif report_type == 'mid_day':
        return orchestrator.run_midday_analysis()
    elif report_type == 'post_market':
        return orchestrator.run_postmarket_analysis()
    elif report_type == 'weekly':
        return orchestrator.run_weekly_analysis()
    else:
        print(f"Unknown report type: {report_type}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='PSX Research Analyst Scheduler')
    parser.add_argument('--run', choices=['pre_market', 'mid_day', 'post_market', 'weekly', 'all'],
                        help='Run a specific report immediately')
    parser.add_argument('--schedule', action='store_true',
                        help='Start the scheduler')
    
    args = parser.parse_args()
    
    if args.run:
        if args.run == 'all':
            run_now('post_market')
        else:
            run_now(args.run)
    elif args.schedule:
        orchestrator.run_scheduler()
    else:
        # Default: run post-market analysis
        run_now('post_market')
