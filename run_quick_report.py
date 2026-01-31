"""
Quick Top 100 PSX Companies Report Generator
Generates a report for the top 100 companies with available data
"""
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from database.db_manager import db
from scraper.ticker_discovery import discover_and_save_tickers
from scraper.price_scraper import fetch_all_prices
from analysis.stock_scoring import score_all_stocks
from report.postmarket_template import generate_postmarket_report
from report.email_sender import send_email

# Top 100 KSE-100 companies by market cap (manually curated list)
TOP_100_SYMBOLS = [
    # Banking
    'HBL', 'UBL', 'MCB', 'NBP', 'BAFL', 'MEBL', 'ABL', 'BAHL', 'AKBL', 'BOP',
    # Oil & Gas
    'OGDC', 'PPL', 'POL', 'MARI', 'PSO', 'APL', 'SNGP', 'SSGC', 'HASCOL', 'BYCO',
    # Fertilizer
    'ENGRO', 'FFC', 'FFBL', 'EFERT', 'FATIMA',
    # Cement
    'LUCK', 'DGKC', 'MLCF', 'FCCL', 'PIOC', 'CHCC', 'KOHC', 'ACPL', 'BWCL', 'GWLC',
    # Power
    'HUBC', 'KAPCO', 'PKGP', 'NCPL', 'EPQL', 'KEL', 'HMM', 'KML',
    # Pharma
    'SEARL', 'GLAXO', 'HINOON', 'FEROZ', 'IBLHL', 'AGP', 'GSKCH',
    # Auto
    'INDU', 'HCAR', 'PSMC', 'HONDA', 'MTL', 'ATLH', 'GHANL', 'GHNI',
    # Telecom
    'PTC', 'TRG', 'WTL', 'PTCL',
    # Food
    'NESTLE', 'UPFL', 'FFL', 'QUICE', 'COLG', 'PAEL', 'MUREB', 'SHEL',
    # Textile
    'NML', 'NCL', 'GATM', 'KTML', 'ILP',
    # Technology
    'SYS', 'AVN', 'NETSOL',
    # Others - Major companies
    'MUGHAL', 'ISL', 'AGTL', 'UNITY', 'ASTL', 'ATRL', 'EPCL', 'IBFL', 'JSBL', 'LOTCHEM',
    'POWER', 'PIBTL', 'THALL', 'TGL', 'TOMCL', 'MTL', 'MLCF', 'PAKD', 'PAKT', 'FRCL'
]


def generate_top100_report():
    """Generate quick report for top 100 companies"""
    print("=" * 60)
    print("📊 GENERATING TOP 100 PSX COMPANIES REPORT")
    print("=" * 60)
    
    # 1. Discover tickers
    print("\n[1/4] Checking tickers...")
    discover_and_save_tickers()
    
    # 2. Fetch prices for top 100
    print("[2/4] Fetching prices for top 100...")
    fetch_all_prices(TOP_100_SYMBOLS[:50], show_progress=True)  # First 50 faster
    
    # 3. Score stocks
    print("[3/4] Running 100-point analysis...")
    scores = score_all_stocks(TOP_100_SYMBOLS[:50], show_progress=True)
    
    # Sort by score
    scores_sorted = sorted(scores, key=lambda x: x.get('total_score', 0), reverse=True)
    
    # 4. Generate report
    print("[4/4] Generating report...")
    
    market_summary = {
        'close_value': 0,
        'change_percent': 0,
        'volume': 0,
        'advancing': 0,
        'declining': 0
    }
    
    # Try to get KSE-100 data
    try:
        from scraper.kse100_scraper import get_kse100_summary
        kse100 = get_kse100_summary()
        if kse100:
            market_summary.update(kse100)
    except:
        pass
    
    top_stocks = [
        {
            'symbol': s['symbol'],
            'price': 0,
            'change_percent': 0,
            'score': s['total_score'],
            'rating': s['rating']
        }
        for s in scores_sorted[:20]
    ]
    
    # Print top 20 to console
    print("\n" + "=" * 60)
    print("🏆 TOP 20 STOCKS BY 100-POINT SCORE")
    print("=" * 60)
    print(f"{'Rank':<6}{'Symbol':<10}{'Score':<10}{'Rating':<15}")
    print("-" * 41)
    for i, stock in enumerate(top_stocks[:20], 1):
        print(f"{i:<6}{stock['symbol']:<10}{stock['score']:<10}{stock['rating']:<15}")
    
    # Generate HTML report
    html = generate_postmarket_report(
        market_summary=market_summary,
        top_stocks=top_stocks,
        sector_performance=[],
        technical_analysis={'rsi': 50, 'support': 0, 'resistance': 0, 'trend': 'N/A'},
        news_summary={'total': 0, 'positive': 0, 'negative': 0, 'sentiment': 'N/A', 'top_headlines': []},
        risk_assessment={'market_risk': 'N/A', 'currency_risk': 'N/A', 'global_risk': 'N/A'},
        tomorrow_outlook={'bias': 'neutral', 'range_low': 0, 'range_high': 0, 'confidence': 0, 'narrative': 'Analysis based on available data.'},
        action_items=['Review top scored stocks for investment opportunities']
    )
    
    # Save HTML report locally
    report_path = os.path.join(os.path.dirname(__file__), 'reports', f'top100_report_{datetime.now().strftime("%Y%m%d_%H%M")}.html')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Report saved to: {report_path}")
    
    # Try to send email
    print("\nSending email report...")
    send_email(
        subject=f"📊 PSX Top 100 Analysis - {datetime.now().strftime('%B %d, %Y %I:%M %p')}",
        html_content=html
    )
    
    print("\n✅ Report generation complete!")
    
    return scores_sorted


if __name__ == "__main__":
    generate_top100_report()
