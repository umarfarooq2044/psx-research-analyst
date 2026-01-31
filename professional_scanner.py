"""
PSX Research Analyst - Comprehensive Professional Market Scanner
Fetches real news, financial data, and generates professional reports
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from tqdm import tqdm

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db, get_connection
from analysis.sentiment import analyze_sentiment

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


# ==============================================================================
# NEWS SCRAPING - Real Pakistani Financial News
# ==============================================================================

def scrape_dawn_business():
    """Scrape business news from DAWN"""
    print("  Scraping DAWN Business...")
    news = []
    
    try:
        url = "https://www.dawn.com/business"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news articles
        articles = soup.find_all('article', limit=20)
        
        for article in articles:
            try:
                headline_tag = article.find('h2') or article.find('h3')
                if not headline_tag:
                    continue
                    
                headline = headline_tag.get_text(strip=True)
                link = headline_tag.find('a')
                url = link['href'] if link and 'href' in link.attrs else ''
                
                if headline:
                    # Analyze sentiment
                    sentiment_score = analyze_sentiment(headline)
                    
                    news.append({
                        'headline': headline,
                        'source': 'DAWN',
                        'url': url if url.startswith('http') else f"https://www.dawn.com{url}",
                        'sentiment': sentiment_score,
                        'scraped_at': datetime.now().isoformat()
                    })
            except:
                continue
        
        print(f"    Found {len(news)} articles from DAWN")
    except Exception as e:
        print(f"    Error scraping DAWN: {e}")
    
    return news


def scrape_business_recorder():
    """Scrape news from Business Recorder"""
    print("  Scraping Business Recorder...")
    news = []
    
    try:
        url = "https://www.brecorder.com/markets"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find articles
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('story' in x.lower() or 'news' in x.lower()), limit=20)
        
        for article in articles:
            try:
                headline_tag = article.find(['h2', 'h3', 'h4', 'a'])
                if not headline_tag:
                    continue
                    
                headline = headline_tag.get_text(strip=True)
                if len(headline) < 20:  # Skip very short strings
                    continue
                    
                link = article.find('a')
                url = link['href'] if link and 'href' in link.attrs else ''
                
                sentiment_score = analyze_sentiment(headline)
                
                news.append({
                    'headline': headline,
                    'source': 'Business Recorder',
                    'url': url if url.startswith('http') else f"https://www.brecorder.com{url}",
                    'sentiment': sentiment_score,
                    'scraped_at': datetime.now().isoformat()
                })
            except:
                continue
        
        print(f"    Found {len(news)} articles from BR")
    except Exception as e:
        print(f"    Error scraping BR: {e}")
    
    return news


def scrape_express_tribune():
    """Scrape business news from Express Tribune"""
    print("  Scraping Express Tribune...")
    news = []
    
    try:
        url = "https://tribune.com.pk/business"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = soup.find_all(['h2', 'h3'], limit=20)
        
        for article in articles:
            try:
                headline = article.get_text(strip=True)
                if len(headline) < 20:
                    continue
                
                link = article.find('a') or article.find_parent('a')
                url = ''
                if link and 'href' in link.attrs:
                    url = link['href']
                
                sentiment_score = analyze_sentiment(headline)
                
                news.append({
                    'headline': headline,
                    'source': 'Express Tribune',
                    'url': url if url.startswith('http') else f"https://tribune.com.pk{url}",
                    'sentiment': sentiment_score,
                    'scraped_at': datetime.now().isoformat()
                })
            except:
                continue
        
        print(f"    Found {len(news)} articles from Tribune")
    except Exception as e:
        print(f"    Error scraping Tribune: {e}")
    
    return news


def scrape_psx_notices():
    """Scrape official PSX notices and announcements"""
    print("  Scraping PSX Official Notices...")
    news = []
    
    try:
        url = "https://dps.psx.com.pk/announcements"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # PSX announcements table
        rows = soup.find_all('tr', limit=30)
        
        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    symbol = cells[0].get_text(strip=True)
                    headline = cells[2].get_text(strip=True) if len(cells) > 2 else cells[1].get_text(strip=True)
                    
                    if headline and len(headline) > 10:
                        sentiment_score = analyze_sentiment(headline)
                        
                        news.append({
                            'headline': f"[{symbol}] {headline}",
                            'source': 'PSX Official',
                            'url': 'https://dps.psx.com.pk/announcements',
                            'sentiment': sentiment_score,
                            'symbol': symbol,
                            'scraped_at': datetime.now().isoformat()
                        })
            except:
                continue
        
        print(f"    Found {len(news)} PSX notices")
    except Exception as e:
        print(f"    Error scraping PSX: {e}")
    
    return news


def get_all_news():
    """Fetch news from all sources"""
    print("\n" + "="*60)
    print("📰 FETCHING REAL NEWS FROM ALL SOURCES")
    print("="*60)
    
    all_news = []
    
    # Scrape all sources
    all_news.extend(scrape_dawn_business())
    time.sleep(1)
    all_news.extend(scrape_business_recorder())
    time.sleep(1)
    all_news.extend(scrape_express_tribune())
    time.sleep(1)
    all_news.extend(scrape_psx_notices())
    
    # Remove duplicates by headline
    seen = set()
    unique_news = []
    for item in all_news:
        if item['headline'] not in seen:
            seen.add(item['headline'])
            unique_news.append(item)
    
    # Save to database
    conn = get_connection()
    cursor = conn.cursor()
    
    for item in unique_news:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO news_headlines 
                (headline, source, url, sentiment_score, impact_level, related_symbols)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item['headline'],
                item['source'],
                item.get('url', ''),
                item['sentiment'],
                'high' if abs(item['sentiment']) > 0.3 else 'medium',
                item.get('symbol', '')
            ))
        except:
            pass
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Total: {len(unique_news)} unique news articles collected")
    
    return unique_news


# ==============================================================================
# FINANCIAL DATA - PSX Company Financials
# ==============================================================================

def get_psx_financial_summary(symbol: str) -> Dict:
    """Fetch company financial summary from PSX"""
    
    try:
        url = f"https://dps.psx.com.pk/company/{symbol}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            'symbol': symbol,
            'eps': None,
            'pe_ratio': None,
            'book_value': None,
            'market_cap': None,
            'dividend_yield': None,
            'volume_avg': None
        }
        
        # Try to extract from PSX company page
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    try:
                        if 'eps' in label:
                            data['eps'] = float(value.replace(',', '').replace('Rs', ''))
                        elif 'p/e' in label or 'pe' in label:
                            data['pe_ratio'] = float(value.replace(',', ''))
                        elif 'book' in label:
                            data['book_value'] = float(value.replace(',', '').replace('Rs', ''))
                        elif 'market cap' in label:
                            data['market_cap'] = value
                        elif 'dividend' in label and 'yield' in label:
                            data['dividend_yield'] = float(value.replace('%', ''))
                    except:
                        pass
        
        return data
        
    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}


def fetch_all_financials(symbols: List[str]) -> List[Dict]:
    """Fetch financial data for all symbols"""
    print("\n" + "="*60)
    print("💰 FETCHING COMPANY FINANCIAL DATA")
    print("="*60)
    
    financials = []
    
    for symbol in tqdm(symbols[:50], desc="Fetching financials"):  # Limit to 50
        data = get_psx_financial_summary(symbol)
        financials.append(data)
        time.sleep(0.5)  # Rate limiting
    
    # Count successful fetches
    success = sum(1 for f in financials if f.get('eps') or f.get('pe_ratio'))
    print(f"\n✅ Financial data fetched: {success}/{len(financials)}")
    
    return financials


# ==============================================================================
# PROFESSIONAL SCORING WITH REAL DATA
# ==============================================================================

def calculate_professional_score(symbol: str, price_data: Dict, financial_data: Dict, news_sentiment: float) -> Dict:
    """
    Calculate professional 100-point score using real data
    """
    scores = {
        'symbol': symbol,
        'financial': 0,
        'valuation': 0,
        'technical': 0,
        'sector_macro': 0,
        'news': 0,
        'total': 0,
        'rating': 'HOLD',
        'details': {}
    }
    
    # 1. FINANCIAL HEALTH (35 points)
    financial_score = 0
    
    eps = financial_data.get('eps')
    if eps:
        if eps > 10:
            financial_score += 15
        elif eps > 5:
            financial_score += 10
        elif eps > 0:
            financial_score += 5
    
    dividend = financial_data.get('dividend_yield')
    if dividend:
        if dividend > 5:
            financial_score += 10
        elif dividend > 2:
            financial_score += 7
        elif dividend > 0:
            financial_score += 4
    
    # Assume moderate health if we have data
    if eps or dividend:
        financial_score += 10
    
    scores['financial'] = min(35, financial_score)
    
    # 2. VALUATION (25 points)
    valuation_score = 0
    
    pe = financial_data.get('pe_ratio')
    if pe:
        if pe < 8:
            valuation_score += 15  # Very undervalued
        elif pe < 12:
            valuation_score += 12  # Undervalued
        elif pe < 18:
            valuation_score += 8  # Fair value
        elif pe < 25:
            valuation_score += 4  # Slightly overvalued
        else:
            valuation_score += 0  # Overvalued
    else:
        valuation_score += 5  # Default if no data
    
    book_value = financial_data.get('book_value')
    if book_value and price_data.get('close_price'):
        pb_ratio = price_data['close_price'] / book_value if book_value > 0 else 0
        if 0 < pb_ratio < 1:
            valuation_score += 10  # Trading below book value
        elif pb_ratio < 1.5:
            valuation_score += 7
        elif pb_ratio < 2.5:
            valuation_score += 4
    
    scores['valuation'] = min(25, valuation_score)
    
    # 3. TECHNICAL (20 points)
    technical_score = 0
    
    if price_data.get('close_price') and price_data.get('open_price'):
        change_pct = ((price_data['close_price'] - price_data['open_price']) / price_data['open_price']) * 100
        
        if change_pct > 3:
            technical_score += 8  # Strong up
        elif change_pct > 0:
            technical_score += 6  # Up
        elif change_pct > -3:
            technical_score += 4  # Slight down
        else:
            technical_score += 2  # Strong down
    else:
        technical_score += 5
    
    # Volume analysis
    if price_data.get('volume'):
        if price_data['volume'] > 1000000:
            technical_score += 6  # High volume
        elif price_data['volume'] > 500000:
            technical_score += 4
        else:
            technical_score += 2
    
    # Trend bonus
    technical_score += 6  # Default for having price data
    
    scores['technical'] = min(20, technical_score)
    
    # 4. SECTOR & MACRO (15 points)
    sector_score = 8  # Default moderate score
    
    # Add points for major sectors
    if symbol in ['OGDC', 'PPL', 'POL', 'MARI', 'PSO']:  # Oil & Gas
        sector_score = 10  # Oil stocks typically tracked
    elif symbol in ['HBL', 'UBL', 'MCB', 'NBP', 'ABL']:  # Banking
        sector_score = 12  # Banking always important
    elif symbol in ['ENGRO', 'FFC', 'FFBL']:  # Fertilizer
        sector_score = 11  # Agri focus
    
    scores['sector_macro'] = min(15, sector_score)
    
    # 5. NEWS SENTIMENT (5 points)
    if news_sentiment > 0.3:
        scores['news'] = 5
    elif news_sentiment > 0:
        scores['news'] = 4
    elif news_sentiment > -0.3:
        scores['news'] = 2
    else:
        scores['news'] = 1
    
    # Calculate total
    scores['total'] = (
        scores['financial'] +
        scores['valuation'] +
        scores['technical'] +
        scores['sector_macro'] +
        scores['news']
    )
    
    # Determine rating
    if scores['total'] >= 75:
        scores['rating'] = 'STRONG BUY'
    elif scores['total'] >= 60:
        scores['rating'] = 'BUY'
    elif scores['total'] >= 45:
        scores['rating'] = 'HOLD'
    elif scores['total'] >= 30:
        scores['rating'] = 'REDUCE'
    else:
        scores['rating'] = 'SELL/AVOID'
    
    # Add details
    scores['details'] = {
        'price': price_data.get('close_price', 0),
        'eps': eps,
        'pe_ratio': pe,
        'dividend_yield': dividend,
        'news_sentiment': news_sentiment
    }
    
    return scores


# ==============================================================================
# COMPREHENSIVE PROFESSIONAL REPORT
# ==============================================================================

def generate_professional_report(symbols: List[str]):
    """Generate comprehensive professional market report"""
    
    print("\n" + "="*70)
    print("🏆 PSX PROFESSIONAL MARKET INTELLIGENCE REPORT")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} PKT")
    print("="*70)
    
    # 1. Fetch real news
    all_news = get_all_news()
    
    # Calculate overall market sentiment from news
    avg_sentiment = sum(n['sentiment'] for n in all_news) / len(all_news) if all_news else 0
    
    # 2. Fetch prices for all symbols
    print("\n" + "="*60)
    print("📈 FETCHING LATEST PRICES")
    print("="*60)
    
    from scraper.price_scraper import fetch_all_prices
    from scraper.ticker_discovery import discover_and_save_tickers
    
    discover_and_save_tickers()
    prices_data = fetch_all_prices(symbols[:50], show_progress=True)
    
    # Create price lookup
    price_lookup = {p['symbol']: p for p in prices_data}
    
    # 3. Fetch financial data
    financials = fetch_all_financials(symbols[:30])
    financial_lookup = {f['symbol']: f for f in financials}
    
    # 4. Calculate professional scores
    print("\n" + "="*60)
    print("🔢 CALCULATING PROFESSIONAL 100-POINT SCORES")
    print("="*60)
    
    scored_stocks = []
    
    for symbol in tqdm(symbols[:50], desc="Scoring"):
        price_data = price_lookup.get(symbol, {})
        financial_data = financial_lookup.get(symbol, {})
        
        # Get news sentiment for this symbol
        symbol_news = [n for n in all_news if symbol in n.get('headline', '').upper()]
        symbol_sentiment = sum(n['sentiment'] for n in symbol_news) / len(symbol_news) if symbol_news else avg_sentiment
        
        score = calculate_professional_score(symbol, price_data, financial_data, symbol_sentiment)
        scored_stocks.append(score)
    
    # Sort by total score
    scored_stocks.sort(key=lambda x: x['total'], reverse=True)
    
    # 5. Print Professional Report
    print("\n")
    print("="*70)
    print("📊 PROFESSIONAL MARKET ANALYSIS REPORT")
    print(f"   Date: {datetime.now().strftime('%A, %B %d, %Y')}")
    print("="*70)
    
    # Market Overview
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│                    MARKET OVERVIEW                          │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│  News Articles Analyzed:    {len(all_news):<30}│")
    print(f"│  Market Sentiment:          {'BULLISH' if avg_sentiment > 0.1 else 'BEARISH' if avg_sentiment < -0.1 else 'NEUTRAL':<30}│")
    print(f"│  Stocks Analyzed:           {len(scored_stocks):<30}│")
    print("└─────────────────────────────────────────────────────────────┘")
    
    # Top 20 Stocks
    print("\n┌────────────────────────────────────────────────────────────────────┐")
    print("│                    TOP 20 STOCKS BY SCORE                          │")
    print("├────────┬────────┬───────────┬───────────┬──────────┬───────────────┤")
    print("│ Rank   │ Symbol │ Score     │ Price     │ P/E      │ Rating        │")
    print("├────────┼────────┼───────────┼───────────┼──────────┼───────────────┤")
    
    for i, stock in enumerate(scored_stocks[:20], 1):
        price = stock['details'].get('price', 0)
        pe = stock['details'].get('pe_ratio', '-')
        pe_str = f"{pe:.1f}" if isinstance(pe, (int, float)) else str(pe)
        
        print(f"│ {i:<6} │ {stock['symbol']:<6} │ {stock['total']:<9} │ Rs.{price:<6.2f} │ {pe_str:<8} │ {stock['rating']:<13} │")
    
    print("└────────┴────────┴───────────┴───────────┴──────────┴───────────────┘")
    
    # News Summary
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│                    TOP NEWS HEADLINES                        │")
    print("├─────────────────────────────────────────────────────────────┤")
    
    # Sort news by sentiment (most impactful first)
    sorted_news = sorted(all_news, key=lambda x: abs(x['sentiment']), reverse=True)
    
    for news in sorted_news[:10]:
        sentiment_icon = "🟢" if news['sentiment'] > 0.1 else "🔴" if news['sentiment'] < -0.1 else "🟡"
        headline = news['headline'][:55] + "..." if len(news['headline']) > 55 else news['headline']
        print(f"│ {sentiment_icon} {headline:<57} │")
    
    print("└─────────────────────────────────────────────────────────────┘")
    
    # Strong Buy Recommendations
    strong_buys = [s for s in scored_stocks if s['rating'] == 'STRONG BUY']
    buys = [s for s in scored_stocks if s['rating'] == 'BUY']
    
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│                    RECOMMENDATIONS                           │")
    print("├─────────────────────────────────────────────────────────────┤")
    
    if strong_buys:
        print(f"│  🌟 STRONG BUY: {', '.join([s['symbol'] for s in strong_buys[:5]]):<44}│")
    if buys:
        print(f"│  ✅ BUY:        {', '.join([s['symbol'] for s in buys[:5]]):<44}│")
    
    print("└─────────────────────────────────────────────────────────────┘")
    
    print("\n" + "="*70)
    print("✅ PROFESSIONAL REPORT COMPLETE")
    print("="*70)
    
    # Save to database
    conn = get_connection()
    cursor = conn.cursor()
    
    for stock in scored_stocks:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO stock_scores 
                (symbol, total_score, financial_score, valuation_score, technical_score, 
                 sector_macro_score, news_score, rating, score_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stock['symbol'],
                stock['total'],
                stock['financial'],
                stock['valuation'],
                stock['technical'],
                stock['sector_macro'],
                stock['news'],
                stock['rating'],
                datetime.now().strftime('%Y-%m-%d')
            ))
        except:
            pass
    
    conn.commit()
    conn.close()
    
    return scored_stocks, all_news


if __name__ == "__main__":
    # Top 100 PSX companies
    TOP_SYMBOLS = [
        # Banking
        'HBL', 'UBL', 'MCB', 'NBP', 'BAFL', 'MEBL', 'ABL', 'BAHL', 'AKBL', 'BOP',
        # Oil & Gas
        'OGDC', 'PPL', 'POL', 'MARI', 'PSO', 'APL', 'SNGP', 'SSGC',
        # Fertilizer
        'ENGRO', 'FFC', 'FFBL', 'EFERT', 'FATIMA',
        # Cement
        'LUCK', 'DGKC', 'MLCF', 'FCCL', 'PIOC', 'CHCC', 'KOHC', 'ACPL',
        # Power
        'HUBC', 'KAPCO', 'PKGP', 'NCPL',
        # Pharma
        'SEARL', 'GLAXO', 'HINOON', 'FEROZ', 'AGP',
        # Auto
        'INDU', 'HCAR', 'PSMC', 'HONDA', 'MTL',
        # Food
        'NESTLE', 'UPFL', 'FFL', 'COLG',
        # Technology
        'SYS', 'TRG', 'NETSOL'
    ]
    
    # Run professional report
    stocks, news = generate_professional_report(TOP_SYMBOLS)
    
    # Export to Excel
    print("\n\n📊 EXPORTING TO EXCEL...")
    import pandas as pd
    
    output_dir = os.path.join(os.path.dirname(__file__), 'exports')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Create DataFrames
    df_stocks = pd.DataFrame([{
        'Rank': i+1,
        'Symbol': s['symbol'],
        'Total Score': s['total'],
        'Financial (35)': s['financial'],
        'Valuation (25)': s['valuation'],
        'Technical (20)': s['technical'],
        'Sector/Macro (15)': s['sector_macro'],
        'News (5)': s['news'],
        'Rating': s['rating'],
        'Price': s['details'].get('price', ''),
        'EPS': s['details'].get('eps', ''),
        'P/E Ratio': s['details'].get('pe_ratio', ''),
        'Div Yield': s['details'].get('dividend_yield', '')
    } for i, s in enumerate(stocks)])
    
    df_news = pd.DataFrame(news)
    
    # Save to Excel
    excel_path = os.path.join(output_dir, f'professional_report_{timestamp}.xlsx')
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_stocks.to_excel(writer, sheet_name='Stock Analysis', index=False)
        df_news.to_excel(writer, sheet_name='News Analysis', index=False)
    
    print(f"✅ Excel saved: {excel_path}")
    
    # Also save CSV
    csv_stocks = os.path.join(output_dir, f'stock_analysis_{timestamp}.csv')
    csv_news = os.path.join(output_dir, f'news_analysis_{timestamp}.csv')
    
    df_stocks.to_csv(csv_stocks, index=False, encoding='utf-8-sig')
    df_news.to_csv(csv_news, index=False, encoding='utf-8-sig')
    
    print(f"✅ CSV saved: {csv_stocks}")
    print(f"✅ CSV saved: {csv_news}")
