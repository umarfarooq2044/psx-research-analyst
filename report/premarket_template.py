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
        body { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; background: #010409; color: #c9d1d9; margin: 0; padding: 20px; }
        .container { max-width: 850px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #d4af37, #b8860b); padding: 35px; border-radius: 16px; margin-bottom: 25px; text-align: center; border: 1px solid rgba(212,175,55,0.3); }
        .header h1 { margin: 0; color: #010409; font-size: 30px; letter-spacing: 1.5px; font-weight: 800; }
        .header .subtitle { color: #1a1a1a; font-size: 15px; margin-top: 10px; font-weight: 600; }
        .section { background: #0d1117; border-radius: 16px; padding: 25px; margin-bottom: 20px; border: 1px solid #30363d; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .section-title { color: #d4af37; font-size: 18px; font-weight: 700; margin-bottom: 20px; border-bottom: 2px solid #30363d; padding-bottom: 12px; display: flex; align-items: center; gap: 10px; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
        .metric { background: #161b22; padding: 15px; border-radius: 12px; border: 1px solid #21262d; }
        .metric-label { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 6px; }
        .positive { color: #3fb950; }
        .negative { color: #f85149; }
        .neutral { color: #8b949e; }
        .stock-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #21262d; }
        .stock-symbol { font-weight: 700; color: #58a6ff; font-size: 17px; }
        .badge { padding: 6px 14px; border-radius: 30px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
        .badge-buy { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
        .badge-sell { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
        .badge-hold { background: rgba(139,148,158,0.15); color: #8b949e; border: 1px solid rgba(139,148,158,0.3); }
        .alert-box { background: rgba(248,81,73,0.05); border: 1px solid #f85149; border-radius: 12px; padding: 15px; margin-top: 20px; }
        .strategy-box { background: rgba(212,175,55,0.05); border: 1px solid #d4af37; border-radius: 12px; padding: 20px; }
        ul { padding-left: 20px; margin: 12px 0; }
        li { margin: 10px 0; color: #c9d1d9; font-size: 14px; }
        .footer { text-align: center; color: #8b949e; font-size: 13px; margin-top: 30px; padding: 25px; border-top: 1px solid #30363d; }
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

            <!-- SMI-v2 Alpha Engine Briefing -->
            {f'''
            <div style="padding: 25px; background: #0d1117; border-left: 5px solid #d4af37; margin: 15px 0; border: 1px solid #30363d; border-radius: 12px;">
                <div style="color: #d4af37; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">👑 SMI-v2 ALPHA ENGINE BRIEFING</div>
                <div style="color: #ffffff; font-size: 18px; font-weight: 700; line-height: 1.4; margin-bottom: 10px;">
                    {trading_strategy.get('synthesis', {}).get('strategy', 'Neutral')} Outlook: {trading_strategy.get('synthesis', {}).get('commentary', 'Awaiting Market Open')}
                </div>
                <div style="color: #8b949e; font-size: 13px; font-style: italic;">
                    Expert Chorus Consensus confirms {trading_strategy.get('bias', 'neutral')} opening bias.
                </div>
                <div style="display: flex; gap: 20px; margin-top: 15px; font-size: 13px; font-weight: 600;">
                    <div style="color: #f85149;">⚠️ RISK: {trading_strategy.get('synthesis', {}).get('risk_flag', 'Safe')}</div>
                    <div style="color: #d4af37;">💎 CONFIDENCE: {trading_strategy.get('synthesis', {}).get('score', 50)}%</div>
                </div>
            </div>
            ''' if trading_strategy.get('synthesis') else ''}
            
            <!-- Global Markets Overnight -->
            <div class="section">
                <div class="section-title">🌍 OVERNIGHT GLOBAL MARKETS</div>
                <div class="grid">
                    <div class="metric">
                        <div class="metric-label">S&P 500</div>
                        <div class="metric-value {'positive' if (global_markets.get('sp500_change', 0) or 0) > 0 else 'negative'}">
                            {global_markets.get('sp500', 'N/A')} 
                            ({'+' if (global_markets.get('sp500_change', 0) or 0) > 0 else ''}{(global_markets.get('sp500_change', 0) or 0):.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">NASDAQ</div>
                        <div class="metric-value {'positive' if (global_markets.get('nasdaq_change', 0) or 0) > 0 else 'negative'}">
                            {global_markets.get('nasdaq', 'N/A')}
                            ({'+' if (global_markets.get('nasdaq_change', 0) or 0) > 0 else ''}{(global_markets.get('nasdaq_change', 0) or 0):.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">WTI Crude Oil</div>
                        <div class="metric-value {'positive' if (global_markets.get('wti_change', 0) or 0) > 0 else 'negative'}">
                            ${global_markets.get('wti_oil', 'N/A')}
                            ({'+' if (global_markets.get('wti_change', 0) or 0) > 0 else ''}{(global_markets.get('wti_change', 0) or 0):.2f}%)
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
                            {(previous_day.get('close_value', 0) or 0):,.0f}
                            ({'+' if (previous_day.get('change_percent', 0) or 0) > 0 else ''}{(previous_day.get('change_percent', 0) or 0):.2f}%)
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Volume</div>
                        <div class="metric-value">{(previous_day.get('volume', 0) or 0):,} shares</div>
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
                        <div class="metric-value">{(technical_outlook.get('support_1', 0) or 0):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Resistance Level 1</div>
                        <div class="metric-value">{(technical_outlook.get('resistance_1', 0) or 0):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Expected Range</div>
                        <div class="metric-value">{(technical_outlook.get('expected_low', 0) or 0):,.0f} - {(technical_outlook.get('expected_high', 0) or 0):,.0f}</div>
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
            
            <!-- SMI-v2 Alpha Engine (Chorus Consensus) -->
            <div class="section" style="border-top: 4px solid #d4af37;">
                <div class="section-title" style="color: #d4af37;">👑 ALPHA ENGINE (CHORUS CONSENSUS)</div>
                {''.join([f'''
                <div class="stock-row" style="flex-direction: column; align-items: flex-start; gap: 10px; background: #161b22; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #21262d;">
                    <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                        <span class="stock-symbol" style="font-size: 20px;">{stock['symbol']}</span>
                        <span class="badge badge-{stock.get('action', 'hold').lower()}">{stock.get('action', 'HOLD')}</span>
                    </div>
                    
                    <div style="color: #e7e9ea; font-size: 14px; font-weight: 500; line-height: 1.5;">
                        "{stock.get('reason', 'Consensus-driven reasoning')}"
                    </div>

                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 5px;">
                        <div style="flex: 1; background: #0d1117; padding: 10px; border-radius: 8px; border: 1px solid #30363d;">
                            <div style="font-size: 10px; color: #8b949e; text-transform: uppercase;">Confidence</div>
                            <div style="font-size: 15px; font-weight: 700; color: #d4af37;">{stock.get('conviction', '50%')}</div>
                        </div>
                        <div style="flex: 2; background: #0d1117; padding: 10px; border-radius: 8px; border: 1px solid #30363d;">
                            <div style="font-size: 10px; color: #8b949e; text-transform: uppercase;">Strategic Path</div>
                            <div style="font-size: 13px; font-weight: 600;">{stock.get('future_path', 'Monitoring catalysts...')}</div>
                        </div>
                    </div>

                    <div style="width: 100%; background: rgba(248,81,73,0.1); padding: 10px; border-radius: 8px; font-size: 12px; display: flex; justify-content: space-between;">
                        <span><strong style="color: #f85149;">RISK:</strong> {stock.get('black_swan', 'Standard Volatility')}</span>
                        <span style="color: #d4af37; font-weight: 700;">ATR STOP: Rs. {stock.get('atr_stop', 'N/A')}</span>
                    </div>
                </div>
                ''' for stock in stocks_to_watch[:10]])}
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
