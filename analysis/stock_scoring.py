"""
PSX Research Analyst - 100-Point Stock Scoring System
Comprehensive scoring based on 20+ years of trading experience in risky markets

SCORING BREAKDOWN (100 Points Total):
- Financial Health: 35 points
- Valuation: 25 points
- Technical Momentum: 20 points
- Sector & Macro: 15 points
- News & Catalysts: 5 points
"""
from typing import Dict, Optional, List
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SCORE_WEIGHTS, SCORE_RATINGS, SECTORS
from database.db_manager import db
from analysis.technical import analyze_ticker_technical, get_technical_score_20
from analysis.sentiment import get_ticker_sentiment, get_sentiment_score_component


# ============================================================================
# FINANCIAL HEALTH SCORE (35 points)
# ============================================================================

def calculate_financial_score(fundamentals: Dict) -> Dict:
    """
    Calculate financial health score (0-35 points)
    
    Components:
    - Earnings Quality: 10 points
    - Profitability Margins: 10 points
    - Dividend Sustainability: 10 points
    - Financial Stability: 5 points
    """
    score = 0
    details = {}
    
    # Earnings Quality (10 points)
    eps_growth = fundamentals.get('eps_growth', 0) or 0
    if eps_growth > 15:
        earnings_score = 10
    elif eps_growth > 5:
        earnings_score = 7
    elif eps_growth > 0:
        earnings_score = 4
    elif eps_growth > -5:
        earnings_score = 2
    else:
        earnings_score = 0
    
    score += earnings_score
    details['earnings_quality'] = f"{earnings_score}/10 (EPS growth: {eps_growth}%)"
    
    # Profitability Margins (10 points)
    net_margin = fundamentals.get('net_margin', 0) or 0
    margin_trend = fundamentals.get('margin_trend', 'stable')
    
    if net_margin > 15 and margin_trend in ['improving', 'stable']:
        margin_score = 10
    elif net_margin > 10:
        margin_score = 8
    elif net_margin > 5:
        margin_score = 6
    elif net_margin > 0:
        margin_score = 4
    else:
        margin_score = 0
    
    # Adjust for trend
    if margin_trend == 'improving':
        margin_score = min(10, margin_score + 1)
    elif margin_trend == 'declining':
        margin_score = max(0, margin_score - 2)
    
    score += margin_score
    details['profitability'] = f"{margin_score}/10 (Net margin: {net_margin}%)"
    
    # Dividend Sustainability (10 points)
    dividend_yield = fundamentals.get('dividend_yield', 0) or 0
    payout_ratio = fundamentals.get('payout_ratio', 50) or 50
    
    if payout_ratio < 40 and dividend_yield > 3:
        dividend_score = 10
    elif payout_ratio < 60 and dividend_yield > 2:
        dividend_score = 8
    elif payout_ratio < 80 and dividend_yield > 0:
        dividend_score = 6
    elif payout_ratio < 100:
        dividend_score = 3
    else:
        dividend_score = 0
    
    score += dividend_score
    details['dividend_sustainability'] = f"{dividend_score}/10 (Yield: {dividend_yield}%, Payout: {payout_ratio}%)"
    
    # Financial Stability (5 points)
    debt_equity = fundamentals.get('debt_equity', 1) or 1
    
    if debt_equity < 0.5:
        stability_score = 5
    elif debt_equity < 1:
        stability_score = 4
    elif debt_equity < 2:
        stability_score = 2
    else:
        stability_score = 0
    
    score += stability_score
    details['stability'] = f"{stability_score}/5 (D/E: {debt_equity})"
    
    return {
        'score': score,
        'max_score': 35,
        'details': details
    }


# ============================================================================
# VALUATION SCORE (25 points)
# ============================================================================

def calculate_valuation_score(fundamentals: Dict, current_price: float = None) -> Dict:
    """
    Calculate valuation score (0-25 points)
    
    Components:
    - P/E Valuation: 10 points
    - Dividend Yield: 10 points
    - Price-to-Book: 5 points
    """
    score = 0
    details = {}
    
    # P/E Valuation (10 points)
    pe_ratio = fundamentals.get('pe_ratio', 15) or 15
    
    if pe_ratio < 7:
        pe_score = 10  # Deep value
    elif pe_ratio < 9:
        pe_score = 8  # Attractive
    elif pe_ratio < 12:
        pe_score = 6  # Fair
    elif pe_ratio < 15:
        pe_score = 3  # Expensive
    else:
        pe_score = 0  # Very expensive
    
    score += pe_score
    details['pe_valuation'] = f"{pe_score}/10 (P/E: {pe_ratio})"
    
    # Dividend Yield (10 points)
    dividend_yield = fundamentals.get('dividend_yield', 0) or 0
    
    if dividend_yield > 5:
        yield_score = 10
    elif dividend_yield > 4:
        yield_score = 8
    elif dividend_yield > 3:
        yield_score = 6
    elif dividend_yield > 2:
        yield_score = 4
    elif dividend_yield > 1:
        yield_score = 2
    else:
        yield_score = 0
    
    score += yield_score
    details['dividend_yield'] = f"{yield_score}/10 (Yield: {dividend_yield}%)"
    
    # Price-to-Book (5 points)
    pb_ratio = fundamentals.get('pb_ratio', 2) or 2
    
    if pb_ratio < 1.5:
        pb_score = 5  # Undervalued
    elif pb_ratio < 2:
        pb_score = 3  # Fair
    elif pb_ratio < 3:
        pb_score = 1  # Expensive
    else:
        pb_score = 0  # Very expensive
    
    score += pb_score
    details['price_to_book'] = f"{pb_score}/5 (P/B: {pb_ratio})"
    
    return {
        'score': score,
        'max_score': 25,
        'details': details
    }


