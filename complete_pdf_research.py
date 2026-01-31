"""
PSX Research Analyst - Complete PDF Research System
Downloads and reads ALL PDF reports for comprehensive analysis
Rating: 20-point scale

Components:
- Technical Score: 0-5 points
- Sentiment Score: 0-5 points
- Financial Metrics (from PDF): 0-5 points
- News/Catalyst Score: 0-5 points
Total: 20 points
"""
import os
import sys
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import pandas as pd
import requests
from io import BytesIO
from PyPDF2 import PdfReader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db
from database.models import get_connection
from config import REQUEST_TIMEOUT, PSX_BASE_URL
from analysis.technical import analyze_ticker_technical
from analysis.sentiment import get_ticker_sentiment, interpret_sentiment


# Top 100 Companies
TOP_100 = [
    "OGDC", "PPL", "POL", "MARI", "PSO", "APL", "SNGP", "SSGC",
    "HBL", "MCB", "UBL", "NBP", "ABL", "BAFL", "BAHL", "MEBL", "AKBL",
    "LUCK", "DGKC", "MLCF", "FCCL", "KOHC", "CHCC", "PIOC", "ACPL", "FLYNG",
    "HUBC", "KAPCO", "NPL", "PKGP", "KEL", "NCPL",
    "ENGRO", "FFC", "FFBL", "FATIMA", "EFERT",
    "NML", "NCL", "GATM", "ILP", "KTML",
    "GLAXO", "SEARL", "FEROZ", "HINOON", "ABOT",
    "INDU", "HCAR", "PSMC", "MTL", "GHNL", "ATLH",
    "TRG", "SYS", "NETSOL", "AVN", "AIRLINK",
    "NESTLE", "COLG", "UNITY", "FFL", "TREET",
    "ISL", "ASTL", "MUGHAL",
    "ICI", "EPCL", "LOTCHEM",
    "PKLI", "JSGCL", "EFUG",
    "PAEL", "DAWH", "ATRL", "SAZEW", "POWER", "SPL", "PAKT",
    "NBPGETF", "JSMFETF"
]

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
    for sector, symbols in SECTOR_MAP.items():
        if symbol in symbols:
            return sector
    return "Other"


def read_pdf_from_url(url: str) -> str:
    """
    Read PDF directly from URL without saving to disk
    Returns extracted text using PyPDF2
    """
    try:
        if not url.startswith('http'):
            url = PSX_BASE_URL + url
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Read PDF from memory using PyPDF2
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        # Read text from pages (limit to first 5 pages)
        text = ""
        for page in reader.pages[:5]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text
        
    except Exception as e:
        return ""


def extract_financial_metrics(text: str) -> Dict:
    """
    Extract key financial metrics from PDF text
    """
    metrics = {
        'revenue': None,
        'revenue_growth': None,
        'profit': None,
        'profit_growth': None,
        'eps': None,
        'eps_growth': None,
        'dividend': None,
        'roe': None,
        'net_margin': None,
        'has_data': False
    }
    
    if not text or len(text) < 100:
        return metrics
    
    text_lower = text.lower()
    
    # Extract EPS
    eps_patterns = [
        r'(?:earnings per share|eps|basic eps)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'eps[:\s]+\(?([\d,\.]+)\)?',
    ]
    for pattern in eps_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                metrics['eps'] = float(match.group(1).replace(',', ''))
                metrics['has_data'] = True
            except:
                pass
            break
    
    # Extract Profit
    profit_patterns = [
        r'(?:net profit|profit after tax|pat)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'profit for the (?:year|period|quarter)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
    ]
    for pattern in profit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                metrics['profit'] = float(match.group(1).replace(',', ''))
                metrics['has_data'] = True
            except:
                pass
            break
    
    # Extract Revenue
    rev_patterns = [
        r'(?:revenue|net sales|turnover)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'total (?:revenue|sales)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
    ]
    for pattern in rev_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                metrics['revenue'] = float(match.group(1).replace(',', ''))
                metrics['has_data'] = True
            except:
                pass
            break
    
    # Extract Growth percentages
    growth_patterns = [
        (r'(?:profit|pat).*(?:increase|grew|growth).*?(\d+\.?\d*)%', 'profit_growth'),
        (r'(?:revenue|sales).*(?:increase|grew|growth).*?(\d+\.?\d*)%', 'revenue_growth'),
        (r'eps.*(?:increase|grew|growth).*?(\d+\.?\d*)%', 'eps_growth'),
        (r'(\d+\.?\d*)%.*(?:increase|growth).*(?:profit|pat)', 'profit_growth'),
    ]
    for pattern, key in growth_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                metrics[key] = float(match.group(1))
                metrics['has_data'] = True
            except:
                pass
    
    # Extract Dividend
    div_patterns = [
        r'(?:cash dividend|dividend)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'(?:final|interim)?\s*dividend[:\s]+(\d+)%',
    ]
    for pattern in div_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                metrics['dividend'] = float(match.group(1).replace(',', ''))
                metrics['has_data'] = True
            except:
                pass
            break
    
    # Extract ROE
    roe_match = re.search(r'(?:roe|return on equity)[:\s]+(\d+\.?\d*)%?', text_lower)
    if roe_match:
        try:
            metrics['roe'] = float(roe_match.group(1))
            metrics['has_data'] = True
        except:
            pass
    
    return metrics


