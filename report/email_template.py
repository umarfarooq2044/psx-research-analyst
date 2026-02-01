"""
PSX Research Analyst - HTML Email Template
Generates professional styled HTML email reports
"""
from typing import List, Dict
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WATCHLIST


def get_css_styles() -> str:
    """
    Return CSS styles for the email template
    """
    return """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }
        .header .date {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 14px;
        }
        .section {
            padding: 25px 30px;
            border-bottom: 1px solid #eee;
        }
        .section:last-child {
            border-bottom: none;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #1a237e;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title .icon {
            font-size: 24px;
        }
        .stock-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-left: 4px solid #1a237e;
        }
        .stock-card.strong-buy {
            border-left-color: #00C851;
            background: linear-gradient(90deg, rgba(0,200,81,0.1) 0%, #f8f9fa 100%);
        }
        .stock-card.buy {
            border-left-color: #33b5e5;
        }
        .stock-card.hold {
            border-left-color: #ffbb33;
        }
        .stock-card.sell {
            border-left-color: #ff4444;
            background: linear-gradient(90deg, rgba(255,68,68,0.1) 0%, #f8f9fa 100%);
        }
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .stock-symbol {
            font-size: 18px;
            font-weight: 700;
            color: #333;
        }
        .stock-name {
            font-size: 13px;
            color: #666;
            margin-left: 10px;
            font-weight: normal;
        }
        .score-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            color: white;
        }
        .score-strong-buy { background-color: #00C851; }
        .score-buy { background-color: #33b5e5; }
        .score-hold { background-color: #ffbb33; color: #333; }
        .score-sell { background-color: #ff4444; }
        .stock-metrics {
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .metric {
            font-size: 13px;
        }
        .metric-label {
            color: #666;
        }
        .metric-value {
            font-weight: 600;
            color: #333;
        }
        .stock-notes {
            font-size: 13px;
            color: #555;
            font-style: italic;
            margin-top: 10px;
            line-height: 1.5;
        }
        .red-alert {
            background: #fff3f3;
        }
        .alert-icon {
            color: #ff4444;
            font-weight: bold;
        }
        .watchlist-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .watchlist-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .watchlist-symbol {
            font-size: 16px;
            font-weight: 700;
            color: #1a237e;
        }
        .watchlist-score {
            font-size: 24px;
            font-weight: 700;
            margin: 10px 0;
        }
        .watchlist-rec {
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 10px;
            display: inline-block;
        }
        .footer {
            background: #f1f1f1;
            padding: 20px 30px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
        .footer a {
            color: #1a237e;
            text-decoration: none;
        }
        .summary-box {
            background: linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .summary-stat {
            display: inline-block;
            margin: 0 20px;
        }
        .summary-value {
            font-size: 28px;
            font-weight: 700;
            color: #1a237e;
        }
        .summary-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
    </style>
    """


