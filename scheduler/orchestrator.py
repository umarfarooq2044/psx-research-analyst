"""
PSX Research Analyst - Multi-Schedule Orchestrator
Manages pre-market, mid-day, post-market, and weekly report scheduling
"""
import os
import sys
import schedule
import time
import nest_asyncio
import asyncio
from datetime import datetime, timedelta

# Apply nest_asyncio globally to solve timeout manager issues in nested loops
nest_asyncio.apply()
from typing import Dict, List, Optional, Callable

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def _safe_run(coro):
    """Helper to run async code from sync context safely"""
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Ensure we always run inside a Task context for timeout stability
        if loop.is_running():
            task = loop.create_task(coro)
            return loop.run_until_complete(task)
        else:
            return loop.run_until_complete(coro)
    except Exception as e:
        print(f"  ⚠️ _safe_run fallback: {e}")
        try:
            return asyncio.run(coro)
        except:
            return None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCHEDULES, MARKET_OPEN, MARKET_CLOSE
from database.db_manager import db

# Import scrapers
from scraper.ticker_discovery import discover_and_save_tickers
from scraper.price_scraper import fetch_all_prices
from scraper.announcements_scraper import scrape_all_announcements
from scraper.fundamentals_scraper import run_fundamentals_scraper
from scraper.kse100_scraper import get_kse100_summary, get_kse100_support_resistance

# Import global data
from global_data.forex_scraper import fetch_usd_pkr
from global_data.oil_prices import fetch_oil_prices, get_oil_summary
from global_data.global_indices import get_us_markets_summary, get_asian_markets_summary, save_global_markets_data

# Import news
from news.comprehensive_news import get_all_news, get_market_moving_news

