"""
PSX Autonomous Research Analyst
Main orchestration script for daily market scanning and reporting

Usage:
    python main.py              # Run with scheduler (waits for 8:15 AM PKT)
    python main.py --run-now    # Run immediately
    python main.py --test       # Test with limited tickers
    python main.py --test-email # Test email configuration
"""
import argparse
import schedule
import time
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DAILY_SCAN_TIME, WATCHLIST, TOP_OPPORTUNITIES_COUNT, RED_ALERT_THRESHOLD
from database.db_manager import db
from scraper.ticker_discovery import discover_and_save_tickers, get_ticker_symbols
from scraper.price_scraper import fetch_all_prices
from scraper.announcements_scraper import scrape_all_announcements
from analysis.recommendation import analyze_all_tickers, get_watchlist_status
from analysis.sentiment import analyze_announcements_sentiment
from report.email_template import generate_html_report, save_report_to_file
from report.email_sender import send_daily_report, send_test_email, validate_email_config


def print_banner():
    """Print application banner"""
    banner = """
    ==============================================================
    |         PSX AUTONOMOUS RESEARCH ANALYST                    |
    |    Daily Market Scanner & Buy/Sell Recommendation Engine   |
    ==============================================================
    """
    print(banner)


def run_daily_scan(test_mode: bool = False, send_email: bool = True) -> Dict:
    """
    Execute the full daily market scan
    
    Args:
        test_mode: If True, only analyze a subset of tickers
        send_email: If True, send the report via email
    
    Returns:
        Dict with scan results
    """
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"Starting daily scan at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    results = {
        'start_time': start_time,
        'tickers_discovered': 0,
        'prices_fetched': 0,
        'announcements_found': 0,
        'tickers_analyzed': 0,
        'strong_buys': 0,
        'red_alerts': 0,
        'email_sent': False,
        'errors': []
    }
    
    try:
        # Step 1: Discover all tickers
        print("[1/8] STEP 1: Discovering all PSX tickers...")
        symbols = get_ticker_symbols(filter_non_equity=False)
        results['tickers_discovered'] = len(symbols)
        print(f"   Found {len(symbols)} tickers\n")
        
        # In test mode, only use a subset
        if test_mode:
            # Use watchlist + a few more for testing
            test_symbols = WATCHLIST + ['OGDC', 'HBL', 'LUCK', 'MCB', 'UBL', 
                                         'PPL', 'ENGRO', 'PSO', 'MTL', 'NESTLE']
            symbols = [s for s in symbols if s in test_symbols]
            print(f"   [TEST MODE] Using {len(symbols)} tickers for testing\n")
        
        # Step 2: Fetch prices for all tickers
        print("[2/8] STEP 2: Fetching price data...")
        prices = fetch_all_prices(symbols, show_progress=True)
        results['prices_fetched'] = len(prices)
        print(f"   Fetched prices for {len(prices)} tickers\n")
        
        # Step 3: Scrape announcements
        print("[3/8] STEP 3: Scraping company announcements...")
        ann_result = scrape_all_announcements(symbols, show_progress=True)
        results['announcements_found'] = ann_result.get('new_announcements', 0)
        print(f"   Found {ann_result.get('new_announcements', 0)} new announcements\n")
        
        # Step 4: Analyze sentiment of announcements
        print("[4/8] STEP 4: Analyzing announcement sentiment...")
        sentiment_results = analyze_announcements_sentiment()
        print(f"   Analyzed {len(sentiment_results)} announcements\n")
        
        # Step 5: Run full analysis on all tickers
        print("[5/8] STEP 5: Running technical and sentiment analysis...")
        analysis_results = analyze_all_tickers(symbols, show_progress=True)
        results['tickers_analyzed'] = len(analysis_results)
        print(f"   Analyzed {len(analysis_results)} tickers\n")
        
        # Step 6: Get top opportunities and red alerts
        print("[6/8] STEP 6: Identifying opportunities and alerts...")
        
        # Filter for strong buys and red alerts
        strong_buys = [r for r in analysis_results if r.get('recommendation') == 'STRONG BUY']
        red_alerts = [r for r in analysis_results if r.get('buy_score', 5) <= RED_ALERT_THRESHOLD]
        
        results['strong_buys'] = len(strong_buys)
        results['red_alerts'] = len(red_alerts)
        
        print(f"   Strong Buys: {len(strong_buys)}")
        print(f"   Red Alerts: {len(red_alerts)}\n")
        
        # Get watchlist status
        watchlist_analysis = [r for r in analysis_results if r['symbol'] in WATCHLIST]
        if len(watchlist_analysis) < len(WATCHLIST):
            # Some watchlist items might not have been analyzed, analyze them now
            missing = [s for s in WATCHLIST if s not in [w['symbol'] for w in watchlist_analysis]]
            if missing:
                print(f"   Analyzing missing watchlist items: {missing}")
                for symbol in missing:
                    from analysis.recommendation import analyze_ticker
                    result = analyze_ticker(symbol)
                    if result:
                        watchlist_analysis.append(result)
        
        # Step 7: Generate report
        print("[7/8] STEP 7: Generating HTML report...")
        
        market_summary = {
            'total_analyzed': results['tickers_analyzed'],
            'strong_buys': results['strong_buys'],
            'red_alerts': results['red_alerts']
        }
        
        html_report = generate_html_report(
            top_opportunities=analysis_results[:TOP_OPPORTUNITIES_COUNT],
            red_alerts=red_alerts[:5],
            watchlist_status=watchlist_analysis,
            market_summary=market_summary
        )
        
        # Save local copy
        filepath = save_report_to_file(html_report)
        print(f"   Report saved to: {filepath}\n")
        
        # Step 8: Send email
        if send_email:
            print("[8/8] STEP 8: Sending email report...")
            email_config = validate_email_config()
            
            if email_config['valid']:
                results['email_sent'] = send_daily_report(html_report, save_copy=False)
            else:
                print("   [!] Email not configured. Skipping email send.")
                for issue in email_config['issues']:
                    print(f"      - {issue}")
                results['errors'].append("Email not configured")
        else:
            print("[8/8] STEP 8: Skipping email (disabled)\n")
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"[OK] SCAN COMPLETE")
        print(f"{'='*60}")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Tickers Analyzed: {results['tickers_analyzed']}")
        print(f"   Strong Buy Signals: {results['strong_buys']}")
        print(f"   Red Alerts: {results['red_alerts']}")
        print(f"   Email Sent: {'Yes' if results['email_sent'] else 'No'}")
        print(f"{'='*60}\n")
        
        # Print top 5 opportunities
        print(">>> TOP 5 OPPORTUNITIES:")
        for i, stock in enumerate(analysis_results[:5], 1):
            print(f"   {i}. {stock['symbol']:8} | Score: {stock['buy_score']}/10 | {stock['recommendation']}")
        
        print("\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error during scan: {e}")
        results['errors'].append(str(e))
        import traceback
        traceback.print_exc()
    
    results['end_time'] = datetime.now()
    return results


