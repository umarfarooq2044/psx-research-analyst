"""
PSX Research Analyst - Hourly Quick Update Report
==================================================
Generates lightweight hourly updates during market hours
without full price scanning - focuses on news and alerts.

Market Hours: 9:30 AM - 3:30 PM PKT (Mon-Fri)
"""

from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config import FOREX_API_URL, OIL_API_URL

def fetch_global_macro_data() -> Dict:
    """Fetch live Global Macro Data (USD/PKR, Oil)"""
    data = {'usd_pkr': 0, 'oil': 0, 'usd_change': 0, 'oil_change': 0}
    try:
        # 1. USD/PKR (Free API)
        resp = requests.get(FOREX_API_URL, timeout=5)
        if resp.status_code == 200:
            rates = resp.json().get('rates', {})
            usd_pkr = rates.get('PKR', 0)
            data['usd_pkr'] = round(usd_pkr, 2)
            # Calculate change if previous stored.. for now just current value
            
        # 2. Oil (Simple/Free API or scrape)
        # Using a simple requests attempt to an oil price API if valid
        # If API fails, we might leave as 0
        try:
            resp_oil = requests.get(OIL_API_URL, headers={'Authorization': 'Token ...'}, timeout=5)
            # Note: OIL_API_URL in config might need a real free endpoint or token.
            # Fallback to simple scraping/hardcoded if API requires key not present.
            pass 
        except:
            pass
            
    except Exception as e:
        print(f"Macro fetch warning: {e}")
    
    return data

from news.comprehensive_news import get_all_news, get_market_moving_news


