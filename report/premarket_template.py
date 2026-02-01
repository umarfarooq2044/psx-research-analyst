"""
PSX Research Analyst - Pre-Market Report Template
Generates comprehensive pre-market briefing email (6:00 AM)
"""
from typing import Dict, List, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_premarket_css() -> str:
    """CSS styles for pre-market email"""
    return """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f1419; color: #e7e9ea; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #1d9bf0, #7856ff); padding: 25px; border-radius: 12px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: white; font-size: 24px; }
        .header .subtitle { color: rgba(255,255,255,0.9); font-size: 14px; margin-top: 8px; }
        .section { background: #1e2732; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #38444d; }
        .section-title { color: #1d9bf0; font-size: 16px; font-weight: 600; margin-bottom: 15px; border-bottom: 1px solid #38444d; padding-bottom: 10px; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .metric { background: #15202b; padding: 12px; border-radius: 8px; }
        .metric-label { color: #8899a6; font-size: 12px; }
        .metric-value { color: #e7e9ea; font-size: 18px; font-weight: 600; margin-top: 4px; }
        .positive { color: #00ba7c; }
        .negative { color: #f91880; }
        .neutral { color: #8899a6; }
        .stock-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #38444d; }
        .stock-symbol { font-weight: 600; color: #1d9bf0; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-buy { background: rgba(0,186,124,0.2); color: #00ba7c; }
        .badge-sell { background: rgba(249,24,128,0.2); color: #f91880; }
        .badge-hold { background: rgba(136,153,166,0.2); color: #8899a6; }
        .alert-box { background: rgba(249,24,128,0.1); border: 1px solid #f91880; border-radius: 8px; padding: 12px; margin-top: 15px; }
        .strategy-box { background: rgba(0,186,124,0.1); border: 1px solid #00ba7c; border-radius: 8px; padding: 15px; }
        ul { padding-left: 20px; margin: 10px 0; }
        li { margin: 8px 0; color: #e7e9ea; }
        .footer { text-align: center; color: #8899a6; font-size: 12px; margin-top: 20px; }
    </style>
    """