def run_scheduler():
    """
    Run the scheduler that triggers daily scan at configured time
    """
    print(f"[SCHEDULER] Started. Daily scan scheduled for {DAILY_SCAN_TIME} PKT")
    print(f"   Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Press Ctrl+C to stop\n")
    
    # Schedule the daily scan
    schedule.every().day.at(DAILY_SCAN_TIME).do(run_daily_scan)
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Scheduler stopped by user")


def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(
        description='PSX Autonomous Research Analyst',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py              # Run with scheduler
    python main.py --run-now    # Run scan immediately  
    python main.py --test       # Test with limited tickers
    python main.py --test-email # Test email configuration
    python main.py --no-email   # Run without sending email
        """
    )
    
    parser.add_argument('--run-now', action='store_true',
                        help='Run the scan immediately instead of waiting for scheduled time')
    parser.add_argument('--test', action='store_true',
                        help='Test mode: analyze only watchlist and a few extra tickers')
    parser.add_argument('--test-email', action='store_true',
                        help='Send a test email to verify configuration')
    parser.add_argument('--no-email', action='store_true',
                        help='Skip sending email (just generate report)')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.test_email:
        print("Testing email configuration...\n")
        config = validate_email_config()
        
        if config['valid']:
            print("[OK] Configuration looks valid")
            print(f"  Sender: {config['sender']}")
            print(f"  Recipients: {config['recipients_count']}\n")
            
            print("Sending test email...")
            if send_test_email():
                print("\n[OK] Test email sent successfully!")
                print("Check your inbox (and spam folder) for the test email.")
            else:
                print("\n[ERROR] Failed to send test email. Check the error messages above.")
        else:
            print("[ERROR] Configuration issues found:")
            for issue in config['issues']:
                print(f"   - {issue}")
            print("\nPlease copy .env.example to .env and fill in your credentials.")
        return
    
    if args.run_now or args.test:
        # Run immediately
        run_daily_scan(test_mode=args.test, send_email=not args.no_email)
    else:
        # Run scheduler
        run_scheduler()


if __name__ == "__main__":
    main()