# Import analysis
from analysis.technical import analyze_ticker_technical
from analysis.stock_scoring import calculate_stock_score, score_all_stocks
from analysis.sentiment import analyze_all_announcements
from analysis.market_synthesis import market_brain
from global_data.sovereign_yields import sovereign_heartbeat
from analysis.leverage_radar import leverage_radar
from analysis.macro_observer import macro_observer

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
            # 1. Fetch overnight global markets (SMI-v2 resilient)
            print("\n[1/5] Fetching global markets (MacroObserver)...")
            macro_packet = macro_observer.get_full_macro_packet()
            us_markets = get_us_markets_summary() # Still useful for deep US sentiment
            
            # Combine for report
            global_summary = {
                'sp500': us_markets.get('sp500', 0),
                'sp500_change': us_markets.get('sp500_change', 0),
                'nasdaq': us_markets.get('nasdaq', 0),
                'nasdaq_change': us_markets.get('nasdaq_change', 0),
                'wti_oil': macro_packet.get('oil_brent', 0),
                'usd_pkr': macro_packet.get('usd_pkr', 0),
                'sentiment': us_markets.get('sentiment', 'mixed'),
                'impact': us_markets.get('impact', 'neutral')
            }
            
            # 2. Get previous day KSE-100 data
            print("[2/5] Getting previous day recap...")
            _prev = db.get_latest_kse100()
            previous_day = _prev if _prev else {
                'close_value': 0, 'change_percent': 0, 'volume': 0, 
                'advancing': 0, 'declining': 0
            }
            
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
            
            # 3.5. Ensure tickers exist (Cloud Fallback)
            if not db.get_all_tickers():
                print("  ⚠️ No tickers found in DB. Discovering now...")
                discover_and_save_tickers()

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
            
            # 5. SMI-v3 Ultra: Institutional Deep Research (Pre-Market Picks)
            print("[5/5] Identifying High-Conviction Long-Term Picks (SMI-v3 Ultra)...")
            from ai_engine.deep_research_engine import DeepResearchEngine
            deep_engine = DeepResearchEngine()
            
            # Fetch top scoring stocks for potential deep research
            scores = db.get_stock_scores(limit=25)
            stocks_for_analysis = []
            for s in scores:
                sym = s['symbol']
                tech = db.get_technical_indicators(sym) or {}
                fund = db.get_latest_fundamentals(sym) or {}
                news = db.get_recent_news_for_ticker(sym, days=7)
                
                context = {
                    "Symbol": sym,
                    "Price": s.get('components', {}).get('technical', {}).get('details', {}).get('price', 0),
                    "Fundamentals": fund,
                    "Technicals": tech,
                    "Sector": fund.get('sector', 'N/A'),
                    "Recent_News": [n.get('headline', '')[:100] for n in (news or [])[:3]]
                }
                stocks_for_analysis.append(context)
            
            # Generate Wealth Generation Top 10
            wealth_picks = deep_engine.find_wealth_generation_picks(stocks_for_analysis)
            
            # Map picks to the format expected by the template (or update template to match)
            # For backward compatibility with existing templates until they are updated:
            stocks_to_watch = []
            for p in wealth_picks:
                stocks_to_watch.append({
                    'symbol': p['symbol'],
                    'action': p['action'],
                    'conviction': f"{p['conviction']}%",
                    'future_path': f"Target 1Y: Rs. {p.get('target_price_1y', 'N/A')}",
                    'black_swan': f"Long-Term Pillar: {p.get('key_investment_pillar', 'N/A')}",
                    'reason': p['long_term_rational'],
                    'atr_stop': f"Stop (Long): {p.get('stop_loss_long', 'N/A')}"
                })
            
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
            
            # AI synthesis for pre-market (SMI-v2)
            news_data = get_all_news()
            synthesis = _safe_run(market_brain.generate_synthesis(
                news_data=news_data,
                market_status=previous_day,
                macro_data=macro_packet,
                top_movers={}
            ))
            
            trading_strategy = {
                'bias': bias,
                'action': 'Accumulate quality stocks' if bias == 'bullish' else (
                    'Be defensive' if bias == 'bearish' else 'Wait for direction'
                ),
                'buy_level': sr_levels.get('support_1', 0),
                'sell_level': sr_levels.get('resistance_1', 0),
                'synthesis': synthesis # For template
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
        Run mid-day market update (Delegated to Hourly Update SMI-v2)
        """
        from report.hourly_update import run_hourly_update
        return run_hourly_update()
    
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
            nest_asyncio.apply()
            # 1. Discover and refresh all tickers
            print("\n[1/8] Discovering tickers...")
            discover_and_save_tickers()
            tickers = db.get_all_tickers()
            
            # 2. Fetch final prices
            print("[2/8] Fetching final prices...")
            tickers = db.get_all_tickers()
            from scraper.price_scraper import AsyncPriceScraper
            scraper = AsyncPriceScraper()
            _safe_run(scraper.fetch_all_prices_async([t['symbol'] for t in tickers]))
            
            # 2.5. Fetch fundamentals (P/E, EPS, Margins)
            print("[2.5/8] Fetching fundamental data...")
            run_fundamentals_scraper()
            
            # 2.6. Leverage & Settlement Audit (SMI-v2)
            print("[2.6/8] Performing Leverage & Settlement Audit (NCCPL/PSX)...")
            leverage_radar.run_leverage_audit()

            # 2.5 Fetch Macro Context
            print("[2.5/8] Fetching Global Macro Context...")
            macro_packet = macro_observer.get_full_macro_packet()
            
            # 3. Scrape announcements
            print("[3/8] Scraping announcements...")
            symbols = [t['symbol'] for t in tickers]  # Analyze ALL
            scrape_all_announcements(symbols, show_progress=True)
            analyze_all_announcements()
            
            # 4. Get KSE-100 final data + Sovereign Yields
            print("[4/8] Getting KSE-100 data & Sovereign Context...")
            _kse = get_kse100_summary()
            kse100 = _kse if _kse else {
                'close_value': 0, 'change_percent': 0, 'volume': 0, 
                'advancing': 0, 'declining': 0, 'sentiment': 'Neutral'
            }
            
            # Fetch SMI Sovereign Context
            kibor = sovereign_heartbeat.fetch_kibor_rates()
            tbills = sovereign_heartbeat.fetch_tbill_yields()
            
            market_summary = {
                'close_value': kse100.get('close_value', 0),
                'change_percent': kse100.get('change_percent', 0),
                'volume': kse100.get('volume', 0),
                'advancing': kse100.get('advancing', 0),
                'declining': kse100.get('declining', 0),
                'kibor_6m': kibor.get('6m_kibor'),
                'tbill_3m': tbills.get('3m_yield'),
                'liquidity': 'Positive' if kibor.get('trend') == 'receding' else 'Stable'
            }
            
            # 5. Score all stocks
            print("[5/8] Running 100-point stock analysis...")
            symbols = [t['symbol'] for t in tickers]  # Analyze ALL
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
            
            # 5.5. SMI-v3 Ultra: Institutional Deep Research (Post-Market Verdicts)
            print("[5.5/8] Analyzing Top Tickers for Wealth Generation (SMI-v3 Ultra)...")
            # Reuse the high-speed engine
            from ai_engine.deep_research_engine import DeepResearchEngine
            deep_engine = DeepResearchEngine()
            
            stocks_for_post_analysis = []
            for s in top_stocks[:25]:
                sym = s['symbol']
                tech = db.get_technical_indicators(sym) or {}
                lev = db.get_latest_leverage(sym) or {}
                fund = db.get_latest_fundamentals(sym) or {}
                news = db.get_recent_news_for_ticker(sym, days=7)
                
                context = {
                    "Symbol": sym,
                    "Price": s['price'],
                    "Change_Percent": s.get('change_percent', 0),
                    "Fundamentals": fund,
                    "Technicals": tech,
                    "Settlement": lev,
                    "Sector": fund.get('sector', 'N/A'),
                    "Macro": macro_packet,
                    "Recent_News": [n.get('headline', '')[:100] for n in (news or [])[:3]]
                }
                stocks_for_post_analysis.append(context)
            
            # Generate Top 10 Institutional Picks
            cognitive_decisions = deep_engine.find_wealth_generation_picks(stocks_for_post_analysis)
            
            # Save for record (using original AIDecision table but enriched context)
            db.save_ai_decisions([
                {
                    'ticker': d['symbol'],
                    'action': d['action'],
                    'conviction': f"{d['conviction']}%",
                    'reasoning': d['long_term_rational'],
                    'future_path': f"Target 1Y: {d.get('target_price_1y')}",
                    'black_swan': d.get('key_investment_pillar')
                } for d in cognitive_decisions
            ])
            
            print(f"  → Received {len(cognitive_decisions)} institutional verdicts.")
            
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
            kse100_tech = db.get_technical_indicators('KSE100') or {}
            
            technical_analysis = {
                'rsi': kse100_tech.get('rsi', 55),
                'macd_trend': kse100_tech.get('macd_signal', 'Neutral').lower(),
                'trend': kse100_tech.get('trend', kse100.get('sentiment', 'Neutral')),
                'support': sr_levels.get('support_1', 0),
                'resistance': sr_levels.get('resistance_1', 0),
                'bollinger_signal': kse100_tech.get('bollinger_signal', 'Neutral')
            }
            
            # 8. Get news summary (Comprehensive)
            print("[8/8] Analyzing news sentiment...")
            news_data = get_all_news()
            
            # AI synthesis for post-market
            synthesis = _safe_run(market_brain.generate_synthesis(
                news_data=news_data,
                market_status=market_summary, # Changed from kse100_summary to market_summary to match original context
                macro_data=macro_observer.get_full_macro_packet(), # Changed from macro_packet to macro_observer.get_full_macro_packet() to match original context
                top_movers={} # Changed from {'gainers': top_gainers, 'losers': top_losers} to {} to match original context
            ))
            
            news_summary = {
                'total': len(news_data.get('national', [])),
                'negative': sum(1 for n in news_data.get('national', []) if n['sentiment'] < -0.1),
                'sentiment': news_data.get('sentiment_label', 'mixed'),
                'top_headlines': [h['headline'] for h in news_data.get('national', [])][:5],
                'synthesis': synthesis # Pass to template
            }
            
            # Risk assessment
            risk_assessment = {
                'market_risk': 'low' if (kse100.get('change_percent', 0) or 0) > 0 else 'medium',
                'currency_risk': 'medium',
                'global_risk': 'low',
                'key_warning': None
            }
            
            # Tomorrow's outlook
            bias = 'bullish' if news_data.get('overall_sentiment') == 'bullish' and (kse100.get('change_percent', 0) or 0) > 0 else (
                'bearish' if news_data.get('overall_sentiment') == 'bearish' else 'neutral'
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
            
            # Identify Undervalued Gems
            undervalued_gems = []
            for s in scores:
                comp = s.get('components', {})
                val_score = comp.get('valuation', {}).get('score', 0)
                fin_score = comp.get('financial', {}).get('score', 0)
                
                # Logic: Good Valuation (>15/25) + Good Financials (>20/35) + Total > 65
                if val_score >= 15 and fin_score >= 20 and s['total_score'] >= 65:
                    # Extract details for display
                    try:
                        pe_str = comp['valuation']['details'].get('pe_valuation', 'N/A').split('P/E: ')[-1].replace(')', '')
                        growth_str = comp['financial']['details'].get('earnings_quality', 'N/A').split('growth: ')[-1].replace('%)', '')
                    except:
                        pe_str = "N/A"
                        growth_str = "N/A"
                        
                    undervalued_gems.append({
                        'symbol': s['symbol'],
                        'score': s['total_score'],
                        'pe_ratio': pe_str,
                        'growth': growth_str,
                        'reason': 'Undervalued High Growth'
                    })

            # Generate report
            html = generate_postmarket_report(
                market_summary=market_summary,
                top_stocks=top_stocks,
                sector_performance=sector_performance,
                technical_analysis=technical_analysis,
                news_summary=news_summary,
                risk_assessment=risk_assessment,
                tomorrow_outlook=tomorrow_outlook,
                action_items=action_items,
                undervalued_gems=undervalued_gems[:4],
                cognitive_decisions=cognitive_decisions
            )
            
            # Generate comprehensive CSV reports
            print("[8.5/8] Generating comprehensive CSV reports...")
            from report.csv_generator import report_generator
            csv_reports = report_generator.generate_all_reports()
            
            # Ensure the specific AI CSV includes today's real-time decisions
            ai_csv_path = report_generator.generate_ai_decisions_csv(cognitive_decisions)
            csv_reports['ai_cognitive_decisions'] = ai_csv_path
            
            attachments = list(csv_reports.values())
            print(f"  → Generated {len(attachments)} CSV reports for attachment")
            
            # Send email with attachments
            from report.email_sender import send_email
            send_email(
                subject=f"📊 PSX Post-Market Analysis - {datetime.now().strftime('%B %d, %Y')} | KSE-100: {market_summary['close_value']:,.0f}",
                html_content=html,
                attachments=attachments
            )
            
            db.save_report_history('post_market')
            self.last_run['post_market'] = datetime.now()
            
            print("\n✅ Post-market analysis complete with CSV attachments!")
            
            return {'status': 'success', 'report_type': 'post_market', 'csv_reports': csv_reports}
            
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
    elif report_type == 'hourly':
        from report.hourly_update import run_hourly_update
        return run_hourly_update()
    else:
        print(f"Unknown report type: {report_type}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='PSX Research Analyst Scheduler')
    parser.add_argument('--run', choices=['pre_market', 'mid_day', 'post_market', 'weekly', 'hourly', 'all'],
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