def generate_stock_card(stock: Dict, card_type: str = "normal") -> str:
    """
    Generate HTML for a single stock card
    """
    symbol = stock.get('symbol', 'N/A')
    name = stock.get('name', stock.get('company_name', symbol))
    buy_score = stock.get('buy_score', 0)
    recommendation = stock.get('recommendation', 'HOLD')
    notes = stock.get('notes', '')
    
    # Get technical data
    technical = stock.get('technical', {})
    rsi = technical.get('rsi', stock.get('rsi'))
    volume_ratio = technical.get('volume_ratio', 1.0)
    current_price = technical.get('current_price', 0)
    
    # Get sentiment data
    sentiment = stock.get('sentiment', {})
    sent_score = sentiment.get('sentiment_score', stock.get('sentiment_score', 0))
    
    # Determine card class
    if recommendation == "STRONG BUY":
        card_class = "strong-buy"
        score_class = "score-strong-buy"
    elif recommendation == "BUY":
        card_class = "buy"
        score_class = "score-buy"
    elif recommendation == "HOLD":
        card_class = "hold"
        score_class = "score-hold"
    else:
        card_class = "sell"
        score_class = "score-sell"
    
    if card_type == "alert":
        card_class += " red-alert"
    
    # Format metrics
    price_str = f"Rs. {current_price:,.2f}" if current_price else "N/A"
    rsi_str = f"{rsi:.1f}" if rsi else "N/A"
    sent_str = f"{sent_score:+.2f}" if sent_score else "0.00"
    vol_str = f"{volume_ratio:.1f}x" if volume_ratio else "1.0x"
    
    # SMI-v1 Recursive Fields
    future_path = stock.get('future_path', 'N/A')
    black_swan = stock.get('black_swan', 'N/A')
    conviction = stock.get('conviction', '50%')
    
    return f"""
    <div class="stock-card {card_class}">
        <div class="stock-header">
            <div>
                <span class="stock-symbol">{symbol}</span>
                <span class="stock-name">{name}</span>
            </div>
            <span class="score-badge {score_class}">{buy_score}/10 {recommendation}</span>
        </div>
        
        <!-- SMI-v1 Recursive Intelligence Layer -->
        <div style="margin-bottom: 12px; display: flex; gap: 10px;">
            <div style="flex: 1; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 6px 10px; border-radius: 4px; font-size: 11px;">
                <div style="color: #2e7d32; font-weight: 700; text-transform: uppercase; font-size: 9px;">🦅 T+7 Tunnel</div>
                <div style="font-weight: 600; color: #1b5e20;">{future_path}</div>
            </div>
            <div style="flex: 1; background: #fff3e0; border: 1px solid #ffe0b2; padding: 6px 10px; border-radius: 4px; font-size: 11px;">
                <div style="color: #e65100; font-weight: 700; text-transform: uppercase; font-size: 9px;">⚡ Black Swan</div>
                <div style="font-weight: 600; color: #bf360c;">{black_swan}</div>
            </div>
        </div>

        <div class="stock-metrics">
            <div class="metric">
                <span class="metric-label">Price:</span>
                <span class="metric-value">{price_str}</span>
            </div>
            <div class="metric">
                <span class="metric-label">RSI:</span>
                <span class="metric-value">{rsi_str}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Conviction:</span>
                <span class="metric-value" style="color: #1a237e;">{conviction}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Sentiment:</span>
                <span class="metric-value">{sent_str}</span>
            </div>
        </div>
        <div class="stock-notes" style="background: #ffffff; padding: 8px; border-radius: 4px; border: 1px solid #eee;">
            <strong>AI Logic:</strong> {notes}
        </div>
    </div>
    """


def generate_watchlist_item(stock: Dict) -> str:
    """
    Generate HTML for a watchlist item
    """
    symbol = stock.get('symbol', 'N/A')
    buy_score = stock.get('buy_score', 0)
    recommendation = stock.get('recommendation', 'HOLD')
    
    # Determine colors
    if recommendation == "STRONG BUY":
        color = "#00C851"
    elif recommendation == "BUY":
        color = "#33b5e5"
    elif recommendation == "HOLD":
        color = "#ffbb33"
    else:
        color = "#ff4444"
    
    return f"""
    <div class="watchlist-item">
        <div class="watchlist-symbol">{symbol}</div>
        <div class="watchlist-score" style="color: {color}">{buy_score}</div>
        <span class="watchlist-rec" style="background-color: {color}; color: white;">{recommendation}</span>
    </div>
    """


