"""
PSX Research Analyst - PDF Financial Report Analyzer
Downloads and extracts key financial metrics from company PDF reports
Uses PyPDF2 with in-memory reading for efficient processing
"""
import os
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PSX_BASE_URL, REQUEST_TIMEOUT, REQUEST_DELAY
from database.db_manager import db
from database.models import get_connection


def read_pdf_from_url(url: str) -> Optional[str]:
    """
    Read PDF directly from URL into memory and extract text
    Does not save file to disk
    Returns extracted text or None on error
    """
    try:
        # Ensure full URL
        if not url.startswith('http'):
            url = PSX_BASE_URL + url
        
        # Fetch PDF
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Read PDF from memory
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        # Read text from all pages
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text
        
    except Exception as e:
        print(f"Error reading PDF from {url}: {e}")
        return None


def parse_financial_metrics(text: str) -> Dict:
    """
    Parse key financial metrics from extracted text
    Returns dict with parsed values
    """
    metrics = {
        'revenue': None,
        'revenue_growth': None,
        'profit': None,
        'profit_growth': None,
        'eps': None,
        'eps_growth': None,
        'gross_margin': None,
        'net_margin': None,
        'dividend': None,
        'dividend_yield': None,
        'debt_to_equity': None,
        'roe': None,
        'roa': None,
        'book_value': None,
        'pe_ratio': None,
        'quarter': None,
        'fiscal_year': None
    }
    
    text_lower = text.lower()
    
    # Extract Revenue/Sales
    revenue_patterns = [
        r'(?:revenue|net sales|turnover|sales)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)\s*(?:million|mn|m|billion|bn|b)?',
        r'(?:revenue|net sales|turnover)[:\s]+([\d,\.]+)',
        r'total\s+(?:revenue|sales)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)'
    ]
    for pattern in revenue_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['revenue'] = clean_number(match.group(1))
            break
    
    # Extract Profit/Net Income
    profit_patterns = [
        r'(?:net profit|profit after tax|pat|net income)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)\s*(?:million|mn|m)?',
        r'(?:net profit|profit after tax)[:\s]+\(?([\d,\.]+)\)?',
        r'profit for the (?:year|period)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)'
    ]
    for pattern in profit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['profit'] = clean_number(match.group(1))
            break
    
    # Extract EPS
    eps_patterns = [
        r'(?:earnings per share|eps|basic eps)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'eps[:\s]+\(?([\d,\.]+)\)?',
        r'(?:basic|diluted)\s+(?:earnings per share|eps)[:\s]+([\d,\.]+)'
    ]
    for pattern in eps_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['eps'] = clean_number(match.group(1))
            break
    
    # Extract Dividend
    dividend_patterns = [
        r'(?:cash dividend|dividend per share)[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'(?:final|interim)?\s*dividend[:\s]+(\d+)%',
        r'dividend[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)\s*per share'
    ]
    for pattern in dividend_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['dividend'] = clean_number(match.group(1))
            break
    
    # Extract Growth percentages
    growth_patterns = [
        (r'(?:revenue|sales)\s+(?:growth|increase|grew)[:\s]+(\d+\.?\d*)%', 'revenue_growth'),
        (r'(?:profit|pat)\s+(?:growth|increase|grew)[:\s]+(\d+\.?\d*)%', 'profit_growth'),
        (r'eps\s+(?:growth|increase|grew)[:\s]+(\d+\.?\d*)%', 'eps_growth'),
        (r'(?:increased|grew|up)\s+by\s+(\d+\.?\d*)%\s+(?:in revenue|revenue)', 'revenue_growth'),
        (r'(?:increased|grew|up)\s+by\s+(\d+\.?\d*)%\s+(?:in profit|profit)', 'profit_growth')
    ]
    for pattern, key in growth_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics[key] = float(match.group(1))
    
    # Extract Margins
    margin_patterns = [
        (r'(?:gross margin|gross profit margin)[:\s]+(\d+\.?\d*)%', 'gross_margin'),
        (r'(?:net margin|net profit margin)[:\s]+(\d+\.?\d*)%', 'net_margin'),
        (r'(?:roe|return on equity)[:\s]+(\d+\.?\d*)%', 'roe'),
        (r'(?:roa|return on assets)[:\s]+(\d+\.?\d*)%', 'roa')
    ]
    for pattern, key in margin_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics[key] = float(match.group(1))
    
    # Extract Quarter/Period
    quarter_patterns = [
        r'(q[1-4])\s*(?:fy)?(\d{4}|\d{2})',
        r'(?:first|second|third|fourth)\s+quarter\s+(\d{4})',
        r'(?:half year|semi annual|annual)\s+(?:results?)?\s*(\d{4})',
        r'for the (?:quarter|year|period) ended[:\s]+([a-z]+\s+\d{1,2},?\s+\d{4})'
    ]
    for pattern in quarter_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['quarter'] = match.group(0).strip()
            break
    
    # Extract Book Value
    bv_patterns = [
        r'(?:book value|nav)\s*(?:per share)?[:\s]+(?:rs\.?|pkr)?\s*([\d,\.]+)',
        r'(?:net asset value|book value)[:\s]+([\d,\.]+)'
    ]
    for pattern in bv_patterns:
        match = re.search(pattern, text_lower)
        if match:
            metrics['book_value'] = clean_number(match.group(1))
            break
    
    return metrics


