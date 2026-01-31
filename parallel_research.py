"""
PSX Research Analyst - Parallel Top 100 Expert Research
Runs comprehensive analysis on top 100 companies in parallel
with expert-level insights based on 20+ years experience methodology
"""
import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db
from database.models import get_connection
from config import WATCHLIST
from analysis.technical import analyze_ticker_technical, get_technical_score
from analysis.sentiment import get_ticker_sentiment, interpret_sentiment
from analysis.recommendation import calculate_buy_score, get_recommendation


# Top 100 Blue Chip / Most Traded PSX Companies
TOP_100_COMPANIES = [
    # Oil & Gas (High dividend, stable)
    "OGDC", "PPL", "POL", "MARI", "PSO", "APL", "SNGP", "SSGC",
    # Banking (Interest rate sensitive)
    "HBL", "MCB", "UBL", "NBP", "ABL", "BAFL", "BAHL", "MEBL", "AKBL",
    # Cement (Infrastructure play)
    "LUCK", "DGKC", "MLCF", "FCCL", "KOHC", "CHCC", "PIOC", "ACPL", "FLYNG",
    # Power/Energy
    "HUBC", "KAPCO", "NPL", "PKGP", "KEL", "NCPL",
    # Fertilizer (Agriculture dependent)
    "ENGRO", "FFC", "FFBL", "FATIMA", "EFERT",
    # Textile (Export oriented)
    "NML", "NCL", "GATM", "ILP", "KTML",
    # Pharma (Defensive)
    "GLAXO", "SEARL", "FEROZ", "HINOON", "ABOT",
    # Auto (Consumer discretionary)
    "INDU", "HCAR", "PSMC", "MTL", "GHNL", "ATLH",
    # Technology/Telecom
    "TRG", "SYS", "NETSOL", "AVN", "AIRLINK",
    # Food & FMCG (Consumer staples)
    "NESTLE", "COLG", "UNITY", "FFL", "TREET",
    # Steel/Metals
    "ISL", "ASTL", "MUGHAL",
    # Chemicals
    "ICI", "EPCL", "LOTCHEM",
    # Insurance
    "PKLI", "JSGCL", "EFUG",
    # Other Blue Chips
    "PAEL", "DAWH", "ATRL", "SAZEW", "POWER", "SPL", "PAKT",
    # ETFs (Passive tracking)
    "NBPGETF", "JSMFETF"
]

# Sector classification for comparison
SECTOR_MAP = {
    "Oil & Gas": ["OGDC", "PPL", "POL", "MARI", "PSO", "APL", "SNGP", "SSGC"],
    "Banking": ["HBL", "MCB", "UBL", "NBP", "ABL", "BAFL", "BAHL", "MEBL", "AKBL"],
    "Cement": ["LUCK", "DGKC", "MLCF", "FCCL", "KOHC", "CHCC", "PIOC", "ACPL", "FLYNG"],
    "Power": ["HUBC", "KAPCO", "NPL", "PKGP", "KEL", "NCPL"],
    "Fertilizer": ["ENGRO", "FFC", "FFBL", "FATIMA", "EFERT"],
    "Textile": ["NML", "NCL", "GATM", "ILP", "KTML"],
    "Pharma": ["GLAXO", "SEARL", "FEROZ", "HINOON", "ABOT"],
    "Auto": ["INDU", "HCAR", "PSMC", "MTL", "GHNL", "ATLH"],
    "Tech": ["TRG", "SYS", "NETSOL", "AVN", "AIRLINK"],
    "FMCG": ["NESTLE", "COLG", "UNITY", "FFL", "TREET"],
    "Steel": ["ISL", "ASTL", "MUGHAL"],
    "Chemicals": ["ICI", "EPCL", "LOTCHEM"],
    "ETF": ["NBPGETF", "JSMFETF"]
}


def get_sector(symbol: str) -> str:
    """Get sector for a symbol"""
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    return "Other"