def generate_html_report(
    top_opportunities: List[Dict],
    red_alerts: List[Dict],
    watchlist_status: List[Dict],
    market_summary: Dict = None
) -> str:
    """
    Generate complete HTML email report
    """
    now = datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p PKT")
    
    # Market summary stats
    total_analyzed = market_summary.get('total_analyzed', 0) if market_summary else 0
    strong_buys = market_summary.get('strong_buys', 0) if market_summary else len([s for s in top_opportunities if s.get('recommendation') == 'STRONG BUY'])
    alerts_count = len(red_alerts)
    
    # Generate sections
    opportunities_html = ""
    for stock in top_opportunities[:5]:
        opportunities_html += generate_stock_card(stock, "opportunity")
    
    alerts_html = ""
    if red_alerts:
        for stock in red_alerts[:5]:
            alerts_html += generate_stock_card(stock, "alert")
    else:
        alerts_html = '<p style="color: #666; text-align: center;">No red alerts today. Market looking healthy! ✓</p>'
    
    watchlist_html = ""
    for stock in watchlist_status:
        watchlist_html += generate_watchlist_item(stock)
    
    # Complete HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PSX Daily Research Report</title>
        {get_css_styles()}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 PSX Daily Research Report</h1>
                <div class="date">{date_str} | Generated at {time_str}</div>
            </div>
            
            <div class="section">
                <div class="summary-box">
                    <div class="summary-stat">
                        <div class="summary-value">{total_analyzed}</div>
                        <div class="summary-label">Stocks Analyzed</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-value" style="color: #00C851;">{strong_buys}</div>
                        <div class="summary-label">Strong Buys</div>
                    </div>
                    <div class="summary-stat">
                        <div class="summary-value" style="color: #ff4444;">{alerts_count}</div>
                        <div class="summary-label">Red Alerts</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">
                    <span class="icon">🚀</span>
                    Top 5 Market Opportunities
                </div>
                {opportunities_html}
            </div>
            
            <div class="section">
                <div class="section-title">
                    <span class="icon">🚨</span>
                    Red Alert Section
                </div>
                {alerts_html}
            </div>
            
            <div class="section">
                <div class="section-title">
                    <span class="icon">👁️</span>
                    Watchlist Update
                </div>
                <div class="watchlist-grid">
                    {watchlist_html}
                </div>
            </div>
            
            <div class="footer">
                <p><strong>PSX Autonomous Research Analyst</strong></p>
                <p>This report is generated automatically using technical and sentiment analysis.</p>
                <p>Not financial advice. Always do your own research before investing.</p>
                <p style="margin-top: 15px;">
                    Powered by AI | Data from <a href="https://dps.psx.com.pk">PSX</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def save_report_to_file(html: str, filename: str = None) -> str:
    """
    Save HTML report to file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"psx_report_{timestamp}.html"
    
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Report saved to: {filepath}")
    return filepath


if __name__ == "__main__":
    # Test with sample data
    sample_opportunities = [
        {
            'symbol': 'MARI',
            'name': 'Mari Energies Limited',
            'buy_score': 9,
            'recommendation': 'STRONG BUY',
            'notes': 'Deeply oversold (RSI 28). Volume spike detected (3.2x average). Positive news flow.',
            'technical': {'rsi': 28, 'volume_ratio': 3.2, 'current_price': 735.50},
            'sentiment': {'sentiment_score': 0.65}
        },
        {
            'symbol': 'OGDC',
            'name': 'Oil & Gas Development Company',
            'buy_score': 8,
            'recommendation': 'STRONG BUY',
            'notes': 'Oversold territory. Near 52-week support level.',
            'technical': {'rsi': 38, 'volume_ratio': 1.8, 'current_price': 125.30},
            'sentiment': {'sentiment_score': 0.42}
        }
    ]
    
    sample_alerts = [
        {
            'symbol': 'XYZ',
            'name': 'XYZ Company Limited',
            'buy_score': 2,
            'recommendation': 'SELL/AVOID',
            'notes': 'Price broke below 52-week support. Negative news sentiment.',
            'technical': {'rsi': 75, 'volume_ratio': 0.7, 'current_price': 45.20},
            'sentiment': {'sentiment_score': -0.45}
        }
    ]
    
    sample_watchlist = [
        {'symbol': 'SAZEW', 'buy_score': 7, 'recommendation': 'BUY'},
        {'symbol': 'GLAXO', 'buy_score': 6, 'recommendation': 'BUY'},
        {'symbol': 'AIRLINK', 'buy_score': 5, 'recommendation': 'HOLD'},
        {'symbol': 'FFC', 'buy_score': 8, 'recommendation': 'STRONG BUY'},
        {'symbol': 'MARI', 'buy_score': 9, 'recommendation': 'STRONG BUY'}
    ]
    
    html = generate_html_report(
        sample_opportunities,
        sample_alerts,
        sample_watchlist,
        {'total_analyzed': 523, 'strong_buys': 12}
    )
    
    filepath = save_report_to_file(html)
    print(f"\nTest report generated: {filepath}")