def clean_number(value: str) -> Optional[float]:
    """Clean and convert a number string to float"""
    try:
        # Remove commas and extra spaces
        cleaned = value.replace(',', '').replace(' ', '').strip()
        return float(cleaned)
    except:
        return None


def analyze_pdf_report(symbol: str, pdf_url: str) -> Dict:
    """
    Read PDF from URL, extract text, and parse financial metrics
    Uses in-memory reading - does not save files to disk
    """
    result = {
        'symbol': symbol,
        'pdf_url': pdf_url,
        'read_success': False,
        'metrics': {},
        'text_preview': '',
        'error': None
    }
    
    # Read PDF from URL into memory
    text = read_pdf_from_url(pdf_url)
    if not text:
        result['error'] = "Failed to read PDF from URL"
        return result
    
    result['read_success'] = True
    result['text_preview'] = text[:1000]  # First 1000 chars
    result['full_text_length'] = len(text)
    
    # Parse metrics
    metrics = parse_financial_metrics(text)
    result['metrics'] = metrics
    
    return result


def get_company_pdf_reports(symbol: str, limit: int = 5) -> List[Dict]:
    """
    Get PDF URLs for a company's recent announcements
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, headline, pdf_url, announcement_date, announcement_type
        FROM announcements
        WHERE symbol = ? AND pdf_url IS NOT NULL AND pdf_url != ''
        ORDER BY announcement_date DESC
        LIMIT ?
    """, (symbol, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'headline': row[1],
            'pdf_url': row[2],
            'date': row[3],
            'type': row[4]
        })
    
    conn.close()
    return results


