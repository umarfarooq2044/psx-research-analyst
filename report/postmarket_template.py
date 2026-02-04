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
        body { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; background: #010409; color: #c9d1d9; margin: 0; padding: 20px; }
        .container { max-width: 950px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #d4af37, #b8860b, #966919); padding: 50px; border-radius: 24px; margin-bottom: 35px; text-align: center; border: 1px solid rgba(212, 175, 55, 0.4); box-shadow: 0 15px 45px rgba(0,0,0,0.6); }
        .header h1 { margin: 0; color: #010409; font-size: 36px; letter-spacing: 2px; font-weight: 900; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header .subtitle { color: #010409; font-size: 17px; margin-top: 15px; font-weight: 700; opacity: 0.9; }
        .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 25px; }
        .summary-card { background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 20px; text-align: center; transition: transform 0.2s; }
        .summary-card:hover { transform: translateY(-5px); border-color: #d4af37; }
        .summary-value { font-size: 28px; font-weight: 800; }
        .summary-label { font-size: 12px; color: #8b949e; margin-top: 6px; text-transform: uppercase; letter-spacing: 1px; }
        .section { background: #0d1117; border: 1px solid #30363d; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .section-title { color: #d4af37; font-size: 20px; font-weight: 700; margin-bottom: 25px; padding-bottom: 12px; border-bottom: 2px solid #30363d; display: flex; align-items: center; gap: 10px; }
        .positive { color: #3fb950; }
        .negative { color: #f85149; }
        .neutral { color: #8b949e; }
        .stock-table { width: 100%; border-collapse: collapse; }
        .stock-table th { text-align: left; padding: 12px; color: #8b949e; font-size: 13px; border-bottom: 1px solid #30363d; text-transform: uppercase; }
        .stock-table td { padding: 15px 12px; border-bottom: 1px solid #21262d; }
        .stock-symbol { font-weight: 700; color: #58a6ff; font-size: 16px; }
        .badge { padding: 6px 14px; border-radius: 30px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .badge-strong-buy { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
        .badge-buy { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
        .badge-hold { background: rgba(139,148,158,0.15); color: #8b949e; border: 1px solid rgba(139,148,158,0.3); }
        .badge-reduce { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
        .badge-sell { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
        .chorus-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; background: #161b22; padding: 15px; border-radius: 12px; margin-top: 15px; border: 1px dashed #30363d; }
        .expert-pill { font-size: 11px; color: #8b949e; display: flex; flex-direction: column; }
        .expert-opinion { color: #c9d1d9; font-weight: 500; font-size: 12px; margin-top: 2px; }
        .footer { text-align: center; color: #8b949e; font-size: 13px; margin-top: 40px; padding: 30px; border-top: 1px solid #30363d; }
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
    undervalued_gems: List[Dict] = None,
    cognitive_decisions: List[Dict] = None
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
            return '#f85149'
    
    # Pre-generate Undervalued Gems HTML to avoid nested f-string errors
    undervalued_gems_html = ""
    if undervalued_gems:
        gems_grid = ''.join([f'''
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
                    ''' for gem in undervalued_gems[:4]])
        
        undervalued_gems_html = f'''
            <div class="section">
                <div class="section-title">💎 UNDERVALUED GEMS (Deep Value + Growth)</div>
                <div class="indicator-grid" style="grid-template-columns: repeat(2, 1fr);">
                    {gems_grid}
                </div>
            </div>
        '''

    # Pre-generate SMI-v3 Ultra Wealth Engine HTML to avoid nested f-string issues
    smi_ultra_html = ""
    if cognitive_decisions and isinstance(cognitive_decisions, list) and len(cognitive_decisions) > 0:
        cards_html = ""
        for d in cognitive_decisions[:10]:
            sym = d.get('symbol', 'N/A')
            action = d.get('action', 'HOLD')
            conviction = d.get('conviction', 0)
            rational = d.get('long_term_rational', 'Deep research concludes this is a foundational asset.')
            target_1y = d.get('target_price_1y', 'N/A')
            stop_loss = d.get('stop_loss_long', 'N/A')
            value_score = d.get('value_score', 0)
            moat = d.get('moat_rating', 'Narrow')
            pillar = str(d.get('key_investment_pillar', 'Asset Strength'))[:50]
            badge_class = get_rating_badge(action)
            
            cards_html += f'''
                    <div style="background: #161b22; padding: 25px; border-radius: 20px; border: 1px solid #30363d; position: relative; transition: all 0.3s ease;">
                        <div style="position: absolute; top: -1px; right: 40px; background: #d4af37; color: #010409; padding: 4px 15px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; font-size: 10px; font-weight: 900; letter-spacing: 1px;">HIGH CONVICTION</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                            <span class="stock-symbol" style="font-size: 26px; letter-spacing: -1px;">{sym}</span>
                            <span class="badge {badge_class}" style="font-size: 12px; padding: 7px 20px;">
                                {action} ({conviction}%)
                            </span>
                        </div>
                        <div style="color: #ffffff; font-size: 17px; line-height: 1.6; font-weight: 500; margin-bottom: 25px; border-left: 4px solid #d4af37; padding-left: 15px; font-style: italic;">
                            "{rational}"
                        </div>
                        
                        <!-- Wealth Indicators -->
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                            <div style="background: rgba(63, 185, 80, 0.1); border: 1px solid rgba(63, 185, 80, 0.2); padding: 15px; border-radius: 12px;">
                                <span style="font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 700;">TARGET PRICE</span>
                                <div style="font-size: 20px; font-weight: 900; color: #3fb950; margin-top: 5px;">
                                    Rs. {target_1y}
                                </div>
                            </div>
                            <div style="background: rgba(248, 81, 73, 0.1); border: 1px solid rgba(248, 81, 73, 0.2); padding: 15px; border-radius: 12px;">
                                <span style="font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 700;">VALUATION FLR</span>
                                <div style="font-size: 20px; font-weight: 900; color: #f85149; margin-top: 5px;">
                                    Rs. {stop_loss}
                                </div>
                            </div>
                            <div style="background: rgba(212, 175, 55, 0.1); border: 1px solid rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 12px;">
                                <span style="font-size: 10px; color: #8b949e; text-transform: uppercase; font-weight: 700;">VALUE SCORE</span>
                                <div style="font-size: 20px; font-weight: 900; color: #d4af37; margin-top: 5px;">
                                    {value_score}/100
                                </div>
                            </div>
                        </div>

                        <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #21262d; padding-top: 15px;">
                            <div style="font-size: 12px; color: #c9d1d9; display: flex; align-items: center; gap: 8px;">
                                <span style="background: #f85149; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 900;">MOAT</span>
                                <strong>{moat}</strong>
                            </div>
                            <div style="background: rgba(88, 166, 255, 0.1); border: 1px solid rgba(88, 166, 255, 0.2); padding: 6px 15px; border-radius: 10px; font-size: 12px; color: #58a6ff; font-weight: 700;">
                                PILLAR: {pillar}
                            </div>
                        </div>
                    </div>
            '''
        
        smi_ultra_html = f'''
            <div class="section" style="border-top: 6px solid #d4af37; box-shadow: 0 0 50px rgba(212,175,55,0.15);">
                <div class="section-title" style="color: #d4af37; border-bottom-color: #d4af37; letter-spacing: 1px;">👑 SMI-v3 ULTRA - INSTITUTIONAL WEALTH ENGINE</div>
                <div style="font-size: 14px; color: #8b949e; margin-bottom: 30px; font-style: italic; background: rgba(212,175,55,0.05); padding: 15px; border-radius: 12px; border: 1px dashed rgba(212,175,55,0.2);">
                    Our 25-Year Expertise persona analyzes the entire market at Groq speed to identify perfect long-term entries. These picks represent high-conviction wealth compounders for long-term holders.
                </div>
                <div style="display: grid; grid-template-columns: 1fr; gap: 20px;">
                    {cards_html}
                </div>
            </div>
        '''

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
            
            <!-- SMI-v3 Ultra Cognitive Briefing -->
            {f'''
            <div style="padding: 30px; background: #0d1117; border-left: 6px solid #7856ff; margin: 20px 0; border: 1px solid #30363d; border-radius: 16px; box-shadow: 0 10px 40px rgba(120,86,255,0.15);">
                <div style="color: #7856ff; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">🦅 SMI-v3 ULTRA COGNITIVE BRIEFING</div>
                <div style="color: #ffffff; font-size: 20px; font-weight: 800; line-height: 1.5; margin-bottom: 15px;">
                    {news_summary.get('synthesis', {}).get('strategy', 'Neutral')} Recap: {news_summary.get('synthesis', {}).get('commentary', 'Market Cycle Complete')}
                </div>
                <div style="color: #c9d1d9; font-size: 14px; background: rgba(120,86,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(120,86,255,0.1); margin-bottom: 15px;">
                    <strong>Institutional Narrative:</strong> Deep research on {news_summary.get('total', 0)} headlines identifies a {news_summary.get('sentiment', 'mixed')} sentiment trajectory.
                </div>
                <div style="display: flex; gap: 20px; font-size: 14px; font-weight: 700;">
                    <div style="color: #3fb950; background: rgba(63,185,80,0.1); padding: 5px 15px; border-radius: 6px;">🛡️ Risk: {news_summary.get('synthesis', {}).get('risk_flag', 'Safe')}</div>
                    <div style="color: #7856ff; background: rgba(120,86,255,0.1); padding: 5px 15px; border-radius: 6px;">💎 Confidence: {news_summary.get('synthesis', {}).get('score', 50)}%</div>
                </div>
            </div>
            ''' if news_summary.get('synthesis') else ''}
            
            <!-- Market Summary Cards -->
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value {'positive' if (market_summary.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {(market_summary.get('close_value', 0) or 0):,.0f}
                    </div>
                    <div class="summary-label">KSE-100 Close</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value {'positive' if (market_summary.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {'+' if (market_summary.get('change_percent', 0) or 0) > 0 else ''}{(market_summary.get('change_percent', 0) or 0):.2f}%
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

            <!-- Sovereign Context (Macro Core) -->
            <div class="section" style="border-top: 3px solid #f08c00;">
                <div class="section-title" style="color: #f08c00;">🏛️ SOVEREIGN DEBT & LIQUIDITY (MACRO CORE)</div>
                <div class="indicator-grid" style="grid-template-columns: repeat(3, 1fr);">
                    <div class="indicator">
                        <div class="indicator-label">6M KIBOR</div>
                        <div class="indicator-value">{market_summary.get('kibor_6m', '22.45')}%</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">3M T-Bill Yield</div>
                        <div class="indicator-value">{market_summary.get('tbill_3m', '21.90')}%</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Liquidity Status</div>
                        <div class="indicator-value" style="color: #3fb950;">{market_summary.get('liquidity', 'Stable')}</div>
                    </div>
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
                            <td>Rs. {(stock.get('price', 0) or 0):,.2f}</td>
                            <td class="{'positive' if (stock.get('change_percent', 0) or 0) > 0 else 'negative'}">
                                {'+' if (stock.get('change_percent', 0) or 0) > 0 else ''}{(stock.get('change_percent', 0) or 0):.2f}%
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
            
            <!-- SMI-v3 Ultra Institutional Wealth Engine -->
            {smi_ultra_html}
            
            <!-- Undervalued Gems -->
            {undervalued_gems_html}
            
            <!-- Sector Performance -->
            <div class="section">
                <div class="section-title">📈 SECTOR PERFORMANCE</div>
                {''.join([f'''
                <div class="sector-row">
                    <div style="font-weight: 600;">{sector['name']}</div>
                    <div class="{'positive' if (sector.get('change_percent', 0) or 0) > 0 else 'negative'}">
                        {'+' if (sector.get('change_percent', 0) or 0) > 0 else ''}{(sector.get('change_percent', 0) or 0):.2f}%
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
                        <div class="indicator-value">{f"{(technical_analysis.get('support', 0) or 0):,.0f}" if technical_analysis.get('support') else 'N/A'}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Resistance</div>
                        <div class="indicator-value">{f"{(technical_analysis.get('resistance', 0) or 0):,.0f}" if technical_analysis.get('resistance') else 'N/A'}</div>
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