def generate_premarket_report(
    global_markets: Dict,
    previous_day: Dict,
    technical_outlook: Dict,
    corporate_events: List[Dict],
    stocks_to_watch: List[Dict],
    risk_warnings: List[str],
    trading_strategy: Dict
) -> str:
    """
    Generate pre-market briefing HTML email
    
    Args:
        global_markets: Overnight global market data
        previous_day: Previous day PSX summary
        technical_outlook: KSE-100 technical analysis
        corporate_events: Today's corporate announcements/earnings
        stocks_to_watch: Stocks to monitor today
        risk_warnings: Current risk factors
        trading_strategy: Recommended strategy for the day
    """
    
    now = datetime.now()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {get_premarket_css()}
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>🌅 PSX PRE-MARKET BRIEFING</h1>
                <div class="subtitle">{now.strftime('%A, %B %d, %Y')} | Generated at {now.strftime('%I:%M %p')} PKT</div>
            </div>
            
            <!-- Global Markets Overnight -->
            <div class="section">
                <div class="section-title">🌍 OVERNIGHT GLOBAL MARKETS</div>
                <div class="grid">
                    <div class="metric">
                        <div class="metric-label">S&P 500</div>
                        <div class="metric-value {'positive' if (global_markets.get('sp500_change', 0) or 0) > 0 else 'negative'}">
                            {global_markets.get('sp500', 'N/A')} 
                            ({'+' if (global_markets.get('sp500_change', 0) or 0) > 0 else ''}{global_markets.get('sp500_change', 0) or 0:.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">NASDAQ</div>
                        <div class="metric-value {'positive' if (global_markets.get('nasdaq_change', 0) or 0) > 0 else 'negative'}">
                            {global_markets.get('nasdaq', 'N/A')}
                            ({'+' if (global_markets.get('nasdaq_change', 0) or 0) > 0 else ''}{global_markets.get('nasdaq_change', 0) or 0:.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">WTI Crude Oil</div>
                        <div class="metric-value {'positive' if (global_markets.get('wti_change', 0) or 0) > 0 else 'negative'}">
                            ${global_markets.get('wti_oil', 'N/A')}
                            ({'+' if (global_markets.get('wti_change', 0) or 0) > 0 else ''}{global_markets.get('wti_change', 0) or 0:.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">USD/PKR</div>
                        <div class="metric-value">
                            Rs. {global_markets.get('usd_pkr', 'N/A')}
                        </div>
                    </div>
                </div>
                <div class="metric" style="margin-top: 12px;">
                    <div class="metric-label">Global Sentiment</div>
                    <div class="metric-value">{global_markets.get('sentiment', 'Mixed')}: {global_markets.get('impact', 'Neutral for PSX')}</div>
                </div>
            </div>
            
            <!-- Previous Day Recap -->
            <div class="section">
                <div class="section-title">📊 PREVIOUS DAY RECAP</div>
                <div class="grid">
                    <div class="metric">
                        <div class="metric-label">KSE-100 Close</div>
                        <div class="metric-value {'positive' if (previous_day.get('change_percent', 0) or 0) > 0 else 'negative'}">
                            {previous_day.get('close_value', 'N/A'):,.0f}
                            ({'+' if (previous_day.get('change_percent', 0) or 0) > 0 else ''}{previous_day.get('change_percent', 0) or 0:.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Volume</div>
                        <div class="metric-value">{previous_day.get('volume', 0):,} shares</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Advancing</div>
                        <div class="metric-value positive">{previous_day.get('advancing', 'N/A')}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Declining</div>
                        <div class="metric-value negative">{previous_day.get('declining', 'N/A')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Technical Outlook -->
            <div class="section">
                <div class="section-title">📈 TECHNICAL OUTLOOK - KSE-100</div>
                <div class="grid">
                    <div class="metric">
                        <div class="metric-label">Support Level 1</div>
                        <div class="metric-value">{technical_outlook.get('support_1', 'N/A'):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Resistance Level 1</div>
                        <div class="metric-value">{technical_outlook.get('resistance_1', 'N/A'):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Expected Range</div>
                        <div class="metric-value">{technical_outlook.get('expected_low', 'N/A'):,.0f} - {technical_outlook.get('expected_high', 'N/A'):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Trend</div>
                        <div class="metric-value">{technical_outlook.get('trend', 'Consolidating')}</div>
                    </div>
                </div>
            </div>
            
            <!-- Corporate Events -->
            <div class="section">
                <div class="section-title">📢 CORPORATE EVENTS TODAY</div>
                {''.join([f'''
                <div class="stock-row">
                    <div>
                        <span class="stock-symbol">{event['symbol']}</span> - {event['event_type']}
                    </div>
                    <div class="{'positive' if event.get('impact') == 'positive' else 'negative' if event.get('impact') == 'negative' else 'neutral'}">
                        {event.get('impact', 'neutral').title()}
                    </div>
                </div>
                ''' for event in corporate_events[:5]]) if corporate_events else '<p style="color: #8899a6;">No major corporate events scheduled today.</p>'}
            </div>
            
            <!-- SMI-v1 Recursive Intelligence -->
            <div class="section">
                <div class="section-title">🦅 SMI-v1 RECURSIVE SIGNALS (T+7 PROBABILITY TUNNELS)</div>
                {''.join([f'''
                <div class="stock-row" style="flex-direction: column; align-items: flex-start; gap: 8px;">
                    <div style="display: flex; justify-content: space-between; width: 100%;">
                        <span class="stock-symbol" style="font-size: 18px;">{stock['symbol']}</span>
                        <span class="badge badge-{stock.get('action', 'hold').lower()}">{stock.get('conviction', '50%')} CONVICTION</span>
                    </div>
                    <div style="display: flex; gap: 10px; width: 100%;">
                        <div style="flex: 1; background: #15202b; padding: 10px; border-radius: 6px; border-left: 3px solid #1d9bf0;">
                            <div style="font-size: 10px; color: #8899a6; text-transform: uppercase;">Signal</div>
                            <div style="font-size: 14px; font-weight: 600; color: {'#00ba7c' if stock.get('action') == 'BUY' else '#f91880' if stock.get('action') == 'SELL' else '#e7e9ea'}">
                                {stock.get('action', 'WAIT')}
                            </div>
                        </div>
                        <div style="flex: 2; background: #15202b; padding: 10px; border-radius: 6px; border-left: 3px solid #7856ff;">
                            <div style="font-size: 10px; color: #8899a6; text-transform: uppercase;">Probability Tunnel (T+7)</div>
                            <div style="font-size: 13px; font-weight: 600;">{stock.get('future_path', 'Stochastic Range: N/A')}</div>
                        </div>
                    </div>
                    <div style="width: 100%; background: rgba(249,24,128,0.05); padding: 8px; border-radius: 4px; border: 1px dashed rgba(249,24,128,0.3); font-size: 11px;">
                        <span style="color: #f91880; font-weight: 700;">BLACK SWAN:</span> {stock.get('black_swan', 'Unknown catalyst breakpoint')}
                    </div>
                    <div style="color: #8899a6; font-size: 12px; margin-top: 4px;">
                        <strong>Logic:</strong> {stock.get('reason', 'Consensus-driven reasoning')}
                    </div>
                    <div style="height: 10px; width: 100%; border-bottom: 1px solid #38444d;"></div>
                </div>
                ''' for stock in stocks_to_watch[:8]])}
            </div>
            
            <!-- Risk Warnings -->
            {f'''
            <div class="section">
                <div class="section-title">⚠️ RISK WARNINGS</div>
                <div class="alert-box">
                    <ul>
                        {''.join([f"<li>{risk}</li>" for risk in risk_warnings])}
                    </ul>
                </div>
            </div>
            ''' if risk_warnings else ''}
            
            <!-- Trading Strategy -->
            <div class="section">
                <div class="section-title">🎯 TODAY'S TRADING STRATEGY</div>
                <div class="strategy-box">
                    <div style="margin-bottom: 10px;">
                        <strong>Market Bias:</strong> 
                        <span class="{'positive' if trading_strategy.get('bias') == 'bullish' else 'negative' if trading_strategy.get('bias') == 'bearish' else 'neutral'}">
                            {trading_strategy.get('bias', 'Neutral').upper()}
                        </span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Recommended Action:</strong> {trading_strategy.get('action', 'Hold current positions')}
                    </div>
                    <div>
                        <strong>Key Levels:</strong> Buy below {trading_strategy.get('buy_level', 'N/A')}, 
                        Sell above {trading_strategy.get('sell_level', 'N/A')}
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p>PSX Autonomous Research Analyst | Pre-Market Report</p>
                <p>Generated automatically. Not financial advice. Do your own research.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_sample_premarket_report() -> str:
    """Generate a sample pre-market report for testing"""
    
    global_markets = {
        'sp500': 5234.18,
        'sp500_change': 0.85,
        'nasdaq': 16428.82,
        'nasdaq_change': 1.12,
        'wti_oil': 78.45,
        'wti_change': -0.32,
        'usd_pkr': 278.50,
        'sentiment': 'Positive',
        'impact': 'Bullish for emerging markets'
    }
    
    previous_day = {
        'close_value': 98245,
        'change_percent': 0.45,
        'volume': 245678900,
        'advancing': 234,
        'declining': 156
    }
    
    technical_outlook = {
        'support_1': 97500,
        'resistance_1': 99000,
        'expected_low': 97800,
        'expected_high': 98800,
        'trend': 'Mildly Bullish'
    }
    
    corporate_events = [
        {'symbol': 'OGDC', 'event_type': 'Earnings Release', 'impact': 'positive'},
        {'symbol': 'HBL', 'event_type': 'Board Meeting', 'impact': 'neutral'},
        {'symbol': 'FFC', 'event_type': 'Dividend Announcement', 'impact': 'positive'}
    ]
    
    stocks_to_watch = [
        {'symbol': 'OGDC', 'reason': 'Earnings catalyst, oil prices up', 'action': 'BUY'},
        {'symbol': 'MARI', 'reason': 'Technical breakout candidate', 'action': 'BUY'},
        {'symbol': 'HBL', 'reason': 'Near 52-week high', 'action': 'HOLD'},
        {'symbol': 'PSO', 'reason': 'Volume surge yesterday', 'action': 'WATCH'},
        {'symbol': 'PPL', 'reason': 'RSI oversold, potential reversal', 'action': 'BUY'}
    ]
    
    risk_warnings = [
        'Global volatility elevated (VIX at 18)',
        'USD/PKR showing weakness, monitor closely',
        'Oil price volatility may impact energy sector'
    ]
    
    trading_strategy = {
        'bias': 'bullish',
        'action': 'Accumulate quality stocks on any dip',
        'buy_level': 97800,
        'sell_level': 99200
    }
    
    return generate_premarket_report(
        global_markets, previous_day, technical_outlook,
        corporate_events, stocks_to_watch, risk_warnings, trading_strategy
    )


if __name__ == "__main__":
    html = generate_sample_premarket_report()
    
    # Save to file
    with open('sample_premarket_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Sample pre-market report saved to sample_premarket_report.html")
