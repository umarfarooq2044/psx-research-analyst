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

from news.comprehensive_news import get_all_news, get_market_moving_news


def generate_hourly_update_html(
    news_data: Dict,
    market_moving: List[Dict],
    top_movers: Optional[Dict] = None
) -> str:
    """Generate HTML for hourly quick update email"""
    
    import pytz
    
    pkt = pytz.timezone('Asia/Karachi')
    current_time = datetime.now(pkt)
    hour = current_time.strftime("%I:%M %p")
    date = current_time.strftime("%B %d, %Y")
    
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
        market_news_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #30363d;">
                <span style="color: {impact_color}; font-weight: bold;">{item.get('market_impact', 'medium').upper()}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #30363d;">
                <a href="{item.get('url', '#')}" style="color: #58a6ff; text-decoration: none;">
                    {item['headline'][:80]}...
                </a>
                <br><span style="color: #8b949e; font-size: 12px;">{item['source']}</span>
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
            
            <!-- Sentiment Banner -->
            <div style="background: {sentiment_color}; padding: 15px; text-align: center;">
                <span style="color: white; font-size: 20px; font-weight: bold;">
                    {sentiment_emoji} Market Sentiment: {sentiment_label.upper()}
                </span>
                <span style="color: rgba(255,255,255,0.8); margin-left: 10px;">
                    (Score: {sentiment:.2f})
                </span>
            </div>
            
            <!-- Market-Moving News -->
            <div style="padding: 20px;">
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
    """Run hourly quick update and send email with CSV attachment"""
    from report.email_sender import send_email
    from report.csv_generator import generate_hourly_news_csv
    
    print("=" * 60)
    print(f"⏰ HOURLY QUICK UPDATE - {datetime.now().strftime('%I:%M %p')}")
    print("=" * 60)
    
    # Collect news (lightweight - no price fetching)
    print("\n[1/4] Collecting news from all sources...")
    news_data = get_all_news()
    
    print("\n[2/4] Identifying market-moving news...")
    market_moving = get_market_moving_news()
    
    print("\n[3/4] Generating CSV report...")
    csv_path = generate_hourly_news_csv(news_data)
    print(f"  → Created: {os.path.basename(csv_path)}")
    
    print(f"\n[4/4] Generating hourly report and sending email...")
    html = generate_hourly_update_html(news_data, market_moving)
    
    import pytz
    
    # Send email with CSV attachment
    pkt = pytz.timezone('Asia/Karachi')
    current_time = datetime.now(pkt)
    subject = f"⏰ PSX Hourly Update - {current_time.strftime('%I:%M %p')} | {news_data.get('sentiment_label', 'Neutral')} Sentiment"
    
    try:
        send_email(
            subject=subject, 
            html_content=html,
            attachments=[csv_path]
        )
        print(f"\n✅ Hourly update sent with CSV attachment!")
    except Exception as e:
        print(f"\n❌ Email error: {e}")
    
    return {
        'timestamp': current_time.isoformat(),
        'news_count': len(news_data.get('national', [])) + len(news_data.get('international', [])),
        'market_moving_count': len(market_moving),
        'sentiment': news_data.get('sentiment_label', 'Neutral'),
        'csv_report': csv_path
    }


if __name__ == "__main__":
    result = run_hourly_update()
    print(f"\n📊 Summary: {result['news_count']} news items, {result['market_moving_count']} market-moving")
