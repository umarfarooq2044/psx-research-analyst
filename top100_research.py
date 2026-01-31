"""
PSX Research Analyst - Top 100 Deep Research Analysis
Detailed analysis of top 100 companies with growth insights, announcements, and sector comparison
"""
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import db
from database.models import get_connection
from config import WATCHLIST, POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
from analysis.sentiment import interpret_sentiment


# Top 100 PSX Companies by market cap/trading activity (curated list)
TOP_100_TICKERS = [
    # Oil & Gas
    "OGDC", "PPL", "POL", "MARI", "PSO", "APL", "SNGP", "SSGC", "HASCOL", "BYCO",
    # Banking
    "HBL", "MCB", "UBL", "NBP", "ABL", "BAFL", "BAHL", "MEBL", "AKBL", "FABL",
    # Cement
    "LUCK", "DGKC", "MLCF", "FCCL", "KOHC", "CHCC", "PIOC", "ACPL", "GWLC", "FLYNG",
    # Power/Energy
    "HUBC", "KAPCO", "NPL", "PKGP", "KEL", "NCPL", "EPQL", "LPGL",
    # Fertilizer
    "ENGRO", "FFC", "FFBL", "FATIMA", "EFERT",
    # Textile
    "NML", "NCL", "GATM", "ILP", "KTML",
    # Pharma
    "GLAXO", "SEARL", "FEROZ", "HINOON", "ABOT",
    # Auto
    "INDU", "HCAR", "PSMC", "MTL", "GHNL", "ATLH",
    # Tech/Telecom
    "TRG", "SYS", "NETSOL", "AVN", "AIRLINK",
    # Food & FMCG
    "NESTLE", "COLG", "UNITY", "FFL", "TREET", "CLOV", "QUICE",
    # Steel
    "ISL", "ASTL", "MUGHAL", "INIL",
    # Chemicals
    "ICI", "EPCL", "LOTCHEM", "BOC",
    # Insurance
    "PKLI", "JSGCL", "EFUG",
    # Investment/Holding
    "PAEL", "JSCL", "PKGS",
    # Others
    "DAWH", "HINO", "AGTL", "GADT", "ATRL", "LOADS", "SAZEW",
    # ETFs
    "NBPGETF", "JSMFETF", "HBLETF",
    # Additional Blue Chips
    "EFERT", "EFUL", "PAKT", "SHEL", "KSBP", "POWER", "SPL"
]