# ============================================================================
# TECHNICAL MOMENTUM SCORE (20 points)
# ============================================================================

def calculate_technical_score(technical: Dict) -> Dict:
    """
    Calculate technical momentum score (0-20 points)
    
    Uses the get_technical_score_20() function from technical.py
    """
    if not technical:
        return {
            'score': 10,  # Neutral
            'max_score': 20,
            'details': {'status': 'No technical data available'}
        }
    
    # Get 20-point technical score
    score = get_technical_score_20(technical)
    
    details = {
        'trend': technical.get('trend', {}).get('trend', 'unknown'),
        'rsi': technical.get('rsi'),
        'macd_trend': technical.get('macd', {}).get('trend', 'unknown'),
        'signals': technical.get('signals', [])
    }
    
    return {
        'score': score,
        'max_score': 20,
        'details': details
    }


# ============================================================================
# SECTOR & MACRO SCORE (15 points)
# ============================================================================

def calculate_sector_score(symbol: str, sector_data: Dict = None) -> Dict:
    """
    Calculate sector & macro score (0-15 points)
    
    Components:
    - Sector Strength: 7 points
    - Macro Tailwinds: 5 points
    - Geopolitical Risk: 3 points
    """
    score = 0
    details = {}
    
    # Determine sector
    stock_sector = None
    for sector_name, stocks in SECTORS.items():
        if symbol in stocks:
            stock_sector = sector_name
            break
    
    details['sector'] = stock_sector or 'unknown'
    
    # Sector Strength (7 points)
    sector_performance = sector_data.get('change_percent', 0) if sector_data else 0
    
    if sector_performance > 2:
        sector_score = 7  # Strong outperformance
    elif sector_performance > 0.5:
        sector_score = 5  # Neutral to positive
    elif sector_performance > -0.5:
        sector_score = 3  # Neutral
    elif sector_performance > -2:
        sector_score = 2  # Underperforming
    else:
        sector_score = 0  # Sector in crisis
    
    score += sector_score
    details['sector_strength'] = f"{sector_score}/7 ({sector_performance}%)"
    
    # Macro Tailwinds (5 points) - Default to neutral
    global_markets = db.get_latest_global_markets() or {}
    
    us_change = global_markets.get('sp500_change', 0) or 0
    oil_change = global_markets.get('wti_change', 0) or 0
    
    # Check if sector benefits from macro
    if stock_sector == 'oil_gas' and oil_change > 2:
        macro_score = 5
    elif stock_sector == 'banking' and us_change > 1:
        macro_score = 4
    elif us_change > 1:
        macro_score = 4
    elif us_change > -1:
        macro_score = 3
    elif us_change > -2:
        macro_score = 1
    else:
        macro_score = 0
    
    score += macro_score
    details['macro_tailwinds'] = f"{macro_score}/5"
    
    # Geopolitical Risk (3 points) - Default to neutral
    geo_risk = 2  # Default neutral
    score += geo_risk
    details['geopolitical'] = f"{geo_risk}/3"
    
    return {
        'score': score,
        'max_score': 15,
        'details': details
    }


# ============================================================================
# NEWS & CATALYSTS SCORE (5 points)
# ============================================================================

def calculate_news_score(symbol: str) -> Dict:
    """
    Calculate news & catalysts score (0-5 points)
    
    Based on recent announcements and sentiment
    """
    sentiment_data = get_ticker_sentiment(symbol, days=7)
    
    sentiment_score = sentiment_data.get('sentiment_score', 0) or 0
    announcement_count = sentiment_data.get('announcement_count', 0)
    
    # Base score on sentiment
    if sentiment_score > 0.5:
        news_score = 5  # Very positive
    elif sentiment_score > 0.2:
        news_score = 4  # Positive
    elif sentiment_score > -0.2:
        news_score = 3  # Neutral
    elif sentiment_score > -0.5:
        news_score = 1  # Negative
    else:
        news_score = 0  # Very negative
    
    # Boost for recent positive announcements
    if announcement_count > 0 and sentiment_score > 0:
        news_score = min(5, news_score + 1)
    
    details = {
        'sentiment': sentiment_score,
        'announcements': announcement_count,
        'recent_headlines': [h['headline'][:50] for h in sentiment_data.get('latest_headlines', [])[:3]]
    }
    
    return {
        'score': news_score,
        'max_score': 5,
        'details': details
    }


