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
        
        Each step is isolated — failures in one step won't crash the report.
        """
        print("\n" + "="*60)
        print("🌅 RUNNING PRE-MARKET ANALYSIS")
        print("="*60)
        import time as _time
        overall_start = _time.time()
        
        try:
            # ── Step 1: Fetch overnight global markets ────────────────
            print("\n[1/5] Fetching global markets (MacroObserver)...")
            macro_packet = {"usd_pkr": 280.0, "oil_brent": 80.0, "kibor_6m": 22.5}
            us_markets = {}
            try:
                macro_packet = macro_observer.get_full_macro_packet()
            except Exception as e:
                print(f"  ⚠️ Macro fetch failed ({e}). Using defaults.")
            
            try:
                us_markets = get_us_markets_summary()
            except Exception as e:
                print(f"  ⚠️ US markets fetch failed ({e}). Using defaults.")
            
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
            
            # ── Step 2: Previous day KSE-100 data ─────────────────────
            print("[2/5] Getting previous day recap...")
            previous_day = {'close_value': 0, 'change_percent': 0, 'volume': 0, 
                           'advancing': 0, 'declining': 0}
            try:
                _prev = db.get_latest_kse100()
                if _prev:
                    previous_day = _prev
            except Exception as e:
                print(f"  ⚠️ KSE-100 data failed ({e}). Using defaults.")
            
            # ── Step 3: Technical outlook ─────────────────────────────
            print("[3/5] Calculating technical outlook...")
            sr_levels = {}
            technical_outlook = {'support_1': 0, 'resistance_1': 0, 'expected_low': 0,
                                'expected_high': 0, 'trend': 'Awaiting market open'}
            try:
                sr_levels = get_kse100_support_resistance()
                technical_outlook = {
                    'support_1': sr_levels.get('support_1', 0),
                    'resistance_1': sr_levels.get('resistance_1', 0),
                    'expected_low': sr_levels.get('support_1', 0) * 0.995 if sr_levels.get('support_1') else 0,
                    'expected_high': sr_levels.get('resistance_1', 0) * 1.005 if sr_levels.get('resistance_1') else 0,
                    'trend': 'Awaiting market open'
                }
            except Exception as e:
                print(f"  ⚠️ Technical outlook failed ({e}). Using defaults.")
            
            # Ensure tickers exist
            try:
                if not db.get_all_tickers():
                    print("  ⚠️ No tickers found in DB. Discovering now...")
                    discover_and_save_tickers()
            except Exception as e:
                print(f"  ⚠️ Ticker check failed ({e}).")

            # ── Step 4: Corporate events ──────────────────────────────
            print("[4/5] Fetching corporate events...")
            corporate_events = []
            try:
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
            except Exception as e:
                print(f"  ⚠️ Corporate events fetch failed ({e}).")
            
            # ── Step 5: Deep Research (lighter — top 10 only) ─────────
            print("[5/5] Identifying High-Conviction Picks (SMI-v3 Ultra)...")
            stocks_to_watch = []
            try:
                step_start = _time.time()
                from ai_engine.deep_research_engine import DeepResearchEngine
                deep_engine = DeepResearchEngine()
                
                # Only analyze top 10 stocks for pre-market (lighter than post-market)
                scores = db.get_stock_scores(limit=10)
                stocks_for_analysis = []
                for s in scores:
                    sym = s['symbol']
                    tech = db.get_technical_indicators(sym) or {}
                    fund = db.get_latest_fundamentals(sym) or {}
                    fund_clean = {k: v for k, v in fund.items() if k != 'date'}
                    news = db.get_recent_news_for_ticker(sym, days=7)
                    
                    context = {
                        "Symbol": sym,
                        "Price": s.get('components', {}).get('technical', {}).get('details', {}).get('price', 0),
                        "Fundamentals": fund_clean,
                        "Technicals": tech,
                        "Sector": fund_clean.get('sector', 'N/A'),
                        "Recent_News": [n.get('headline', '')[:100] for n in (news or [])[:3]]
                    }
                    stocks_for_analysis.append(context)
                
                wealth_picks = deep_engine.find_wealth_generation_picks(stocks_for_analysis)
                
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
                print(f"  ✅ Deep research done in {_time.time()-step_start:.1f}s → {len(stocks_to_watch)} picks")
            except Exception as e:
                print(f"  ⚠️ Deep research failed ({e}). Using cached scores as fallback.")
                try:
                    cached_scores = db.get_stock_scores(limit=5)
                    for s in cached_scores:
                        stocks_to_watch.append({
                            'symbol': s['symbol'],
                            'action': s.get('rating', 'HOLD'),
                            'conviction': f"{s.get('total_score', 50)}%",
                            'reason': f"Score {s.get('total_score', 0)}/100",
                            'future_path': 'N/A', 'black_swan': 'N/A', 'atr_stop': 'N/A'
                        })
                except:
                    pass
            
            # ── Risk warnings ─────────────────────────────────────────
            risk_warnings = []
            try:
                if us_markets.get('sentiment') == 'negative':
                    risk_warnings.append("US markets closed negative - caution advised")
                
                oil_summary = get_oil_summary()
                if oil_summary.get('trend') == 'falling':
                    risk_warnings.append("Oil prices declining - energy sector may be weak")
                
                forex = fetch_usd_pkr()
                if forex and forex.get('usd_pkr', 0) > 280:
                    risk_warnings.append("PKR weakness may impact import-heavy stocks")
            except Exception as e:
                print(f"  ⚠️ Risk warnings generation failed ({e}).")
            
            # ── Trading strategy + AI synthesis ───────────────────────
            bias = 'bullish' if us_markets.get('sentiment') == 'positive' else (
                'bearish' if us_markets.get('sentiment') == 'negative' else 'neutral'
            )
            
            synthesis = None
            try:
                news_data = get_all_news()
                synthesis = _safe_run(market_brain.generate_synthesis(
                    news_data=news_data,
                    market_status=previous_day,
                    macro_data=macro_packet,
                    top_movers={}
                ))
            except Exception as e:
                print(f"  ⚠️ AI synthesis failed ({e}). Report will skip AI section.")
            
            trading_strategy = {
                'bias': bias,
                'action': 'Accumulate quality stocks' if bias == 'bullish' else (
                    'Be defensive' if bias == 'bearish' else 'Wait for direction'
                ),
                'buy_level': sr_levels.get('support_1', 0),
                'sell_level': sr_levels.get('resistance_1', 0),
                'synthesis': synthesis
            }
            
            # ── Generate report ───────────────────────────────────────
            html = generate_premarket_report(
                global_markets=global_summary,
                previous_day=previous_day,
                technical_outlook=technical_outlook,
                corporate_events=corporate_events,
                stocks_to_watch=stocks_to_watch,
                risk_warnings=risk_warnings,
                trading_strategy=trading_strategy
            )
            
            # ── Send email ────────────────────────────────────────────
            try:
                from report.email_sender import send_email
                send_email(
                    subject=f"🌅 PSX Pre-Market Briefing - {datetime.now().strftime('%B %d, %Y')}",
                    html_content=html
                )
            except Exception as e:
                print(f"  ⚠️ Email sending failed ({e}). Saving report locally.")
                try:
                    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                               'reports', f"premarket_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
                    os.makedirs(os.path.dirname(report_path), exist_ok=True)
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"  📄 Report saved to {report_path}")
                except:
                    pass
            
            db.save_report_history('pre_market')
            self.last_run['pre_market'] = datetime.now()
            
            elapsed = _time.time() - overall_start
            print(f"\n✅ Pre-market analysis complete in {elapsed:.0f}s ({elapsed/60:.1f} min)!")
            
            return {
                'status': 'success',
                'report_type': 'pre_market',
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': round(elapsed, 1)
            }
            
        except Exception as e:
            print(f"\n❌ Pre-market analysis failed: {e}")
            import traceback
            traceback.print_exc()
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
        
        Each step is isolated — failures in one step won't crash the report.
        """
        print("\n" + "="*60)
        print("🌙 RUNNING POST-MARKET DEEP ANALYSIS")
        print("="*60)
        import time as _time
        overall_start = _time.time()
        
        try:
            nest_asyncio.apply()
            
            # Use TOP_STOCKS from config (50 tickers) instead of ALL discovered tickers (500+)
            from config import TOP_STOCKS
            
            # ── Step 1: Discover tickers ──────────────────────────────
            print("\n[1/8] Discovering tickers...")
            try:
                discover_and_save_tickers()
                tickers = db.get_all_tickers()
            except Exception as e:
                print(f"  ⚠️ Ticker discovery failed ({e}). Using cached tickers.")
                tickers = db.get_all_tickers() or []
            
            # Use TOP_STOCKS for heavy operations, all tickers only for price fetching
            analysis_symbols = TOP_STOCKS
            all_symbols = [t['symbol'] for t in tickers] if tickers else TOP_STOCKS
            
            # ── Step 2: Fetch final prices ────────────────────────────
            print("[2/8] Fetching final prices...")
            try:
                step_start = _time.time()
                from scraper.price_scraper import AsyncPriceScraper
                scraper = AsyncPriceScraper()
                _safe_run(scraper.fetch_all_prices_async(all_symbols))
                print(f"  ✅ Prices fetched in {_time.time()-step_start:.1f}s")
            except Exception as e:
                print(f"  ⚠️ Price fetching failed ({e}). Using cached prices.")
            
            # ── Step 2.5: Fetch fundamentals ──────────────────────────
            print("[2.5/8] Fetching fundamental data...")
            try:
                step_start = _time.time()
                run_fundamentals_scraper()
                print(f"  ✅ Fundamentals done in {_time.time()-step_start:.1f}s")
            except Exception as e:
                print(f"  ⚠️ Fundamentals fetch failed ({e}). Using cached data.")
            
            # ── Step 2.6: Leverage Audit ──────────────────────────────
            print("[2.6/8] Performing Leverage & Settlement Audit...")
            try:
                leverage_radar.run_leverage_audit()
            except Exception as e:
                print(f"  ⚠️ Leverage audit failed ({e}). Skipping.")

            # ── Step 2.7: Fetch Macro Context (SINGLE call, reused later) ─
            print("[2.7/8] Fetching Global Macro Context...")
            macro_packet = {}
            try:
                macro_packet = macro_observer.get_full_macro_packet()
            except Exception as e:
                print(f"  ⚠️ Macro fetch failed ({e}). Using defaults.")
                macro_packet = {"usd_pkr": 280.0, "oil_brent": 80.0, "kibor_6m": 22.5}
            
            # ── Step 3: Scrape announcements (TOP_STOCKS only) ────────
            print("[3/8] Scraping announcements...")
            try:
                step_start = _time.time()
                scrape_all_announcements(analysis_symbols, show_progress=True)
                analyze_all_announcements()
                print(f"  ✅ Announcements done in {_time.time()-step_start:.1f}s")
            except Exception as e:
                print(f"  ⚠️ Announcements failed ({e}). Using cached data.")
            
            # ── Step 4: Get KSE-100 data + Sovereign Yields ──────────
            print("[4/8] Getting KSE-100 data & Sovereign Context...")
            kse100 = {'close_value': 0, 'change_percent': 0, 'volume': 0, 
                      'advancing': 0, 'declining': 0, 'sentiment': 'Neutral'}
            kibor = {}
            tbills = {}
            try:
                _kse = get_kse100_summary()
                if _kse:
                    kse100 = _kse
            except Exception as e:
                print(f"  ⚠️ KSE-100 fetch failed ({e}). Using defaults.")
            
            try:
                kibor = sovereign_heartbeat.fetch_kibor_rates()
                tbills = sovereign_heartbeat.fetch_tbill_yields()
            except Exception as e:
                print(f"  ⚠️ Sovereign yields failed ({e}). Using defaults.")
            
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
            
            # ── Step 5: Score stocks (TOP_STOCKS only, not all 500+) ──
            print("[5/8] Running 100-point stock analysis...")
            scores = []
            try:
                step_start = _time.time()
                scores = score_all_stocks(analysis_symbols, show_progress=True)
                print(f"  ✅ Scored {len(scores)} stocks in {_time.time()-step_start:.1f}s")
            except Exception as e:
                print(f"  ⚠️ Stock scoring failed ({e}). Report will have limited data.")
            
            # Top stocks for report
            top_stocks = [
                {
                    'symbol': s['symbol'],
                    'price': s['components']['technical'].get('details', {}).get('price', 0),
                    'change_percent': 0,
                    'score': s['total_score'],
                    'rating': s['rating']
                }
                for s in scores[:15]
            ]
            
            # ── Step 5.5: SMI-v3 Ultra Deep Research ──────────────────
            print("[5.5/8] Analyzing Top Tickers for Wealth Generation (SMI-v3 Ultra)...")
            cognitive_decisions = []
            try:
                step_start = _time.time()
                from ai_engine.deep_research_engine import DeepResearchEngine
                deep_engine = DeepResearchEngine()
                
                # Limit to top 15 stocks for faster completion
                stocks_for_post_analysis = []
                for s in top_stocks[:15]:
                    sym = s['symbol']
                    tech = db.get_technical_indicators(sym) or {}
                    lev = db.get_latest_leverage(sym) or {}
                    fund = db.get_latest_fundamentals(sym) or {}
                    fund_clean = {k: v for k, v in fund.items() if k != 'date'}
                    news = db.get_recent_news_for_ticker(sym, days=7)
                    
                    context = {
                        "Symbol": sym,
                        "Price": s['price'],
                        "Change_Percent": s.get('change_percent', 0),
                        "Fundamentals": fund_clean,
                        "Technicals": tech,
                        "Settlement": lev,
                        "Sector": fund_clean.get('sector', 'N/A'),
                        "Macro": macro_packet,
                        "Recent_News": [n.get('headline', '')[:100] for n in (news or [])[:3]]
                    }
                    stocks_for_post_analysis.append(context)
                
                cognitive_decisions = deep_engine.find_wealth_generation_picks(stocks_for_post_analysis)
                print(f"  ✅ Deep research done in {_time.time()-step_start:.1f}s → {len(cognitive_decisions)} verdicts")
                
                # Save decisions to DB
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
            except Exception as e:
                print(f"  ⚠️ Deep research failed ({e}). Report will skip AI verdicts.")
            
            # ── Step 6: Sector performance ────────────────────────────
            print("[6/8] Analyzing sectors...")
            sector_performance = []
            try:
                sector_indices = db.get_sector_indices()
                sector_performance = [
                    {'name': s['sector'], 'change_percent': s.get('change_percent', 0)}
                    for s in sector_indices
                ]
            except Exception as e:
                print(f"  ⚠️ Sector analysis failed ({e}).")
            
            # ── Step 7: Technical analysis ────────────────────────────
            print("[7/8] Compiling technical analysis...")
            sr_levels = {}
            technical_analysis = {'rsi': 55, 'macd_trend': 'neutral', 'trend': 'Neutral',
                                  'support': 0, 'resistance': 0, 'bollinger_signal': 'Neutral'}
            try:
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
            except Exception as e:
                print(f"  ⚠️ Technical analysis failed ({e}). Using defaults.")
            
            # ── Step 8: News + AI Synthesis ───────────────────────────
            print("[8/8] Analyzing news sentiment...")
            news_summary = {'total': 0, 'negative': 0, 'sentiment': 'mixed',
                           'top_headlines': [], 'synthesis': None}
            try:
                step_start = _time.time()
                news_data = get_all_news()
                
                # AI synthesis — reuse macro_packet from Step 2.7 (no duplicate call)
                synthesis = _safe_run(market_brain.generate_synthesis(
                    news_data=news_data,
                    market_status=market_summary,
                    macro_data=macro_packet,
                    top_movers={}
                ))
                
                news_summary = {
                    'total': len(news_data.get('national', [])),
                    'negative': sum(1 for n in news_data.get('national', []) if n['sentiment'] < -0.1),
                    'sentiment': news_data.get('sentiment_label', 'mixed'),
                    'top_headlines': [h['headline'] for h in news_data.get('national', [])][:5],
                    'synthesis': synthesis
                }
                print(f"  ✅ News done in {_time.time()-step_start:.1f}s")
            except Exception as e:
                print(f"  ⚠️ News analysis failed ({e}). Report will have limited news section.")
                news_data = {'national': [], 'overall_sentiment': 'neutral'}
            
            # ── Compile remaining report data ────────────────────────
            risk_assessment = {
                'market_risk': 'low' if (kse100.get('change_percent', 0) or 0) > 0 else 'medium',
                'currency_risk': 'medium',
                'global_risk': 'low',
                'key_warning': None
            }
            
            bias = 'bullish' if news_summary.get('sentiment') == 'bullish' and (kse100.get('change_percent', 0) or 0) > 0 else (
                'bearish' if news_summary.get('sentiment') == 'bearish' else 'neutral'
            )
            
            tomorrow_outlook = {
                'bias': bias,
                'range_low': sr_levels.get('support_1', 0),
                'range_high': sr_levels.get('resistance_1', 0),
                'confidence': 60,
                'narrative': f"Market expected to {'continue positive momentum' if bias == 'bullish' else 'face some pressure' if bias == 'bearish' else 'consolidate'}."
            }
            
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
                
                if val_score >= 15 and fin_score >= 20 and s['total_score'] >= 65:
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

            # ── Generate report HTML ─────────────────────────────────
            print("\n📝 Generating report...")
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
            
            # ── Generate CSV reports ─────────────────────────────────
            print("[8.5/8] Generating comprehensive CSV reports...")
            csv_reports = {}
            attachments = []
            try:
                from report.csv_generator import report_generator
                csv_reports = report_generator.generate_all_reports()
                ai_csv_path = report_generator.generate_ai_decisions_csv(cognitive_decisions)
                csv_reports['ai_cognitive_decisions'] = ai_csv_path
                attachments = list(csv_reports.values())
                print(f"  → Generated {len(attachments)} CSV reports for attachment")
            except Exception as e:
                print(f"  ⚠️ CSV generation failed ({e}). Sending email without attachments.")
            
            # ── Send email ───────────────────────────────────────────
            try:
                from report.email_sender import send_email
                send_email(
                    subject=f"📊 PSX Post-Market Analysis - {datetime.now().strftime('%B %d, %Y')} | KSE-100: {market_summary['close_value']:,.0f}",
                    html_content=html,
                    attachments=attachments
                )
            except Exception as e:
                print(f"  ⚠️ Email sending failed ({e}). Saving report locally.")
                # Save locally as fallback
                try:
                    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                               'reports', f"postmarket_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
                    os.makedirs(os.path.dirname(report_path), exist_ok=True)
                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(html)
                    print(f"  📄 Report saved to {report_path}")
                except:
                    pass
            
            db.save_report_history('post_market')
            self.last_run['post_market'] = datetime.now()
            
            elapsed = _time.time() - overall_start
            print(f"\n✅ Post-market analysis complete in {elapsed:.0f}s ({elapsed/60:.1f} min)!")
            
            return {'status': 'success', 'report_type': 'post_market', 'csv_reports': csv_reports,
                    'elapsed_seconds': round(elapsed, 1)}
            
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