def generate_financial_analysis(metrics: Dict, symbol: str) -> str:
    """
    Generate detailed financial analysis text based on extracted metrics
    """
    analysis_parts = []
    
    # Revenue Analysis
    if metrics.get('revenue'):
        analysis_parts.append(f"Revenue: Rs. {metrics['revenue']:,.0f}")
        if metrics.get('revenue_growth'):
            if metrics['revenue_growth'] > 10:
                analysis_parts.append(f"Strong revenue growth of {metrics['revenue_growth']:.1f}%.")
            elif metrics['revenue_growth'] > 0:
                analysis_parts.append(f"Modest revenue growth of {metrics['revenue_growth']:.1f}%.")
            else:
                analysis_parts.append(f"Revenue declined by {abs(metrics['revenue_growth']):.1f}%.")
    
    # Profit Analysis
    if metrics.get('profit'):
        analysis_parts.append(f"Net Profit: Rs. {metrics['profit']:,.0f}")
        if metrics.get('profit_growth'):
            if metrics['profit_growth'] > 20:
                analysis_parts.append(f"Excellent profit growth of {metrics['profit_growth']:.1f}% - strong execution.")
            elif metrics['profit_growth'] > 0:
                analysis_parts.append(f"Profit grew by {metrics['profit_growth']:.1f}%.")
            else:
                analysis_parts.append(f"Profit declined by {abs(metrics['profit_growth']):.1f}% - needs monitoring.")
    
    # EPS Analysis
    if metrics.get('eps'):
        analysis_parts.append(f"EPS: Rs. {metrics['eps']:.2f}")
        if metrics.get('eps_growth'):
            if metrics['eps_growth'] > 15:
                analysis_parts.append(f"Strong EPS growth of {metrics['eps_growth']:.1f}% indicates shareholder value creation.")
            elif metrics['eps_growth'] > 0:
                analysis_parts.append(f"EPS grew by {metrics['eps_growth']:.1f}%.")
    
    # Dividend Analysis
    if metrics.get('dividend'):
        analysis_parts.append(f"Dividend: Rs. {metrics['dividend']:.2f}/share - income opportunity for investors.")
    
    # Margin Analysis
    if metrics.get('gross_margin'):
        if metrics['gross_margin'] > 30:
            analysis_parts.append(f"Healthy gross margin of {metrics['gross_margin']:.1f}% indicates pricing power.")
        else:
            analysis_parts.append(f"Gross margin at {metrics['gross_margin']:.1f}%.")
    
    if metrics.get('net_margin'):
        if metrics['net_margin'] > 15:
            analysis_parts.append(f"Strong net margin of {metrics['net_margin']:.1f}% shows operational efficiency.")
        elif metrics['net_margin'] > 5:
            analysis_parts.append(f"Moderate net margin of {metrics['net_margin']:.1f}%.")
        else:
            analysis_parts.append(f"Thin net margin of {metrics['net_margin']:.1f}% - watch for improvement.")
    
    # ROE Analysis
    if metrics.get('roe'):
        if metrics['roe'] > 15:
            analysis_parts.append(f"ROE of {metrics['roe']:.1f}% exceeds cost of equity - value creation.")
        else:
            analysis_parts.append(f"ROE at {metrics['roe']:.1f}%.")
    
    # Book Value
    if metrics.get('book_value'):
        analysis_parts.append(f"Book Value: Rs. {metrics['book_value']:.2f}/share.")
    
    if not analysis_parts:
        return "Unable to extract financial metrics from available reports."
    
    return " ".join(analysis_parts)


def analyze_company_reports(symbol: str, max_reports: int = 3) -> Dict:
    """
    Analyze multiple PDF reports for a company
    Returns comprehensive analysis
    """
    print(f"  Analyzing PDF reports for {symbol}...")
    
    # Get PDF URLs
    reports = get_company_pdf_reports(symbol, limit=max_reports)
    
    if not reports:
        return {
            'symbol': symbol,
            'reports_found': 0,
            'analysis': "No PDF reports available for analysis.",
            'metrics': {}
        }
    
    all_metrics = {}
    
    for report in reports:
        if report.get('pdf_url'):
            print(f"    - Processing: {report['headline'][:50]}...")
            result = analyze_pdf_report(symbol, report['pdf_url'])
            
            if result.get('metrics'):
                # Merge metrics (prefer newer values)
                for key, value in result['metrics'].items():
                    if value is not None and key not in all_metrics:
                        all_metrics[key] = value
            
            time.sleep(REQUEST_DELAY)  # Rate limiting
    
    # Generate analysis
    analysis = generate_financial_analysis(all_metrics, symbol)
    
    return {
        'symbol': symbol,
        'reports_found': len(reports),
        'reports_analyzed': len([r for r in reports if r.get('pdf_url')]),
        'analysis': analysis,
        'metrics': all_metrics
    }


if __name__ == "__main__":
    # Test with a sample company
    test_symbol = "ENGRO"
    print(f"Testing PDF analysis for {test_symbol}...")
    
    result = analyze_company_reports(test_symbol)
    
    print(f"\nResults for {test_symbol}:")
    print(f"  Reports found: {result['reports_found']}")
    print(f"  Analysis: {result['analysis']}")
    print(f"  Metrics: {result['metrics']}")