def analyze_single_company(symbol: str) -> Dict:
    """
    Comprehensive analysis of a single company
    Returns detailed analysis dict
    """
    try:
        # Get company info
        ticker_info = db.get_ticker(symbol)
        company_name = ticker_info.get('name', symbol) if ticker_info else symbol
        sector = get_sector(symbol)
        
        # Get technical analysis
        technical = analyze_ticker_technical(symbol)
        
        # Get sentiment analysis
        sentiment = get_ticker_sentiment(symbol, days=14)
        
        # Calculate scores
        buy_score = calculate_buy_score(technical, sentiment)
        recommendation = get_recommendation(buy_score)
        
        # Get price data
        price_history = db.get_price_history(symbol, days=30)
        current_price = price_history[0].get('close_price', 0) if price_history else 0
        current_volume = price_history[0].get('volume', 0) if price_history else 0
        
        # Calculate price changes
        price_change_1d = 0
        price_change_7d = 0
        price_change_30d = 0
        
        if len(price_history) >= 2:
            prev = price_history[1].get('close_price', current_price)
            if prev > 0:
                price_change_1d = ((current_price - prev) / prev) * 100
        
        if len(price_history) >= 7:
            week_ago = price_history[6].get('close_price', current_price)
            if week_ago > 0:
                price_change_7d = ((current_price - week_ago) / week_ago) * 100
        
        if len(price_history) >= 20:
            month_ago = price_history[-1].get('close_price', current_price)
            if month_ago > 0:
                price_change_30d = ((current_price - month_ago) / month_ago) * 100
        
        # Get 52-week data
        high_52w, low_52w = db.get_52_week_high_low(symbol)
        position_52w = 0
        if high_52w and low_52w and high_52w > low_52w:
            position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
        
        # Get recent announcements
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT headline, announcement_type, sentiment_score, announcement_date
            FROM announcements
            WHERE symbol = ?
            ORDER BY announcement_date DESC
            LIMIT 5
        """, (symbol,))
        announcements = cur.fetchall()
        conn.close()
        
        # Analyze announcements for key events
        dividend_news = any('dividend' in (a[0] or '').lower() for a in announcements)
        bonus_news = any('bonus' in (a[0] or '').lower() for a in announcements)
        earnings_news = any(kw in (a[0] or '').lower() for a in announcements 
                          for kw in ['financial result', 'quarterly', 'annual'])
        
        # Generate expert analysis
        expert_analysis = generate_expert_analysis(
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            buy_score=buy_score,
            recommendation=recommendation,
            technical=technical,
            sentiment=sentiment,
            price_change_1d=price_change_1d,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            position_52w=position_52w,
            dividend_news=dividend_news,
            bonus_news=bonus_news,
            earnings_news=earnings_news
        )
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'current_price': round(current_price, 2),
            'volume': current_volume,
            'buy_score': buy_score,
            'recommendation': recommendation,
            'rsi': technical.get('rsi') if technical else None,
            'volume_spike': technical.get('volume_spike', False) if technical else False,
            'sentiment_score': sentiment.get('sentiment_score', 0),
            'sentiment_label': interpret_sentiment(sentiment.get('sentiment_score', 0)),
            'price_change_1d': round(price_change_1d, 2),
            'price_change_7d': round(price_change_7d, 2),
            'price_change_30d': round(price_change_30d, 2),
            'high_52w': high_52w or 0,
            'low_52w': low_52w or 0,
            'position_52w': round(position_52w, 1),
            'dividend_news': dividend_news,
            'bonus_news': bonus_news,
            'earnings_news': earnings_news,
            'announcement_count': len(announcements),
            'expert_analysis': expert_analysis,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'status': 'error',
            'error': str(e),
            'buy_score': 0,
            'recommendation': 'N/A',
            'expert_analysis': f'Analysis failed: {str(e)}'
        }


def generate_expert_analysis(symbol, company_name, sector, buy_score, recommendation,
                            technical, sentiment, price_change_1d, price_change_7d,
                            price_change_30d, position_52w, dividend_news, 
                            bonus_news, earnings_news) -> str:
    """
    Generate expert-level analysis text like a 20+ year experienced analyst
    """
    parts = []
    
    # Opening assessment
    if buy_score >= 8:
        parts.append(f"{symbol} presents a compelling investment opportunity.")
    elif buy_score >= 6:
        parts.append(f"{symbol} shows favorable characteristics for consideration.")
    elif buy_score >= 4:
        parts.append(f"{symbol} requires careful evaluation before commitment.")
    else:
        parts.append(f"{symbol} currently displays concerning signals.")
    
    # Sector context
    parts.append(f"Operating in the {sector} sector,")
    
    # Technical assessment
    rsi = technical.get('rsi') if technical else None
    if rsi:
        if rsi < 30:
            parts.append(f"the stock is deeply oversold with RSI at {rsi:.0f}, suggesting potential mean reversion opportunity.")
        elif rsi < 40:
            parts.append(f"RSI at {rsi:.0f} indicates oversold conditions that historically precede recoveries.")
        elif rsi > 70:
            parts.append(f"caution is warranted as RSI of {rsi:.0f} signals overbought territory.")
        elif rsi > 60:
            parts.append(f"momentum remains strong with RSI at {rsi:.0f}.")
        else:
            parts.append(f"technical indicators are neutral with RSI at {rsi:.0f}.")
    
    # Price momentum
    if price_change_30d > 15:
        parts.append(f"The {price_change_30d:.1f}% monthly gain demonstrates strong market conviction.")
    elif price_change_30d > 5:
        parts.append(f"Recent {price_change_30d:.1f}% monthly appreciation reflects positive sentiment.")
    elif price_change_30d < -15:
        parts.append(f"The {abs(price_change_30d):.1f}% monthly decline warrants investigation into underlying causes.")
    elif price_change_30d < -5:
        parts.append(f"Recent weakness of {abs(price_change_30d):.1f}% may present accumulation opportunity for patient investors.")
    
    # 52-week position valuation context
    if position_52w < 20:
        parts.append("Trading near 52-week lows suggests deep value territory, though catalyst identification is crucial.")
    elif position_52w < 40:
        parts.append("Current levels in lower quartile of 52-week range may offer favorable risk-reward.")
    elif position_52w > 85:
        parts.append("Near 52-week highs, entry timing and position sizing become critical.")
    elif position_52w > 70:
        parts.append("Strong positioning in upper range reflects market confidence.")
    
    # Volume analysis
    if technical and technical.get('volume_spike'):
        parts.append("Elevated volume signals institutional interest or significant news flow.")
    
    # News/Catalyst assessment
    if dividend_news:
        parts.append("Recent dividend announcement provides income component and signals management confidence.")
    if bonus_news:
        parts.append("Bonus share announcement reflects strong retained earnings and shareholder-friendly policy.")
    if earnings_news:
        parts.append("Recent earnings release should be reviewed for growth trajectory insights.")
    
    # Sentiment
    sent_score = sentiment.get('sentiment_score', 0)
    if sent_score > 0.3:
        parts.append("News sentiment is distinctly positive, supporting the bullish case.")
    elif sent_score < -0.3:
        parts.append("Negative news flow creates headwinds that must be monitored.")
    
    # Conclusion
    if buy_score >= 8:
        parts.append(f"VERDICT: {recommendation} - Multiple factors align favorably. Consider initiating or adding to positions.")
    elif buy_score >= 6:
        parts.append(f"VERDICT: {recommendation} - Fundamentals support gradual accumulation on weakness.")
    elif buy_score >= 4:
        parts.append(f"VERDICT: {recommendation} - Wait for better entry or clearer catalyst.")
    else:
        parts.append(f"VERDICT: {recommendation} - Risk management suggests reducing exposure or avoiding.")
    
    return " ".join(parts)


def run_parallel_analysis(max_workers: int = 5) -> List[Dict]:
    """
    Run analysis on all Top 100 companies in parallel
    """
    print("="*70)
    print("TOP 100 PARALLEL EXPERT RESEARCH SYSTEM")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Companies: {len(TOP_100_COMPANIES)}")
    print(f"Parallel Workers: {max_workers}")
    print()
    
    results = []
    failed = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(analyze_single_company, symbol): symbol 
            for symbol in TOP_100_COMPANIES
        }
        
        # Process as completed
        completed = 0
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            completed += 1
            
            try:
                result = future.result()
                results.append(result)
                
                status = "OK" if result.get('status') == 'success' else "ERR"
                score = result.get('buy_score', 0)
                rec = result.get('recommendation', 'N/A')
                
                print(f"[{completed:3d}/{len(TOP_100_COMPANIES)}] {symbol:8s} | {status} | Score: {score}/10 | {rec}")
                
            except Exception as e:
                failed.append({'symbol': symbol, 'error': str(e)})
                print(f"[{completed:3d}/{len(TOP_100_COMPANIES)}] {symbol:8s} | FAILED: {e}")
    
    print()
    print(f"Completed: {len(results)} | Failed: {len(failed)}")
    
    return results


def calculate_sector_metrics(results: List[Dict]) -> pd.DataFrame:
    """
    Calculate sector-level performance metrics
    """
    sector_data = []
    
    for sector, symbols in SECTOR_MAP.items():
        sector_results = [r for r in results if r.get('symbol') in symbols and r.get('status') == 'success']
        
        if not sector_results:
            continue
        
        # Calculate averages
        avg_score = sum(r.get('buy_score', 0) for r in sector_results) / len(sector_results)
        avg_change_7d = sum(r.get('price_change_7d', 0) for r in sector_results) / len(sector_results)
        avg_change_30d = sum(r.get('price_change_30d', 0) for r in sector_results) / len(sector_results)
        avg_rsi = sum(r.get('rsi', 50) or 50 for r in sector_results) / len(sector_results)
        
        # Find top pick
        best = max(sector_results, key=lambda x: x.get('buy_score', 0))
        
        # Count strong buys
        strong_buys = len([r for r in sector_results if r.get('buy_score', 0) >= 8])
        
        sector_data.append({
            'Sector': sector,
            'Companies': len(sector_results),
            'Avg Score': round(avg_score, 1),
            'Strong Buys': strong_buys,
            'Avg 7D %': round(avg_change_7d, 1),
            'Avg 30D %': round(avg_change_30d, 1),
            'Avg RSI': round(avg_rsi, 0),
            'Top Pick': best.get('symbol', ''),
            'Top Score': best.get('buy_score', 0),
            'Sector Outlook': get_sector_outlook(avg_score, avg_change_30d)
        })
    
    return pd.DataFrame(sector_data).sort_values('Avg Score', ascending=False)


def get_sector_outlook(avg_score: float, avg_change_30d: float) -> str:
    """Generate sector outlook text"""
    if avg_score >= 7 and avg_change_30d > 5:
        return "Strong - Outperforming"
    elif avg_score >= 6:
        return "Positive - Favorable"
    elif avg_score >= 5:
        return "Neutral - Market Perform"
    elif avg_score >= 4:
        return "Cautious - Underweight"
    else:
        return "Weak - Avoid"


def export_to_excel(results: List[Dict], sector_df: pd.DataFrame) -> str:
    """
    Export comprehensive analysis to Excel
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        os.path.dirname(__file__),
        "reports",
        f"psx_expert_research_{timestamp}.xlsx"
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("\nGenerating Excel report...")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # Sheet 1: Full Analysis
        full_data = []
        for r in sorted(results, key=lambda x: x.get('buy_score', 0), reverse=True):
            if r.get('status') != 'success':
                continue
            full_data.append({
                'Symbol': r.get('symbol', ''),
                'Company': r.get('company_name', ''),
                'Sector': r.get('sector', ''),
                'Price': r.get('current_price', 0),
                'Buy Score': r.get('buy_score', 0),
                'Recommendation': r.get('recommendation', ''),
                '1D %': r.get('price_change_1d', 0),
                '7D %': r.get('price_change_7d', 0),
                '30D %': r.get('price_change_30d', 0),
                '52W Position %': r.get('position_52w', 0),
                'RSI': r.get('rsi', ''),
                'Volume Spike': 'Yes' if r.get('volume_spike') else '',
                'Sentiment': r.get('sentiment_label', ''),
                'Dividend News': 'Yes' if r.get('dividend_news') else '',
                'Bonus News': 'Yes' if r.get('bonus_news') else '',
                'Expert Analysis': r.get('expert_analysis', '')
            })
        
        df_full = pd.DataFrame(full_data)
        df_full.to_excel(writer, sheet_name='Full Analysis', index=False)
        
        # Sheet 2: Strong Buy (8-10)
        df_strong = df_full[df_full['Buy Score'] >= 8]
        df_strong.to_excel(writer, sheet_name='Strong Buy (8+)', index=False)
        
        # Sheet 3: Buy (5-7)
        df_buy = df_full[(df_full['Buy Score'] >= 5) & (df_full['Buy Score'] < 8)]
        df_buy.to_excel(writer, sheet_name='Buy (5-7)', index=False)
        
        # Sheet 4: Hold/Avoid (1-4)
        df_avoid = df_full[df_full['Buy Score'] < 5]
        df_avoid.to_excel(writer, sheet_name='Hold-Avoid (1-4)', index=False)
        
        # Sheet 5: Sector Comparison
        sector_df.to_excel(writer, sheet_name='Sector Analysis', index=False)
        
        # Sheet 6: Momentum Leaders
        df_momentum = df_full.sort_values('30D %', ascending=False).head(15)
        df_momentum.to_excel(writer, sheet_name='Momentum Leaders', index=False)
        
        # Sheet 7: Value Opportunities
        df_value = df_full[(df_full['52W Position %'] < 30) & (df_full['Buy Score'] >= 5)]
        df_value = df_value.sort_values('Buy Score', ascending=False)
        df_value.to_excel(writer, sheet_name='Value Plays', index=False)
        
        # Sheet 8: Dividend Stocks
        df_div = df_full[df_full['Dividend News'] == 'Yes']
        df_div.to_excel(writer, sheet_name='Dividend News', index=False)
        
        # Sheet 9: Summary
        summary = {
            'Metric': [
                'Report Generated',
                'Total Analyzed',
                'Strong Buy (8+)',
                'Buy (5-7)',
                'Hold/Avoid (<5)',
                'Top Overall Pick',
                'Top Sector',
                'Most Momentum',
                'Best Value Play'
            ],
            'Value': [
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                len(df_full),
                len(df_strong),
                len(df_buy),
                len(df_avoid),
                df_full.iloc[0]['Symbol'] if len(df_full) > 0 else 'N/A',
                sector_df.iloc[0]['Sector'] if len(sector_df) > 0 else 'N/A',
                df_momentum.iloc[0]['Symbol'] if len(df_momentum) > 0 else 'N/A',
                df_value.iloc[0]['Symbol'] if len(df_value) > 0 else 'N/A'
            ]
        }
        pd.DataFrame(summary).to_excel(writer, sheet_name='Summary', index=False)
    
    return output_path


