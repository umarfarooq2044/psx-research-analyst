"""
PSX Research Analyst - Post-Market Deep Analysis Template
Generates comprehensive post-market analysis email (4:30 PM)
"""
from typing import Dict, List, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_postmarket_css() -> str:
    """CSS styles for post-market email"""
    return """
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #238636, #1f6feb); padding: 30px; border-radius: 12px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: white; font-size: 26px; }
        .header .subtitle { color: rgba(255,255,255,0.85); font-size: 14px; margin-top: 10px; }
        .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
        .summary-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }
        .summary-value { font-size: 24px; font-weight: 700; }
        .summary-label { font-size: 11px; color: #8b949e; margin-top: 4px; text-transform: uppercase; }
        .section { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
        .section-title { color: #58a6ff; font-size: 18px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #30363d; }
        .positive { color: #3fb950; }
        .negative { color: #f85149; }
        .neutral { color: #8b949e; }
        .stock-table { width: 100%; border-collapse: collapse; }
        .stock-table th { text-align: left; padding: 10px; color: #8b949e; font-size: 12px; border-bottom: 1px solid #30363d; }
        .stock-table td { padding: 12px 10px; border-bottom: 1px solid #21262d; }
        .stock-symbol { font-weight: 600; color: #58a6ff; }
        .score-bar { background: #21262d; height: 8px; border-radius: 4px; overflow: hidden; width: 100px; display: inline-block; vertical-align: middle; }
        .score-fill { height: 100%; border-radius: 4px; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-strong-buy { background: rgba(63,185,80,0.2); color: #3fb950; }
        .badge-buy { background: rgba(88,166,255,0.2); color: #58a6ff; }
        .badge-hold { background: rgba(139,148,158,0.2); color: #8b949e; }
        .badge-reduce { background: rgba(210,153,34,0.2); color: #d29922; }
        .badge-sell { background: rgba(248,81,73,0.2); color: #f85149; }
        .sector-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #21262d; }
        .indicator-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .indicator { background: #0d1117; border-radius: 8px; padding: 14px; }
        .indicator-label { font-size: 11px; color: #8b949e; }
        .indicator-value { font-size: 18px; font-weight: 600; margin-top: 4px; }
        .tomorrow-box { background: linear-gradient(135deg, rgba(88,166,255,0.1), rgba(35,134,54,0.1)); border: 1px solid #30363d; border-radius: 12px; padding: 20px; }
        .action-item { background: #0d1117; border-left: 3px solid #58a6ff; padding: 10px 15px; margin: 8px 0; border-radius: 0 8px 8px 0; }
        .footer { text-align: center; color: #8b949e; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #30363d; }
    </style>
    """