def get_company_deep_analysis(symbol: str) -> dict:
    """
    Perform deep analysis on a single company with detailed insights
    """
    conn = get_connection()
    
    # Get company info
    ticker_info = db.get_ticker(symbol)
    company_name = ticker_info.get('name', symbol) if ticker_info else symbol
    
    # Get latest price and volume data
    price_history = db.get_price_history(symbol, days=30)
    latest_price = price_history[0] if price_history else {}
    
    # Get 52-week high/low
    high_52w, low_52w = db.get_52_week_high_low(symbol)
    
    # Get today's analysis
    today = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT buy_score, recommendation, rsi, volume_spike, sentiment_score, notes
        FROM analysis_results
        WHERE symbol = ? AND date = ?
    """, (symbol, today))
    analysis_row = cursor.fetchone()
    
    # Get recent announcements
    cursor.execute("""
        SELECT headline, announcement_type, sentiment_score, announcement_date, pdf_url
        FROM announcements
        WHERE symbol = ?
        ORDER BY announcement_date DESC
        LIMIT 10
    """, (symbol,))
    announcements = cursor.fetchall()
    
    # Calculate price change
    current_price = latest_price.get('close_price', 0)
    price_change_1d = 0
    price_change_7d = 0
    price_change_30d = 0
    
    if len(price_history) >= 2:
        prev_price = price_history[1].get('close_price', current_price)
        if prev_price > 0:
            price_change_1d = ((current_price - prev_price) / prev_price) * 100
    
    if len(price_history) >= 7:
        week_ago_price = price_history[6].get('close_price', current_price)
        if week_ago_price > 0:
            price_change_7d = ((current_price - week_ago_price) / week_ago_price) * 100
    
    if len(price_history) >= 30:
        month_ago_price = price_history[-1].get('close_price', current_price)
        if month_ago_price > 0:
            price_change_30d = ((current_price - month_ago_price) / month_ago_price) * 100
    
    # Position relative to 52-week range
    position_52w = 0
    if high_52w and low_52w and high_52w > low_52w:
        position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
    
    # Announcement analysis
    announcement_summary = []
    positive_news_count = 0
    negative_news_count = 0
    dividend_announced = False
    bonus_announced = False
    earnings_announced = False
    
    for ann in announcements:
        headline = ann[0] if ann[0] else ""
        ann_type = ann[1] if ann[1] else "general"
        sentiment = ann[2] if ann[2] else 0
        date = ann[3] if ann[3] else ""
        
        # Classify announcement
        headline_lower = headline.lower()
        
        if any(kw in headline_lower for kw in ['dividend', 'cash dividend']):
            dividend_announced = True
        if any(kw in headline_lower for kw in ['bonus', 'bonus share']):
            bonus_announced = True
        if any(kw in headline_lower for kw in ['financial result', 'quarterly', 'annual', 'half year']):
            earnings_announced = True
        
        if sentiment and sentiment > 0.2:
            positive_news_count += 1
        elif sentiment and sentiment < -0.2:
            negative_news_count += 1
        
        announcement_summary.append({
            'headline': headline[:100],
            'type': ann_type,
            'sentiment': interpret_sentiment(sentiment),
            'date': date
        })
    
    # Generate growth outlook based on analysis
    growth_outlook = generate_growth_outlook(
        symbol, company_name, 
        analysis_row, 
        price_change_1d, price_change_7d, price_change_30d,
        position_52w,
        positive_news_count, negative_news_count,
        dividend_announced, bonus_announced, earnings_announced
    )
    
    conn.close()
    
    return {
        'symbol': symbol,
        'company_name': company_name,
        'current_price': current_price,
        'volume': latest_price.get('volume', 0),
        'high_52w': high_52w or 0,
        'low_52w': low_52w or 0,
        'position_52w': round(position_52w, 1),
        'price_change_1d': round(price_change_1d, 2),
        'price_change_7d': round(price_change_7d, 2),
        'price_change_30d': round(price_change_30d, 2),
        'buy_score': analysis_row[0] if analysis_row else 5,
        'recommendation': analysis_row[1] if analysis_row else 'HOLD',
        'rsi': analysis_row[2] if analysis_row else None,
        'volume_spike': 'Yes' if analysis_row and analysis_row[3] else 'No',
        'sentiment_score': analysis_row[4] if analysis_row else 0,
        'analysis_notes': analysis_row[5] if analysis_row else '',
        'announcements': announcement_summary[:5],
        'dividend_announced': dividend_announced,
        'bonus_announced': bonus_announced,
        'earnings_announced': earnings_announced,
        'positive_news': positive_news_count,
        'negative_news': negative_news_count,
        'growth_outlook': growth_outlook
    }


def generate_growth_outlook(symbol, name, analysis, 
                            change_1d, change_7d, change_30d,
                            position_52w, positive_news, negative_news,
                            dividend, bonus, earnings) -> str:
    """
    Generate detailed growth outlook text based on analysis
    """
    outlook_parts = []
    
    # Price momentum analysis
    if change_30d > 10:
        outlook_parts.append(f"Strong upward momentum with {change_30d:.1f}% gain over 30 days.")
    elif change_30d > 0:
        outlook_parts.append(f"Positive trend with {change_30d:.1f}% monthly gain.")
    elif change_30d < -10:
        outlook_parts.append(f"Under pressure with {change_30d:.1f}% decline over 30 days.")
    elif change_30d < 0:
        outlook_parts.append(f"Slight weakness with {change_30d:.1f}% monthly decline.")
    
    # 52-week position
    if position_52w > 90:
        outlook_parts.append("Trading near 52-week highs - momentum play but watch for pullback.")
    elif position_52w > 70:
        outlook_parts.append("Strong position in upper range of 52-week band.")
    elif position_52w < 20:
        outlook_parts.append("Near 52-week lows - potential value opportunity or further weakness.")
    elif position_52w < 40:
        outlook_parts.append("Trading in lower range - may offer accumulation opportunity.")
    
    # Technical indicators
    rsi = analysis[2] if analysis else None
    if rsi:
        if rsi < 30:
            outlook_parts.append(f"RSI at {rsi:.0f} indicates deeply oversold - potential bounce ahead.")
        elif rsi < 40:
            outlook_parts.append(f"RSI at {rsi:.0f} shows oversold conditions.")
        elif rsi > 70:
            outlook_parts.append(f"RSI at {rsi:.0f} signals overbought - caution advised.")
        elif rsi > 60:
            outlook_parts.append(f"RSI at {rsi:.0f} shows healthy momentum.")
    
    # News sentiment
    if positive_news > negative_news and positive_news > 0:
        outlook_parts.append(f"Positive news flow ({positive_news} favorable announcements).")
    elif negative_news > positive_news and negative_news > 0:
        outlook_parts.append(f"Negative sentiment concerns ({negative_news} adverse announcements).")
    
    # Corporate actions
    if dividend:
        outlook_parts.append("Recent dividend announcement - income opportunity.")
    if bonus:
        outlook_parts.append("Bonus shares announced - management confident in growth.")
    if earnings:
        outlook_parts.append("Recent earnings release - check for surprises.")
    
    # Buy score interpretation
    buy_score = analysis[0] if analysis else 5
    if buy_score >= 8:
        outlook_parts.append("OUTLOOK: Strong Buy - Multiple positive signals align.")
    elif buy_score >= 6:
        outlook_parts.append("OUTLOOK: Favorable for accumulation on dips.")
    elif buy_score >= 4:
        outlook_parts.append("OUTLOOK: Hold - Wait for clearer signals.")
    else:
        outlook_parts.append("OUTLOOK: Caution - Consider reducing exposure.")
    
    return " ".join(outlook_parts) if outlook_parts else "Insufficient data for detailed outlook."


def export_top100_analysis():
    """
    Export detailed Top 100 analysis to Excel
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        os.path.dirname(__file__),
        "reports",
        f"psx_top100_research_{timestamp}.xlsx"
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("="*60)
    print("TOP 100 DEEP RESEARCH ANALYSIS")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analyzing {len(TOP_100_TICKERS)} companies...")
    print()
    
    # Analyze all Top 100 companies
    results = []
    for i, symbol in enumerate(TOP_100_TICKERS, 1):
        try:
            print(f"  [{i:3d}/{len(TOP_100_TICKERS)}] {symbol}...", end=" ")
            analysis = get_company_deep_analysis(symbol)
            results.append(analysis)
            print(f"Score: {analysis['buy_score']}/10 | {analysis['recommendation']}")
        except Exception as e:
            print(f"Error: {e}")
    
    print()
    print("Generating Excel report...")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # ========== SHEET 1: Executive Summary ==========
        summary_data = []
        for r in sorted(results, key=lambda x: x['buy_score'], reverse=True):
            summary_data.append({
                'Symbol': r['symbol'],
                'Company': r['company_name'],
                'Price': r['current_price'],
                'Buy Score': r['buy_score'],
                'Recommendation': r['recommendation'],
                '1D Change %': r['price_change_1d'],
                '7D Change %': r['price_change_7d'],
                '30D Change %': r['price_change_30d'],
                '52W Position %': r['position_52w'],
                'RSI': r['rsi'],
                'Volume Spike': r['volume_spike'],
                'Sentiment': r['sentiment_score'],
                'Dividend': 'Yes' if r['dividend_announced'] else '',
                'Bonus': 'Yes' if r['bonus_announced'] else '',
                'Growth Outlook': r['growth_outlook']
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # ========== SHEET 2: Strong Buy (8-10) ==========
        df_strong = df_summary[df_summary['Buy Score'] >= 8]
        df_strong.to_excel(writer, sheet_name='Strong Buy (8-10)', index=False)
        
        # ========== SHEET 3: Buy Recommendations (5-7) ==========
        df_buy = df_summary[(df_summary['Buy Score'] >= 5) & (df_summary['Buy Score'] < 8)]
        df_buy.to_excel(writer, sheet_name='Buy (5-7)', index=False)
        
        # ========== SHEET 4: Hold/Avoid (1-4) ==========
        df_hold = df_summary[df_summary['Buy Score'] < 5]
        df_hold.to_excel(writer, sheet_name='Hold-Avoid (1-4)', index=False)
        
        # ========== SHEET 5: Momentum Leaders ==========
        df_momentum = df_summary.sort_values('30D Change %', ascending=False).head(20)
        df_momentum.to_excel(writer, sheet_name='Momentum Leaders', index=False)
        
        # ========== SHEET 6: Value Opportunities ==========
        df_value = df_summary[df_summary['52W Position %'] < 30].sort_values('Buy Score', ascending=False)
        df_value.to_excel(writer, sheet_name='Value Opportunities', index=False)
        
        # ========== SHEET 7: Dividend Stocks ==========
        df_dividend = df_summary[df_summary['Dividend'] == 'Yes']
        df_dividend.to_excel(writer, sheet_name='Dividend Stocks', index=False)
        
        # ========== SHEET 8: Detailed Announcements ==========
        ann_data = []
        for r in results:
            for ann in r.get('announcements', []):
                ann_data.append({
                    'Symbol': r['symbol'],
                    'Company': r['company_name'],
                    'Date': ann['date'],
                    'Headline': ann['headline'],
                    'Type': ann['type'],
                    'Sentiment': ann['sentiment']
                })
        
        df_announcements = pd.DataFrame(ann_data)
        df_announcements.to_excel(writer, sheet_name='Announcements', index=False)
        
        # ========== SHEET 9: Sector Analysis ==========
        sector_mapping = {
            'Oil & Gas': ['OGDC', 'PPL', 'POL', 'MARI', 'PSO', 'APL', 'SNGP', 'SSGC', 'HASCOL', 'BYCO'],
            'Banking': ['HBL', 'MCB', 'UBL', 'NBP', 'ABL', 'BAFL', 'BAHL', 'MEBL', 'AKBL', 'FABL'],
            'Cement': ['LUCK', 'DGKC', 'MLCF', 'FCCL', 'KOHC', 'CHCC', 'PIOC', 'ACPL', 'GWLC', 'FLYNG'],
            'Power/Energy': ['HUBC', 'KAPCO', 'NPL', 'PKGP', 'KEL', 'NCPL', 'EPQL', 'LPGL'],
            'Fertilizer': ['ENGRO', 'FFC', 'FFBL', 'FATIMA', 'EFERT'],
            'Pharma': ['GLAXO', 'SEARL', 'FEROZ', 'HINOON', 'ABOT'],
            'Auto': ['INDU', 'HCAR', 'PSMC', 'MTL', 'GHNL', 'ATLH'],
            'Tech/Telecom': ['TRG', 'SYS', 'NETSOL', 'AVN', 'AIRLINK'],
            'FMCG/Food': ['NESTLE', 'COLG', 'UNITY', 'FFL', 'TREET']
        }
        
        sector_data = []
        for sector, tickers in sector_mapping.items():
            sector_results = [r for r in results if r['symbol'] in tickers]
            if sector_results:
                avg_score = sum(r['buy_score'] for r in sector_results) / len(sector_results)
                avg_change = sum(r['price_change_30d'] for r in sector_results) / len(sector_results)
                best = max(sector_results, key=lambda x: x['buy_score'])
                
                sector_data.append({
                    'Sector': sector,
                    'Avg Buy Score': round(avg_score, 1),
                    'Avg 30D Change %': round(avg_change, 1),
                    'Top Pick': best['symbol'],
                    'Top Pick Score': best['buy_score'],
                    'Companies Analyzed': len(sector_results)
                })
        
        df_sector = pd.DataFrame(sector_data)
        df_sector = df_sector.sort_values('Avg Buy Score', ascending=False)
        df_sector.to_excel(writer, sheet_name='Sector Analysis', index=False)
        
        # ========== SHEET 10: Report Summary ==========
        report_data = {
            'Metric': [
                'Report Generated',
                'Companies Analyzed',
                'Strong Buy (8-10)',
                'Buy (5-7)',
                'Hold/Avoid (1-4)',
                'Avg Buy Score',
                'Companies with Dividend News',
                'Companies with Bonus News',
                'Top Sector',
                'Top Pick Overall'
            ],
            'Value': [
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                len(results),
                len(df_strong),
                len(df_buy),
                len(df_hold),
                round(sum(r['buy_score'] for r in results) / len(results), 1),
                len(df_dividend),
                len(df_summary[df_summary['Bonus'] == 'Yes']),
                df_sector.iloc[0]['Sector'] if len(df_sector) > 0 else 'N/A',
                df_summary.iloc[0]['Symbol'] if len(df_summary) > 0 else 'N/A'
            ]
        }
        
        df_report = pd.DataFrame(report_data)
        df_report.to_excel(writer, sheet_name='Report Summary', index=False)
    
    print(f"\n[OK] Top 100 Research saved to: {output_path}")
    print()
    print("="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    
    # Print top 10
    print("\nTOP 10 PICKS:")
    for i, r in enumerate(sorted(results, key=lambda x: x['buy_score'], reverse=True)[:10], 1):
        print(f"  {i:2d}. {r['symbol']:8s} | Score: {r['buy_score']}/10 | {r['recommendation']:12s} | {r['company_name'][:30]}")
    
    return output_path


if __name__ == "__main__":
    export_top100_analysis()