def run_full_research(workers: int = 5):
    """
    Main function to run complete Top 100 research
    """
    start_time = datetime.now()
    
    # Run parallel analysis
    results = run_parallel_analysis(max_workers=workers)
    
    # Calculate sector metrics
    sector_df = calculate_sector_metrics(results)
    
    # Export to Excel
    excel_path = export_to_excel(results, sector_df)
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("="*70)
    print("RESEARCH COMPLETE")
    print("="*70)
    print(f"Duration: {duration:.1f} seconds")
    print(f"Excel Report: {excel_path}")
    print()
    
    # Top 10 picks
    print("TOP 10 EXPERT PICKS:")
    print("-"*70)
    successful = [r for r in results if r.get('status') == 'success']
    for i, r in enumerate(sorted(successful, key=lambda x: x.get('buy_score', 0), reverse=True)[:10], 1):
        print(f"{i:2d}. {r['symbol']:8s} | Score: {r['buy_score']}/10 | {r['recommendation']:12s} | {r['sector']}")
    
    print()
    print("SECTOR RANKINGS:")
    print("-"*70)
    for _, row in sector_df.head(5).iterrows():
        print(f"  {row['Sector']:15s} | Avg: {row['Avg Score']}/10 | Top: {row['Top Pick']} | {row['Sector Outlook']}")
    
    return results, sector_df, excel_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Top 100 Parallel Expert Research')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    args = parser.parse_args()
    
    run_full_research(workers=args.workers)