def generate_postmarket_report(
    market_summary: Dict,
    top_stocks: List[Dict],
    sector_performance: List[Dict],
    technical_analysis: Dict,
    news_summary: Dict,
    risk_assessment: Dict,
    tomorrow_outlook: Dict,
    action_items: List[str],
    undervalued_gems: List[Dict] = None
) -> str:
    """
    Generate comprehensive post-market analysis HTML email
    """
    
    now = datetime.now()
    if undervalued_gems is None: undervalued_gems = []
    
    def get_rating_badge(rating: str) -> str:
        rating_map = {
            'STRONG BUY': 'badge-strong-buy',
            'BUY': 'badge-buy',
            'HOLD': 'badge-hold',
            'REDUCE': 'badge-reduce',
            'SELL/AVOID': 'badge-sell'
        }
        return rating_map.get(rating, 'badge-hold')
    
    def get_score_color(score: int) -> str:
        if score >= 70:
            return '#3fb950'
        elif score >= 55:
            return '#58a6ff'
        elif score >= 40:
            return '#d29922'
        else:
            return '#f85149'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {get_postmarket_css()}
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>📊 PSX POST-MARKET DEEP ANALYSIS</h1>
                <div class="subtitle">{now.strftime('%A, %B %d, %Y')} | Market Close Report | Generated at {now.strftime('%I:%M %p')} PKT</div>
            </div>
            
            <!-- Market Summary Cards -->
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value {'positive' if (market_summary.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {market_summary.get('close_value', 0):,.0f}
                    </div>
                    <div class="summary-label">KSE-100 Close</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value {'positive' if (market_summary.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {'+' if (market_summary.get('change_percent', 0) or 0) > 0 else ''}{market_summary.get('change_percent', 0) or 0:.2f}%
                    </div>
                    <div class="summary-label">Day Change</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value">{(market_summary.get('volume') or 0):,.0f}</div>
                    <div class="summary-label">Volume (M)</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value {'positive' if (market_summary.get('advancing') or 0) > (market_summary.get('declining') or 0) else 'negative'}">
                        {market_summary.get('advancing') or 0}/{market_summary.get('declining') or 0}
                    </div>
                    <div class="summary-label">Adv/Dec</div>
                </div>
            </div>
            
            <!-- Top Stocks by 100-Point Score -->
            <div class="section">
                <div class="section-title">🏆 TOP STOCKS - 100-POINT ANALYSIS</div>
                <table class="stock-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Price</th>
                            <th>Change</th>
                            <th>Score</th>
                            <th>Rating</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td><span class="stock-symbol">{stock['symbol']}</span></td>
                            <td>Rs. {stock.get('price', 0):,.2f}</td>
                            <td class="{'positive' if (stock.get('change_percent', 0) or 0) > 0 else 'negative'}">
                                {'+' if (stock.get('change_percent', 0) or 0) > 0 else ''}{stock.get('change_percent', 0) or 0:.2f}%
                            </td>
                            <td>
                                <div class="score-bar">
                                    <div class="score-fill" style="width: {stock.get('score', 0)}%; background: {get_score_color(stock.get('score', 0))}"></div>
                                </div>
                                <span style="margin-left: 8px; font-weight: 600;">{stock.get('score', 0)}/100</span>
                            </td>
                            <td><span class="badge {get_rating_badge(stock.get('rating', 'HOLD'))}">{stock.get('rating', 'HOLD')}</span></td>
                        </tr>
                        ''' for stock in top_stocks[:10]])}
                    </tbody>
                </table>
            </div>
            
            <!-- Undervalued Gems -->
            {'' if not undervalued_gems else f'''
            <div class="section">
                <div class="section-title">💎 UNDERVALUED GEMS (Deep Value + Growth)</div>
                <div class="indicator-grid" style="grid-template-columns: repeat(2, 1fr);">
                    {''.join([f'''
                    <div class="indicator" style="border: 1px solid #3fb950;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="stock-symbol" style="font-size: 16px;">{gem['symbol']}</span>
                            <span class="badge badge-strong-buy" style="font-size: 10px;">SCORE: {gem['score']}</span>
                        </div>
                        <div style="margin-top: 8px; font-size: 12px; color: #8b949e;">
                            Relative P/E: <strong style="color: #c9d1d9;">{gem.get('pe_ratio', 'N/A')}</strong> vs Sector
                        </div>
                        <div style="margin-top: 4px; font-size: 12px; color: #8b949e;">
                            Growth: <strong style="color: #3fb950;">{gem.get('growth', 'N/A')}%</strong>
                        </div>
                        <div style="margin-top: 8px; font-size: 11px;">
                            {gem.get('reason', 'Strong Fundamentals')}
                        </div>
                    </div>
                    ''' for gem in undervalued_gems[:4]])}
                </div>
            </div>
            '''}
            
            <!-- Sector Performance -->
            <div class="section">
                <div class="section-title">📈 SECTOR PERFORMANCE</div>
                {''.join([f'''
                <div class="sector-row">
                    <div style="font-weight: 600;">{sector['name']}</div>
                    <div class="{'positive' if (sector.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {'+' if (sector.get('change_percent', 0) or 0) > 0 else ''}{sector.get('change_percent', 0) or 0:.2f}%
                    </div>
                </div>
                ''' for sector in sector_performance])}
            </div>
            
            <!-- Technical Analysis -->
            <div class="section">
                <div class="section-title">📉 TECHNICAL ANALYSIS - KSE-100</div>
                <div class="indicator-grid">
                    <div class="indicator">
                        <div class="indicator-label">RSI (14)</div>
                        <div class="indicator-value {'positive' if (technical_analysis.get('rsi', 50) or 50) < 40 else 'negative' if (technical_analysis.get('rsi', 50) or 50) > 70 else ''}">
                            {technical_analysis.get('rsi', 'N/A')}
                        </div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">MACD</div>
                        <div class="indicator-value {'positive' if technical_analysis.get('macd_trend') == 'bullish' else 'negative' if technical_analysis.get('macd_trend') == 'bearish' else ''}">
                            {technical_analysis.get('macd_trend', 'Neutral').title()}
                        </div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Trend</div>
                        <div class="indicator-value">{technical_analysis.get('trend', 'Consolidating')}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Support</div>
                        <div class="indicator-value">{f"{technical_analysis.get('support'):,.0f}" if technical_analysis.get('support') else 'N/A'}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Resistance</div>
                        <div class="indicator-value">{f"{technical_analysis.get('resistance'):,.0f}" if technical_analysis.get('resistance') else 'N/A'}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Bollinger</div>
                        <div class="indicator-value">{technical_analysis.get('bollinger_signal', 'Neutral')}</div>
                    </div>
                </div>
            </div>
            
            <!-- News Summary -->
            <div class="section">
                <div class="section-title">📰 NEWS & SENTIMENT SUMMARY</div>
                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                    <div>
                        <span style="color: #8b949e;">Headlines Analyzed:</span> 
                        <strong>{news_summary.get('total', 0)}</strong>
                    </div>
                    <div>
                        <span style="color: #8b949e;">Positive:</span> 
                        <strong class="positive">{news_summary.get('positive', 0)}</strong>
                    </div>
                    <div>
                        <span style="color: #8b949e;">Negative:</span> 
                        <strong class="negative">{news_summary.get('negative', 0)}</strong>
                    </div>
                    <div>
                        <span style="color: #8b949e;">Overall:</span> 
                        <strong class="{'positive' if news_summary.get('sentiment') == 'bullish' else 'negative' if news_summary.get('sentiment') == 'bearish' else ''}">{news_summary.get('sentiment', 'Mixed').title()}</strong>
                    </div>
                </div>
                <ul>
                    {''.join([f"<li>{headline}</li>" for headline in news_summary.get('top_headlines', [])[:5]])}
                </ul>
            </div>
            
            <!-- Risk Assessment -->
            <div class="section">
                <div class="section-title">⚠️ RISK ASSESSMENT</div>
                <div class="indicator-grid">
                    <div class="indicator">
                        <div class="indicator-label">Market Risk</div>
                        <div class="indicator-value {'negative' if risk_assessment.get('market_risk') == 'high' else 'positive' if risk_assessment.get('market_risk') == 'low' else ''}">{risk_assessment.get('market_risk', 'Medium').title()}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Currency Risk</div>
                        <div class="indicator-value">{risk_assessment.get('currency_risk', 'Medium').title()}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Global Risk</div>
                        <div class="indicator-value">{risk_assessment.get('global_risk', 'Medium').title()}</div>
                    </div>
                </div>
                {f'''<div style="margin-top: 15px; padding: 12px; background: rgba(248,81,73,0.1); border-radius: 8px; border: 1px solid #f85149;">
                    <strong style="color: #f85149;">⚠️ Key Risk:</strong> {risk_assessment.get('key_warning', '')}
                </div>''' if risk_assessment.get('key_warning') else ''}
            </div>
            
            <!-- Tomorrow's Outlook -->
            <div class="section">
                <div class="section-title">🔮 TOMORROW'S OUTLOOK</div>
                <div class="tomorrow-box">
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 15px;">
                        <div>
                            <div style="color: #8b949e; font-size: 12px;">Expected Bias</div>
                            <div style="font-size: 20px; font-weight: 700;" class="{'positive' if tomorrow_outlook.get('bias') == 'bullish' else 'negative' if tomorrow_outlook.get('bias') == 'bearish' else ''}">{tomorrow_outlook.get('bias', 'Neutral').upper()}</div>
                        </div>
                        <div>
                            <div style="color: #8b949e; font-size: 12px;">Expected Range</div>
                            <div style="font-size: 16px; font-weight: 600;">{f"{tomorrow_outlook.get('range_low'):,.0f}" if tomorrow_outlook.get('range_low') else 'N/A'} - {f"{tomorrow_outlook.get('range_high'):,.0f}" if tomorrow_outlook.get('range_high') else 'N/A'}</div>
                        </div>
                        <div>
                            <div style="color: #8b949e; font-size: 12px;">Probability</div>
                            <div style="font-size: 16px; font-weight: 600;">{tomorrow_outlook.get('confidence', 50)}% confidence</div>
                        </div>
                    </div>
                    <div style="color: #c9d1d9;">{tomorrow_outlook.get('narrative', '')}</div>
                </div>
            </div>
            
            <!-- Action Items -->
            <div class="section">
                <div class="section-title">✅ ACTION ITEMS FOR TOMORROW</div>
                {''.join([f'<div class="action-item">{item}</div>' for item in action_items])}
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p>PSX Autonomous Research Analyst | Post-Market Deep Analysis</p>
                <p>This report is generated automatically using technical and sentiment analysis. Not financial advice.</p>
                <p style="margin-top: 10px;">© {now.year} PSX Research Analyst</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


if __name__ == "__main__":
    # Sample data for testing
    market_summary = {
        'close_value': 98456,
        'change_percent': 0.67,
        'volume': 312,
        'advancing': 245,
        'declining': 142
    }
    
    top_stocks = [
        {'symbol': 'OGDC', 'price': 145.50, 'change_percent': 2.3, 'score': 87, 'rating': 'STRONG BUY'},
        {'symbol': 'HBL', 'price': 168.25, 'change_percent': 1.8, 'score': 78, 'rating': 'BUY'},
        {'symbol': 'MARI', 'price': 1890.00, 'change_percent': 3.1, 'score': 82, 'rating': 'STRONG BUY'},
        {'symbol': 'FFC', 'price': 112.30, 'change_percent': 0.5, 'score': 71, 'rating': 'BUY'},
        {'symbol': 'PSO', 'price': 298.75, 'change_percent': -0.8, 'score': 65, 'rating': 'HOLD'}
    ]
    
    sector_performance = [
        {'name': 'Oil & Gas', 'change_percent': 1.8},
        {'name': 'Banking', 'change_percent': 1.2},
        {'name': 'Fertilizer', 'change_percent': 0.5},
        {'name': 'Cement', 'change_percent': -0.3},
        {'name': 'Power', 'change_percent': -0.8}
    ]
    
    technical_analysis = {
        'rsi': 58,
        'macd_trend': 'bullish',
        'trend': 'Uptrend',
        'support': 97500,
        'resistance': 99500,
        'bollinger_signal': 'Neutral'
    }
    
    news_summary = {
        'total': 45,
        'positive': 23,
        'negative': 12,
        'sentiment': 'bullish',
        'top_headlines': [
            'OGDC announces major oil discovery',
            'SBP maintains interest rates',
            'Banking sector posts record profits'
        ]
    }
    
    risk_assessment = {
        'market_risk': 'low',
        'currency_risk': 'medium',
        'global_risk': 'low',
        'key_warning': 'Monitor USD/PKR for any sudden movements'
    }
    
    tomorrow_outlook = {
        'bias': 'bullish',
        'range_low': 98000,
        'range_high': 99200,
        'confidence': 65,
        'narrative': 'Markets expected to continue upward momentum on strong banking earnings and stable oil prices.'
    }
    
    action_items = [
        'Accumulate OGDC if price dips below Rs. 143',
        'Book partial profits in HBL above Rs. 170',
        'Watch for FFC dividend announcement',
        'Maintain stop-loss at 97,500 for index positions'
    ]
    
    html = generate_postmarket_report(
        market_summary, top_stocks, sector_performance,
        technical_analysis, news_summary, risk_assessment,
        tomorrow_outlook, action_items
    )
    
    with open('sample_postmarket_report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Sample post-market report saved to sample_postmarket_report.html")