def get_company_pdf_urls(symbol: str, limit: int = 3) -> List[str]:
    """
    Get PDF URLs for financial reports
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pdf_url FROM announcements
        WHERE symbol = ? 
        AND pdf_url IS NOT NULL AND pdf_url != ''
        AND (headline LIKE '%Financial%' OR headline LIKE '%Quarterly%' 
             OR headline LIKE '%Annual%' OR headline LIKE '%Result%')
        ORDER BY announcement_date DESC
        LIMIT ?
    """, (symbol, limit))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]


def calculate_financial_score(metrics: Dict) -> int:
    """
    Calculate financial score from PDF metrics (0-5 points)
    """
    score = 0
    
    if not metrics.get('has_data'):
        return 2  # Neutral if no data
    
    # EPS present and positive
    if metrics.get('eps') and metrics['eps'] > 0:
        score += 1
    
    # Profit growth
    if metrics.get('profit_growth'):
        if metrics['profit_growth'] > 20:
            score += 2
        elif metrics['profit_growth'] > 0:
            score += 1
    
    # Dividend
    if metrics.get('dividend') and metrics['dividend'] > 0:
        score += 1
    
    # ROE
    if metrics.get('roe'):
        if metrics['roe'] > 15:
            score += 1
        elif metrics['roe'] < 5:
            score -= 1
    
    return max(0, min(5, score + 2))  # Base of 2, range 0-5


def calculate_news_score(announcements: List, sentiment_data: Dict) -> int:
    """
    Calculate news/catalyst score (0-5 points)
    """
    score = 2  # Base neutral
    
    # Check for positive catalysts
    dividend_news = False
    bonus_news = False
    earnings_news = False
    
    for ann in announcements:
        headline = (ann[0] or '').lower()
        if 'dividend' in headline:
            dividend_news = True
        if 'bonus' in headline:
            bonus_news = True
        if any(kw in headline for kw in ['financial result', 'quarterly', 'annual']):
            earnings_news = True
    
    if dividend_news:
        score += 1
    if bonus_news:
        score += 1
    if earnings_news:
        score += 0.5
    
    # Sentiment adjustment
    sent_score = sentiment_data.get('sentiment_score', 0)
    if sent_score > 0.3:
        score += 1
    elif sent_score < -0.3:
        score -= 1
    
    return max(0, min(5, int(score)))


