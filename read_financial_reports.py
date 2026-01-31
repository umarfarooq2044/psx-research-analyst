"""
PSX Financial Reports Reader
Downloads and extracts key financial data from PSX annual/quarterly reports
"""
import requests
import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# PDF reading library
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

# Create directories
REPORTS_DIR = Path("financial_reports")
REPORTS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)

# Top 6 companies and their latest quarterly report PDF links
COMPANY_REPORTS = {
    "FFC": {
        "name": "Fauji Fertilizer Company Limited",
        "quarterly_report": "https://dps.psx.com.pk/download/document/264632.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/258110.pdf"
    },
    "LUCK": {
        "name": "Lucky Cement Limited", 
        "quarterly_report": "https://dps.psx.com.pk/download/document/264455.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/258917.pdf"
    },
    "UBL": {
        "name": "United Bank Limited",
        "quarterly_report": "https://dps.psx.com.pk/download/document/264343.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/258618.pdf"
    },
    "MEBL": {
        "name": "Meezan Bank Limited",
        "quarterly_report": "https://dps.psx.com.pk/download/document/264198.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/258329.pdf"
    },
    "PSO": {
        "name": "Pakistan State Oil Company Limited",
        "quarterly_report": "https://dps.psx.com.pk/download/document/264179.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/260771.pdf"
    },
    "FFBL": {
        "name": "Fauji Fertilizer Bin Qasim Limited",
        "quarterly_report": "https://dps.psx.com.pk/download/document/241641.pdf",
        "annual_report": "https://dps.psx.com.pk/download/document/235591.pdf"
    }
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def download_pdf(url, symbol, report_type="quarterly"):
    """Download a PDF file from PSX"""
    filepath = REPORTS_DIR / f"{symbol}_{report_type}_report.pdf"
    
    if filepath.exists():
        print(f"  [CACHED] {filepath.name}")
        return filepath
    
    print(f"  Downloading {report_type} report...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f"  [OK] Saved {len(resp.content)/1024:.1f} KB")
            return filepath
        else:
            print(f"  [FAIL] HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] {str(e)[:50]}")
        return None


def extract_text_from_pdf(filepath):
    """Extract text from PDF using available library"""
    text = ""
    
    if HAS_FITZ:
        try:
            doc = fitz.open(filepath)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"  [PyMuPDF Error] {str(e)[:50]}")
    
    if HAS_PYPDF:
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text
        except Exception as e:
            print(f"  [PyPDF Error] {str(e)[:50]}")
    
    return text


def extract_financial_metrics(text, symbol):
    """Extract key financial metrics from report text"""
    metrics = {
        "symbol": symbol,
        "company_name": COMPANY_REPORTS.get(symbol, {}).get("name", symbol),
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "revenue": None,
        "net_profit": None,
        "eps": None,
        "gross_margin": None,
        "net_margin": None,
        "total_assets": None,
        "total_liabilities": None,
        "dividend": None,
        "key_highlights": []
    }
    
    if not text:
        return metrics
    
    # Clean text
    text_lower = text.lower()
    
    # Extract Revenue/Sales patterns
    revenue_patterns = [
        r"(?:net\s+)?(?:revenue|sales|turnover)[:\s]+(?:rs\.?|pkr\.?)\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion|m|bn)?",
        r"(?:revenue|sales)[:\s]+([\d,]+(?:\.\d+)?)\s*(?:million|billion)?",
        r"gross\s+sales[:\s]+(?:rs\.?|pkr\.?)?\s*([\d,]+(?:\.\d+)?)",
    ]
    
    for pattern in revenue_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1).replace(",", ""))
                if value > 1000:  # Likely in millions
                    metrics["revenue"] = f"{value/1000:.2f} Billion PKR"
                else:
                    metrics["revenue"] = f"{value:.2f} Million PKR"
                break
            except:
                pass
    
    # Extract Net Profit patterns
    profit_patterns = [
        r"(?:net\s+)?profit(?:\s+after\s+tax)?[:\s]+(?:rs\.?|pkr\.?)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion)?",
        r"profit\s+for\s+the\s+(?:period|year)[:\s]+(?:rs\.?|pkr\.?)?\s*([\d,]+(?:\.\d+)?)",
        r"(?:pat|pbt)[:\s]+(?:rs\.?|pkr\.?)?\s*([\d,]+(?:\.\d+)?)",
    ]
    
    for pattern in profit_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1).replace(",", ""))
                if value > 1000:
                    metrics["net_profit"] = f"{value/1000:.2f} Billion PKR"
                else:
                    metrics["net_profit"] = f"{value:.2f} Million PKR"
                break
            except:
                pass
    
    # Extract EPS
    eps_patterns = [
        r"(?:earnings|basic\s+eps|eps)\s+per\s+share[:\s]+(?:rs\.?|pkr\.?)?\s*([\d.]+)",
        r"eps[:\s]+(?:rs\.?|pkr\.?)?\s*([\d.]+)",
        r"basic\s+earning[s]?\s+per\s+share[:\s]+(?:rs\.?|pkr\.?)?\s*([\d.]+)",
    ]
    
    for pattern in eps_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1))
                if value > 0:
                    metrics["eps"] = f"Rs. {value:.2f}"
                    break
            except:
                pass
    
    # Extract Dividend
    dividend_patterns = [
        r"(?:cash\s+)?dividend[:\s]+(?:rs\.?|pkr\.?)?\s*([\d.]+)\s*(?:per\s+share)?",
        r"dividend\s+(?:of|@)\s*(?:rs\.?|pkr\.?)?\s*([\d.]+)",
        r"interim\s+dividend[:\s]+(?:rs\.?|pkr\.?)?\s*([\d.]+)",
    ]
    
    for pattern in dividend_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1))
                if value > 0:
                    metrics["dividend"] = f"Rs. {value:.2f} per share"
                    break
            except:
                pass
    
    # Extract key numbers from text (amounts in billions/millions)
    amounts = re.findall(r"(?:rs\.?|pkr\.?)\s*([\d,]+(?:\.\d+)?)\s*(million|billion|mn|bn)", text_lower)
    if amounts:
        # Store top amounts as potential key figures
        for amount, unit in amounts[:5]:
            try:
                value = float(amount.replace(",", ""))
                unit_lower = unit.lower()
                if "billion" in unit_lower or "bn" in unit_lower:
                    metrics["key_highlights"].append(f"Rs. {value:.2f} Billion")
                else:
                    metrics["key_highlights"].append(f"Rs. {value:.2f} Million")
            except:
                pass
    
    return metrics