def generate_hourly_update_html(
    news_data: Dict,
    market_moving: List[Dict],
    top_movers: Optional[Dict] = None,
    alerts: List[str] = None,
    active_stocks: List[Dict] = None,
    synthesis_data: Dict = None
) -> str:
    """Generate HTML for hourly surveillance email"""
    
    import pytz
    
    if alerts is None: alerts = []
    if active_stocks is None: active_stocks = []
    if top_movers is None: top_movers = {'gainers': [], 'losers': []}
    
    pkt = pytz.timezone('Asia/Karachi')
    current_time = datetime.now(pkt)
    hour = current_time.strftime("%I:%M %p")
    date = current_time.strftime("%B %d, %Y")
    
    # Build SMI-v1 Cognitive Briefing
    smi_briefing_html = ""
    if synthesis_data and synthesis_data.get('strategy'):
        smi_briefing_html = f"""
        <div style="padding: 20px; background: #0d1117; border-left: 4px solid #7856ff; margin: 15px 0;">
            <div style="color: #7856ff; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">🦅 SMI-v1 COGNITIVE BRIEFING</div>
            <div style="color: #e7e9ea; font-size: 15px; font-weight: 600; line-height: 1.4;">
                {synthesis_data.get('strategy')}
            </div>
            <div style="display: flex; gap: 15px; margin-top: 12px; font-size: 13px;">
                <div style="color: #00d26a;">↑ {synthesis_data.get('best_news', 'Bullish Catalysts Stable')}</div>
                <div style="color: #f85149;">↓ {synthesis_data.get('bad_news', 'Risk Factors Monitored')}</div>
            </div>
        </div>
        """

    # Generate Executive Summary Block
    summary_html = ""
    if synthesis_data:
        from analysis.market_synthesis import market_brain
        summary_html = market_brain.get_html_summary(synthesis_data)
    
    # Calculate sentiment color
    sentiment = news_data.get('overall_sentiment', 0)
    sentiment_label = news_data.get('sentiment_label', 'Neutral')
    sentiment_color = '#00d26a' if sentiment > 0.1 else '#ff4757' if sentiment < -0.1 else '#ffa502'
    sentiment_emoji = '📈' if sentiment > 0.1 else '📉' if sentiment < -0.1 else '➡️'
    
    # Build market-moving news section
    market_news_html = ""
    for i, item in enumerate(market_moving[:8]):
        impact_color = '#ff4757' if item.get('market_impact') == 'high' else '#ffa502'
        sent_arrow = '↑' if item['sentiment'] > 0 else '↓' if item['sentiment'] < 0 else '→'
        
        # Show impacted tickers if any
        tickers_html = ""
        if item.get('tickers'):
            tickers_html = f"<div style='margin-top:4px;'><span style='background:#1f6feb; color:white; padding:2px 6px; border-radius:4px; font-size:10px;'>{' '.join(item['tickers'])}</span></div>"
            
        market_news_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #30363d;">
                <span style="color: {impact_color}; font-weight: bold;">{item.get('market_impact', 'medium').upper()}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #30363d;">
                <a href="{item.get('url', '#')}" style="color: #c9d1d9; text-decoration: none; font-weight: 500;">
                    {item['headline']}
                </a>
                {tickers_html}
                <div style="color: #8b949e; font-size: 11px; margin-top: 2px;">{item['source']}</div>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #30363d; text-align: center;">
                <span style="color: {'#00d26a' if item['sentiment'] > 0 else '#ff4757' if item['sentiment'] < 0 else '#8b949e'};">
                    {sent_arrow} {item['sentiment']:.2f}
                </span>
            </td>
        </tr>
        """
    
    # Build national news section
    national_news_html = ""
    for item in news_data.get('national', [])[:6]:
        national_news_html += f"""
        <div style="padding: 10px 0; border-bottom: 1px solid #30363d;">
            <a href="{item.get('url', '#')}" style="color: #c9d1d9; text-decoration: none;">
                {item['headline'][:70]}...
            </a>
            <span style="color: #8b949e; font-size: 11px; margin-left: 8px;">[{item['source']}]</span>
        </div>
        """
    
    # Build international news section
    intl_news_html = ""
    for item in news_data.get('international', [])[:5]:
        intl_news_html += f"""
        <div style="padding: 10px 0; border-bottom: 1px solid #30363d;">
            <a href="{item.get('url', '#')}" style="color: #c9d1d9; text-decoration: none;">
                {item['headline'][:70]}...
            </a>
            <span style="color: #8b949e; font-size: 11px; margin-left: 8px;">[{item['source']}]</span>
        </div>
        """
    
    # Build announcements section
    announcements_html = ""
    for item in news_data.get('announcements', [])[:5]:
        announcements_html += f"""
        <div style="padding: 8px 12px; background: #21262d; border-radius: 6px; margin-bottom: 8px;">
            <strong style="color: #58a6ff;">{item.get('company', 'PSX')}</strong>
            <span style="color: #c9d1d9;"> - {item['headline'][:60]}</span>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PSX Hourly Update - {hour}</title>
    </head>
    <body style="margin: 0; padding: 0; background: #0d1117; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 700px; margin: 0 auto; background: #161b22; border-radius: 12px; overflow: hidden;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #238636 0%, #1f6feb 100%); padding: 25px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">
                    ⏰ PSX HOURLY UPDATE
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">
                    {date} • {hour}
                </p>
            </div>
            
            {summary_html}
            {smi_briefing_html}
            
            <!-- Sentiment Banner -->
            <div style="background: {sentiment_color}; padding: 15px; text-align: center;">
                <span style="color: white; font-size: 20px; font-weight: bold;">
                    {sentiment_emoji} Market Sentiment: {sentiment_label.upper()}
                </span>
                <span style="color: rgba(255,255,255,0.8); margin-left: 10px;">
                    (Score: {sentiment:.2f})
                </span>
            </div>
            
            <!-- Actionable Alerts -->
            <div style="padding: 20px;">
                <h2 style="color: #f0883e; margin: 0 0 15px 0; font-size: 18px; border-bottom: 2px solid #30363d; padding-bottom: 10px;">
                    ⚡ ACTIONABLE RISK ALERTS
                </h2>
                {f'<div style="background: rgba(248,81,73,0.15); border-left: 4px solid #f85149; padding: 15px; border-radius: 4px;">' + 
                 ''.join([f'<div style="margin-bottom: 8px; color: #c9d1d9;">{alert}</div>' for alert in alerts]) + 
                 '</div>' if alerts else '<p style="color: #8b949e;">No critical risk alerts at this moment.</p>'}
            </div>

            <!-- Active Stocks / Volume Spikes -->
            <div style="padding: 0 20px 20px 20px;">
                <h3 style="color: #58a6ff; margin: 0 0 10px 0; font-size: 16px;">
                    📊 Volume Leaders & Spikes
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background: #21262d;">
                        <th style="padding: 8px; text-align: left; color: #8b949e;">Symbol</th>
                        <th style="padding: 8px; text-align: right; color: #8b949e;">Price</th>
                        <th style="padding: 8px; text-align: right; color: #8b949e;">Change</th>
                        <th style="padding: 8px; text-align: right; color: #8b949e;">Volume</th>
                    </tr>
                    {''.join([f'''
                    <tr style="border-bottom: 1px solid #30363d;">
                        <td style="padding: 8px; font-weight: bold; color: #c9d1d9;">{s['symbol']}</td>
                        <td style="padding: 8px; text-align: right; color: #c9d1d9;">{s['price']:.2f}</td>
                        <td style="padding: 8px; text-align: right; color: {'#00d26a' if s['change'] > 0 else '#ff4757'};">{s['change']:+.2f}%</td>
                        <td style="padding: 8px; text-align: right; color: #c9d1d9;">{s['volume']:,}</td>
                    </tr>
                    ''' for s in active_stocks]) if active_stocks else '<tr><td colspan="4" style="padding:10px; text-align:center; color:#8b949e;">No significant volume active</td></tr>'}
                </table>
            </div>

            <!-- Market-Moving News -->
            <div style="padding: 0 20px 20px 20px;">
                <h2 style="color: #ff4757; margin: 0 0 15px 0; font-size: 18px; border-bottom: 2px solid #30363d; padding-bottom: 10px;">
                    🚨 MARKET-MOVING NEWS
                </h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #21262d;">
                        <th style="padding: 10px; text-align: left; color: #8b949e; width: 80px;">Impact</th>
                        <th style="padding: 10px; text-align: left; color: #8b949e;">Headline</th>
                        <th style="padding: 10px; text-align: center; color: #8b949e; width: 80px;">Sentiment</th>
                    </tr>
                    {market_news_html if market_news_html else '<tr><td colspan="3" style="padding: 20px; text-align: center; color: #8b949e;">No major market-moving news at this hour</td></tr>'}
                </table>
            </div>
            
            <!-- Two Column Layout -->
            <div style="padding: 0 20px 20px 20px;">
                <table style="width: 100%;">
                    <tr>
                        <!-- National News -->
                        <td style="width: 50%; vertical-align: top; padding-right: 10px;">
                            <h3 style="color: #58a6ff; margin: 0 0 10px 0; font-size: 15px;">
                                🇵🇰 Pakistan Business
                            </h3>
                            <div style="background: #0d1117; border-radius: 8px; padding: 10px;">
                                {national_news_html if national_news_html else '<p style="color: #8b949e;">No updates</p>'}
                            </div>
                        </td>
                        
                        <!-- International News -->
                        <td style="width: 50%; vertical-align: top; padding-left: 10px;">
                            <h3 style="color: #f0883e; margin: 0 0 10px 0; font-size: 15px;">
                                🌍 Global Markets
                            </h3>
                            <div style="background: #0d1117; border-radius: 8px; padding: 10px;">
                                {intl_news_html if intl_news_html else '<p style="color: #8b949e;">No updates</p>'}
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- PSX Announcements -->
            <div style="padding: 0 20px 20px 20px;">
                <h3 style="color: #a371f7; margin: 0 0 10px 0; font-size: 15px;">
                    📢 PSX Company Announcements
                </h3>
                {announcements_html if announcements_html else '<p style="color: #8b949e; padding: 10px;">No new announcements</p>'}
            </div>
            
            <!-- Footer -->
            <div style="background: #0d1117; padding: 15px; text-align: center; border-top: 1px solid #30363d;">
                <p style="color: #8b949e; margin: 0; font-size: 12px;">
                    📊 PSX Research Analyst | Hourly Intelligence Updates<br>
                    Next update in ~1 hour | Full analysis at market close
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def run_hourly_update() -> Dict:
    """Run hourly surveillance (Full Market Scan) and send email"""
    from report.email_sender import send_email
    from report.csv_generator import generate_hourly_news_csv
    from scraper.price_scraper import fetch_all_prices
    from database.db_manager import db
    from analysis.technical import analyze_ticker_technical
    import asyncio
    
    print("=" * 60)
    print(f"⏰ FULL MARKET SURVEILLANCE - {datetime.now().strftime('%I:%M %p')}")
    print("=" * 60)
    
    # 1. News & Sentiment
    print("\n[1/5] Scanning News Sources (Official + Media)...")
    news_data = get_all_news()
    market_moving = get_market_moving_news()
    
    # 2. Unlimited Market Scan
    print("\n[2/5] Scanning ALL Stocks for Volatility & Volume...")
    tickers = db.get_all_tickers()
    
    # Cloud Fallback: If DB is empty, discover tickers
    if not tickers:
        print("  ⚠️ No tickers found in DB. Discovering now...")
        from scraper.ticker_discovery import discover_and_save_tickers
        discover_and_save_tickers()
        tickers = db.get_all_tickers()
        
    symbols = [t['symbol'] for t in tickers]
    
    # Fetch live prices
    fetch_all_prices(symbols)
    
    # Detect Anomalies
    alerts = []
    volume_spikes = []
    price_movers = []
    
    print(f"  → Analyzing {len(symbols)} tickers...")
    
    for symbol in symbols:
        price_data = db.get_latest_price(symbol)
        if not price_data: continue
        
        # Check Price Volatility
        change = price_data.get('change_percent', 0)
        if abs(change) > 5.0:
            price_movers.append({
                'symbol': symbol,
                'change': change,
                'price': price_data.get('close_price'),
                'volume': price_data.get('volume', 0)
            })
            alerts.append(f"⚠️ {symbol}: High Volatility ({change:+.2f}%)")
            
        # Check Volume Spikes
        # Simple check: Current Vol > 20-Day Avg Vol (if available) * 2.5
        # For lightweight, we can check if volume > 1M and change is small (Accumulation?)
        vol = price_data.get('volume', 0)
        if vol > 1_000_000: # Significant volume
            volume_spikes.append({
                'symbol': symbol,
                'volume': vol,
                'change': change,
                'price': price_data.get('close_price')
            })
            if change > 0:
                alerts.append(f"🟢 {symbol}: High Volume Buying ({vol:,.0f})")
            else:
                alerts.append(f"🔴 {symbol}: High Volume Selling ({vol:,.0f})")

    # 3. Macro Check
    print("\n[3/5] Fetching Global Macro Data...")
    global_data = fetch_global_macro_data()
    if global_data.get('usd_pkr'):
        alerts.append(f"💵 USD/PKR Rate: {global_data['usd_pkr']}") 
    
    # 4. Generate Reports
    print("\n[4/5] Generating Intelligence Reports...")
    csv_path = generate_hourly_news_csv(news_data)
    
    # === MARKET SYNTHESIS & RECOMMENDATION ===
    from analysis.market_synthesis import market_brain
    
    # Prepare data for synthesis
    # Calculate simple breadth from active movers as proxy
    gainers = [m for m in price_movers if m['change'] > 0]
    losers = [m for m in price_movers if m['change'] < 0]
    
    top_movers_dict = {'gainers': gainers, 'losers': losers}
    
    synthesis = market_brain.generate_synthesis(
        news_data=news_data,
        market_status={}, # Future: get from Index trend
        macro_data=global_data,
        top_movers=top_movers_dict
    )
    
    print(f"\n🧠 ANALYST BRAIN SAYS: {synthesis['strategy']}")
    
    # Prepare High Risk / Opportunity List (News + Technical Correlation)
    smart_signals = []
    
    # Create lookup for market moving news by ticker
    news_map = {}
    for item in market_moving:
        for t in item.get('tickers', []):
            if t not in news_map: news_map[t] = []
            news_map[t].append(item)
            
    # Check for correlation
    for spike in volume_spikes:
        sym = spike['symbol']
        if sym in news_map:
            # We have a Match! Volume Spike + News
            news_items = news_map[sym]
            avg_sent = sum(n['sentiment'] for n in news_items) / len(news_items)
            
            if avg_sent > 0.1 and spike['change'] > 0:
                smart_signals.append(f"🚀 **{sym} (Strong Buy)**: Volume Breakout confirmed by Positive News")
            elif avg_sent < -0.1 and spike['change'] < 0:
                smart_signals.append(f"🔻 **{sym} (Strong Sell)**: Panic Selling confirmed by Negative News")
            else:
                smart_signals.append(f"⚠️ **{sym} (Watch)**: High Volume on Mixed News")

    # Add these smart signals to alerts
    if smart_signals:
        alerts = smart_signals + alerts
            
    # 5. Send Email
    print("\n[5/5] Sending Executive Summary...")
    html = generate_hourly_update_html(
        news_data, 
        market_moving, 
        top_movers={'gainers': gainers[:5], 'losers': losers[:5]},
        alerts=alerts[:10],
        active_stocks=volume_spikes[:5],
        synthesis_data=synthesis # Pass synthesis
    )
    
    import pytz
    pkt = pytz.timezone('Asia/Karachi')
    current_time = datetime.now(pkt)
    sentiment_label = news_data.get('sentiment_label', 'Neutral')
    
    subject = f"🚨 HOURLY ALERT: {sentiment_label} | {len(alerts)} Risk Signals | {current_time.strftime('%I:%M %p')}"
    
    try:
        send_email(subject=subject, html_content=html, attachments=[csv_path])
        print(f"\n✅ Surveillance Complete. Alert Sent.")
    except Exception as e:
        print(f"\n❌ Email Error: {e}")
        
    return {
        'alerts': len(alerts),
        'volume_spikes': len(volume_spikes),
        'time': current_time.isoformat()
    }


if __name__ == "__main__":
    result = run_hourly_update()
    print(f"\n📊 Summary: {result['news_count']} news items, {result['market_moving_count']} market-moving")