# ============================================================================
# COMPREHENSIVE 100-POINT SCORING
# ============================================================================

def calculate_stock_score(symbol: str) -> Dict:
    """
    Calculate comprehensive 100-point stock score
    
    Returns:
        Dict with total score, component scores, rating, and details
    """
    # Get all data
    technical = analyze_ticker_technical(symbol)
    fundamentals = {}  # Will be enhanced with fundamental data scraping
    
    # Get sector data
    stock_sector = None
    for sector_name, stocks in SECTORS.items():
        if symbol in stocks:
            stock_sector = sector_name
            break
    
    sector_indices = db.get_sector_indices()
    sector_data = next((s for s in sector_indices if s['sector'] == stock_sector), None)
    
    # Calculate component scores
    financial = calculate_financial_score(fundamentals)
    valuation = calculate_valuation_score(fundamentals, 
                                          technical.get('current_price') if technical else None)
    tech_score = calculate_technical_score(technical)
    sector = calculate_sector_score(symbol, sector_data)
    news = calculate_news_score(symbol)
    
    # Calculate total score
    total_score = (
        financial['score'] +
        valuation['score'] +
        tech_score['score'] +
        sector['score'] +
        news['score']
    )
    
    # Determine rating
    if total_score >= 85:
        rating = "STRONG BUY"
    elif total_score >= 70:
        rating = "BUY"
    elif total_score >= 55:
        rating = "HOLD"
    elif total_score >= 40:
        rating = "REDUCE"
    else:
        rating = "SELL/AVOID"
    
    # Save to database
    db.save_stock_score(symbol, {
        'financial': financial['score'],
        'valuation': valuation['score'],
        'technical': tech_score['score'],
        'sector_macro': sector['score'],
        'news': news['score'],
        'details': {
            'financial': financial['details'],
            'valuation': valuation['details'],
            'technical': tech_score['details'],
            'sector': sector['details'],
            'news': news['details']
        }
    })
    
    return {
        'symbol': symbol,
        'total_score': total_score,
        'rating': rating,
        'components': {
            'financial': financial,
            'valuation': valuation,
            'technical': tech_score,
            'sector_macro': sector,
            'news': news
        },
        'timestamp': datetime.now().isoformat()
    }


def score_all_stocks(symbols: List[str], show_progress: bool = True) -> List[Dict]:
    """
    Score all given stocks
    """
    results = []
    
    from tqdm import tqdm
    iterator = tqdm(symbols, desc="Scoring stocks") if show_progress else symbols
    
    for symbol in iterator:
        try:
            score = calculate_stock_score(symbol)
            results.append(score)
        except Exception as e:
            print(f"Error scoring {symbol}: {e}")
    
    # Sort by total score
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    return results


def get_stock_ranking(limit: int = 50) -> List[Dict]:
    """
    Get ranked list of stocks by score
    """
    return db.get_stock_scores(limit=limit)


def print_scorecard(score: Dict):
    """
    Print formatted scorecard for a stock
    """
    print(f"\n{'='*60}")
    print(f"STOCK SCORECARD: {score['symbol']}")
    print(f"{'='*60}")
    print(f"\n📊 TOTAL SCORE: {score['total_score']}/100 → {score['rating']}")
    print(f"\n{'─'*60}")
    
    components = score['components']
    
    print(f"\n💰 Financial Health: {components['financial']['score']}/{components['financial']['max_score']}")
    for key, val in components['financial']['details'].items():
        print(f"   • {key}: {val}")
    
    print(f"\n📈 Valuation: {components['valuation']['score']}/{components['valuation']['max_score']}")
    for key, val in components['valuation']['details'].items():
        print(f"   • {key}: {val}")
    
    print(f"\n📉 Technical: {components['technical']['score']}/{components['technical']['max_score']}")
    tech_details = components['technical']['details']
    print(f"   • Trend: {tech_details.get('trend', 'N/A')}")
    print(f"   • RSI: {tech_details.get('rsi', 'N/A')}")
    print(f"   • MACD: {tech_details.get('macd_trend', 'N/A')}")
    
    print(f"\n🌍 Sector & Macro: {components['sector_macro']['score']}/{components['sector_macro']['max_score']}")
    for key, val in components['sector_macro']['details'].items():
        print(f"   • {key}: {val}")
    
    print(f"\n📰 News & Catalysts: {components['news']['score']}/{components['news']['max_score']}")
    print(f"   • Sentiment: {components['news']['details'].get('sentiment', 'N/A')}")
    print(f"   • Announcements: {components['news']['details'].get('announcements', 0)}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Test scoring system
    test_symbols = ["OGDC", "HBL", "FFC", "MARI", "LUCK"]
    
    print("Testing 100-Point Stock Scoring System...")
    
    for symbol in test_symbols:
        score = calculate_stock_score(symbol)
        print_scorecard(score)