def analyze_company_with_pdf(symbol: str) -> Dict:
    """
    Complete analysis of a company including PDF reading
    """
    try:
        # Get basic info
        ticker_info = db.get_ticker(symbol)
        company_name = ticker_info.get('name', symbol) if ticker_info else symbol
        sector = get_sector(symbol)
        
        # Technical analysis (0-5 points)
        technical = analyze_ticker_technical(symbol)
        tech_score = 3  # Default
        if technical:
            rsi = technical.get('rsi')
            if rsi:
                if rsi < 30:
                    tech_score = 5
                elif rsi < 40:
                    tech_score = 4
                elif rsi > 70:
                    tech_score = 1
                elif rsi > 60:
                    tech_score = 2
                else:
                    tech_score = 3
            
            if technical.get('volume_spike'):
                tech_score = min(5, tech_score + 1)
        
        # Sentiment analysis (0-5 points)
        sentiment = get_ticker_sentiment(symbol, days=14)
        sent_value = sentiment.get('sentiment_score', 0)
        if sent_value > 0.5:
            sent_score = 5
        elif sent_value > 0.2:
            sent_score = 4
        elif sent_value > -0.2:
            sent_score = 3
        elif sent_value > -0.5:
            sent_score = 2
        else:
            sent_score = 1
        
        # Read PDF reports
        pdf_urls = get_company_pdf_urls(symbol, limit=2)
        pdf_text = ""
        pdfs_read = 0
        
        for url in pdf_urls:
            text = read_pdf_from_url(url)
            if text:
                pdf_text += text + "\n"
                pdfs_read += 1
        
        # Extract financial metrics
        fin_metrics = extract_financial_metrics(pdf_text)
        fin_score = calculate_financial_score(fin_metrics)
        
        # Get announcements for news score
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT headline, announcement_type, sentiment_score
            FROM announcements WHERE symbol = ?
            ORDER BY announcement_date DESC LIMIT 10
        """, (symbol,))
        announcements = cur.fetchall()
        conn.close()
        
        news_score = calculate_news_score(announcements, sentiment)
        
        # TOTAL SCORE (out of 20)
        total_score = tech_score + sent_score + fin_score + news_score
        
        # Get recommendation
        if total_score >= 16:
            recommendation = "STRONG BUY"
        elif total_score >= 13:
            recommendation = "BUY"
        elif total_score >= 10:
            recommendation = "HOLD"
        elif total_score >= 7:
            recommendation = "REDUCE"
        else:
            recommendation = "SELL"
        
        # Price data
        price_history = db.get_price_history(symbol, days=30)
        current_price = price_history[0].get('close_price', 0) if price_history else 0
        
        # Price changes
        price_change_30d = 0
        if len(price_history) >= 20:
            month_ago = price_history[-1].get('close_price', current_price)
            if month_ago > 0:
                price_change_30d = ((current_price - month_ago) / month_ago) * 100
        
        # 52-week position
        high_52w, low_52w = db.get_52_week_high_low(symbol)
        position_52w = 0
        if high_52w and low_52w and high_52w > low_52w:
            position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
        
        # Generate expert analysis
        analysis_text = generate_expert_text(
            symbol, company_name, sector, total_score, recommendation,
            tech_score, sent_score, fin_score, news_score,
            technical, fin_metrics, price_change_30d, position_52w
        )
        
        return {
            'symbol': symbol,
            'company_name': company_name,
            'sector': sector,
            'current_price': round(current_price, 2),
            'total_score': total_score,
            'max_score': 20,
            'recommendation': recommendation,
            'tech_score': tech_score,
            'sentiment_score': sent_score,
            'financial_score': fin_score,
            'news_score': news_score,
            'rsi': technical.get('rsi') if technical else None,
            'volume_spike': technical.get('volume_spike', False) if technical else False,
            'price_change_30d': round(price_change_30d, 2),
            'position_52w': round(position_52w, 1),
            'eps': fin_metrics.get('eps'),
            'profit_growth': fin_metrics.get('profit_growth'),
            'revenue': fin_metrics.get('revenue'),
            'dividend': fin_metrics.get('dividend'),
            'roe': fin_metrics.get('roe'),
            'pdfs_read': pdfs_read,
            'expert_analysis': analysis_text,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'status': 'error',
            'error': str(e),
            'total_score': 0,
            'recommendation': 'N/A'
        }


def generate_expert_text(symbol, name, sector, total, rec, 
                        tech, sent, fin, news,
                        technical, metrics, change_30d, pos_52w) -> str:
    """Generate expert analysis text"""
    parts = []
    
    # Rating context
    parts.append(f"{symbol} ({name}) rates {total}/20 with {rec} recommendation.")
    
    # Score breakdown
    parts.append(f"Scores: Technical {tech}/5, Sentiment {sent}/5, Financial {fin}/5, News {news}/5.")
    
    # Technical insights
    rsi = technical.get('rsi') if technical else None
    if rsi:
        if rsi < 35:
            parts.append(f"Technically oversold (RSI {rsi:.0f}) - potential rebound opportunity.")
        elif rsi > 65:
            parts.append(f"Technically overbought (RSI {rsi:.0f}) - may see consolidation.")
    
    # Financial insights from PDF
    if metrics.get('profit_growth') and metrics['profit_growth'] > 15:
        parts.append(f"Strong profit growth of {metrics['profit_growth']:.0f}% shows execution strength.")
    
    if metrics.get('eps'):
        parts.append(f"EPS of Rs.{metrics['eps']:.2f} reported.")
    
    if metrics.get('dividend'):
        parts.append(f"Dividend of Rs.{metrics['dividend']:.2f} provides income component.")
    
    if metrics.get('roe') and metrics['roe'] > 15:
        parts.append(f"ROE of {metrics['roe']:.0f}% indicates efficient capital utilization.")
    
    # Price position
    if pos_52w < 25:
        parts.append("Trading near 52-week lows - deep value territory.")
    elif pos_52w > 80:
        parts.append("Near 52-week highs - momentum intact but entry timing matters.")
    
    # Momentum
    if change_30d > 10:
        parts.append(f"Strong momentum with {change_30d:.1f}% monthly gain.")
    elif change_30d < -10:
        parts.append(f"Weakness observed with {abs(change_30d):.1f}% monthly decline.")
    
    # Sector context
    parts.append(f"Sector: {sector}.")
    
    return " ".join(parts)


def run_complete_research(workers: int = 3):
    """
    Run complete research with PDF reading
    """
    print("="*70)
    print("COMPLETE PDF RESEARCH SYSTEM - RATING OUT OF 20")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Companies: {len(TOP_100)}")
    print(f"Workers: {workers}")
    print()
    print("Reading PDF reports and analyzing all companies...")
    print()
    
    results = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(analyze_company_with_pdf, s): s for s in TOP_100}
        
        for i, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                if result.get('status') == 'success':
                    score = result.get('total_score', 0)
                    rec = result.get('recommendation', 'N/A')
                    pdfs = result.get('pdfs_read', 0)
                    print(f"[{i:3d}/{len(TOP_100)}] {symbol:8s} | {score:2d}/20 | {rec:12s} | PDFs: {pdfs}")
                else:
                    print(f"[{i:3d}/{len(TOP_100)}] {symbol:8s} | ERROR: {result.get('error', 'Unknown')[:30]}")
            except Exception as e:
                print(f"[{i:3d}/{len(TOP_100)}] {symbol:8s} | FAILED: {e}")
    
    # Export to Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        os.path.dirname(__file__), "reports",
        f"psx_complete_research_{timestamp}.xlsx"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("\nGenerating Excel report...")
    
    # Create DataFrames
    success_results = [r for r in results if r.get('status') == 'success']
    success_results.sort(key=lambda x: x.get('total_score', 0), reverse=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Full Analysis
        data = []
        for r in success_results:
            data.append({
                'Symbol': r['symbol'],
                'Company': r['company_name'],
                'Sector': r['sector'],
                'Price': r['current_price'],
                'TOTAL SCORE': r['total_score'],
                'Out Of': 20,
                'Recommendation': r['recommendation'],
                'Technical': r['tech_score'],
                'Sentiment': r['sentiment_score'],
                'Financial': r['financial_score'],
                'News': r['news_score'],
                'RSI': r.get('rsi', ''),
                '30D Change %': r['price_change_30d'],
                '52W Position %': r['position_52w'],
                'EPS': r.get('eps', ''),
                'Profit Growth %': r.get('profit_growth', ''),
                'Dividend': r.get('dividend', ''),
                'ROE %': r.get('roe', ''),
                'PDFs Read': r['pdfs_read'],
                'Expert Analysis': r['expert_analysis']
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Complete Analysis', index=False)
        
        # Strong Buy
        df_strong = df[df['TOTAL SCORE'] >= 16]
        df_strong.to_excel(writer, sheet_name='Strong Buy (16+)', index=False)
        
        # Buy
        df_buy = df[(df['TOTAL SCORE'] >= 13) & (df['TOTAL SCORE'] < 16)]
        df_buy.to_excel(writer, sheet_name='Buy (13-15)', index=False)
        
        # Hold
        df_hold = df[(df['TOTAL SCORE'] >= 10) & (df['TOTAL SCORE'] < 13)]
        df_hold.to_excel(writer, sheet_name='Hold (10-12)', index=False)
        
        # Reduce/Sell
        df_avoid = df[df['TOTAL SCORE'] < 10]
        df_avoid.to_excel(writer, sheet_name='Reduce-Sell (below 10)', index=False)
        
        # Sector Analysis
        sector_data = []
        for sector in set(r['sector'] for r in success_results):
            s_results = [r for r in success_results if r['sector'] == sector]
            if s_results:
                avg = sum(r['total_score'] for r in s_results) / len(s_results)
                best = max(s_results, key=lambda x: x['total_score'])
                sector_data.append({
                    'Sector': sector,
                    'Avg Score': round(avg, 1),
                    'Companies': len(s_results),
                    'Top Pick': best['symbol'],
                    'Top Score': best['total_score']
                })
        
        df_sector = pd.DataFrame(sector_data).sort_values('Avg Score', ascending=False)
        df_sector.to_excel(writer, sheet_name='Sector Ranking', index=False)
    
    print(f"\n[OK] Report saved: {output_path}")
    print()
    print("="*70)
    print("TOP 10 PICKS (OUT OF 20)")
    print("="*70)
    for i, r in enumerate(success_results[:10], 1):
        print(f"{i:2d}. {r['symbol']:8s} | {r['total_score']:2d}/20 | {r['recommendation']:12s} | PDFs: {r['pdfs_read']}")
    
    return output_path


if __name__ == "__main__":
    run_complete_research(workers=3)