def main():
    print("=" * 60)
    print("PSX FINANCIAL REPORTS READER")
    print("Top 6 Companies: FFBL, UBL, LUCK, FFC, MEBL, PSO")
    print("=" * 60)
    print()
    
    if not HAS_FITZ and not HAS_PYPDF:
        print("[WARNING] No PDF library available. Installing pymupdf...")
        os.system("pip install pymupdf --quiet")
    
    all_metrics = []
    
    for symbol, info in COMPANY_REPORTS.items():
        print(f"\n[{symbol}] {info['name']}")
        print("-" * 50)
        
        # Download quarterly report
        pdf_path = download_pdf(info["quarterly_report"], symbol, "quarterly")
        
        if pdf_path and pdf_path.exists():
            print("  Extracting text from PDF...")
            text = extract_text_from_pdf(pdf_path)
            
            if text:
                print(f"  Extracted {len(text)} characters")
                metrics = extract_financial_metrics(text, symbol)
                all_metrics.append(metrics)
                
                # Print key metrics
                print(f"  Revenue: {metrics['revenue'] or 'Not found'}")
                print(f"  Net Profit: {metrics['net_profit'] or 'Not found'}")
                print(f"  EPS: {metrics['eps'] or 'Not found'}")
                print(f"  Dividend: {metrics['dividend'] or 'Not found'}")
            else:
                print("  [WARN] Could not extract text from PDF")
                metrics = extract_financial_metrics("", symbol)
                all_metrics.append(metrics)
        else:
            print("  [SKIP] PDF not available")
            metrics = extract_financial_metrics("", symbol)
            all_metrics.append(metrics)
    
    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    json_file = EXPORTS_DIR / f"financial_reports_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] JSON saved: {json_file}")
    
    # Save to CSV
    csv_file = EXPORTS_DIR / f"financial_reports_{timestamp}.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        headers = ["Symbol", "Company Name", "Revenue", "Net Profit", "EPS", "Dividend", "Key Highlights"]
        f.write(",".join(headers) + "\n")
        for m in all_metrics:
            highlights = "; ".join(m.get("key_highlights", [])[:3])
            row = [
                m.get("symbol", ""),
                m.get("company_name", ""),
                m.get("revenue", "N/A"),
                m.get("net_profit", "N/A"),
                m.get("eps", "N/A"),
                m.get("dividend", "N/A"),
                f'"{highlights}"'
            ]
            f.write(",".join(str(x) for x in row) + "\n")
    print(f"[OK] CSV saved: {csv_file}")
    
    # Print summary table
    print("\n" + "=" * 80)
    print("FINANCIAL SUMMARY - TOP 6 PSX COMPANIES")
    print("=" * 80)
    print(f"{'Symbol':<8} {'Revenue':<20} {'Net Profit':<20} {'EPS':<15} {'Dividend':<15}")
    print("-" * 80)
    for m in all_metrics:
        print(f"{m['symbol']:<8} {(m['revenue'] or 'N/A'):<20} {(m['net_profit'] or 'N/A'):<20} {(m['eps'] or 'N/A'):<15} {(m['dividend'] or 'N/A'):<15}")
    print("=" * 80)


if __name__ == "__main__":
    main()
