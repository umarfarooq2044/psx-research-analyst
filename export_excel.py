"""
PSX Research Analyst - Export Analysis to Excel
Exports all analysis data to Excel spreadsheet
"""
import pandas as pd
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import db
from config import WATCHLIST


def export_analysis_to_excel(output_path: str = None) -> str:
    """
    Export all analysis data to Excel with multiple sheets
    """
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.dirname(__file__), 
            "reports", 
            f"psx_analysis_{timestamp}.xlsx"
        )
    
    # Ensure reports directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Exporting analysis data to Excel...")
    
    # Get today's analysis
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # ========== SHEET 1: Full Analysis Summary ==========
        print("  - Generating Full Analysis sheet...")
        conn = db.get_connection() if hasattr(db, 'get_connection') else None
        
        # Get all analysis results with company names
        from database.models import get_connection
        conn = get_connection()
        
        query = """
            SELECT 
                ar.symbol,
                t.name as company_name,
                ar.buy_score,
                ar.recommendation,
                ar.rsi,
                ar.volume_spike,
                ar.sentiment_score,
                ar.notes,
                ar.date
            FROM analysis_results ar
            LEFT JOIN tickers t ON ar.symbol = t.symbol
            WHERE ar.date = ?
            ORDER BY ar.buy_score DESC
        """
        
        df_analysis = pd.read_sql_query(query, conn, params=[today])
        
        # Add recommendation color coding description
        df_analysis['volume_spike'] = df_analysis['volume_spike'].apply(
            lambda x: 'Yes' if x == 1 else 'No'
        )
        
        # Round numeric columns (handle None values)
        if 'rsi' in df_analysis.columns:
            df_analysis['rsi'] = pd.to_numeric(df_analysis['rsi'], errors='coerce').round(2)
        if 'sentiment_score' in df_analysis.columns:
            df_analysis['sentiment_score'] = pd.to_numeric(df_analysis['sentiment_score'], errors='coerce').round(3)
        
        # Rename columns for clarity
        df_analysis.columns = [
            'Symbol', 'Company Name', 'Buy Score (1-10)', 'Recommendation',
            'RSI (14)', 'Volume Spike', 'Sentiment Score', 'Analysis Notes', 'Date'
        ]
        
        df_analysis.to_excel(writer, sheet_name='Full Analysis', index=False)
        
        # ========== SHEET 2: Strong Buy Opportunities ==========
        print("  - Generating Strong Buy sheet...")
        df_strong_buy = df_analysis[df_analysis['Buy Score (1-10)'] >= 8].copy()
        df_strong_buy.to_excel(writer, sheet_name='Strong Buy (8-10)', index=False)
        
        # ========== SHEET 3: Buy Recommendations ==========
        print("  - Generating Buy sheet...")
        df_buy = df_analysis[
            (df_analysis['Buy Score (1-10)'] >= 5) & 
            (df_analysis['Buy Score (1-10)'] < 8)
        ].copy()
        df_buy.to_excel(writer, sheet_name='Buy (5-7)', index=False)
        
        # ========== SHEET 4: Hold ==========
        print("  - Generating Hold sheet...")
        df_hold = df_analysis[
            (df_analysis['Buy Score (1-10)'] >= 4) & 
            (df_analysis['Buy Score (1-10)'] < 5)
        ].copy()
        df_hold.to_excel(writer, sheet_name='Hold (4)', index=False)
        
        # ========== SHEET 5: Sell/Avoid ==========
        print("  - Generating Sell-Avoid sheet...")
        df_sell = df_analysis[df_analysis['Buy Score (1-10)'] < 4].copy()
        df_sell.to_excel(writer, sheet_name='Sell-Avoid (1-3)', index=False)
        
        # ========== SHEET 6: Watchlist ==========
        print("  - Generating Watchlist sheet...")
        df_watchlist = df_analysis[df_analysis['Symbol'].isin(WATCHLIST)].copy()
        df_watchlist.to_excel(writer, sheet_name='Watchlist', index=False)
        
        # ========== SHEET 7: Volume Spikes ==========
        print("  - Generating Volume Spikes sheet...")
        df_volume = df_analysis[df_analysis['Volume Spike'] == 'Yes'].copy()
        df_volume.to_excel(writer, sheet_name='Volume Spikes', index=False)
        
        # ========== SHEET 8: Oversold (RSI < 40) ==========
        print("  - Generating Oversold sheet...")
        df_oversold = df_analysis[df_analysis['RSI (14)'] < 40].copy()
        df_oversold = df_oversold.sort_values('RSI (14)')
        df_oversold.to_excel(writer, sheet_name='Oversold (RSI below 40)', index=False)
        
        # ========== SHEET 9: Overbought (RSI > 70) ==========
        print("  - Generating Overbought sheet...")
        df_overbought = df_analysis[df_analysis['RSI (14)'] > 70].copy()
        df_overbought = df_overbought.sort_values('RSI (14)', ascending=False)
        df_overbought.to_excel(writer, sheet_name='Overbought (RSI above 70)', index=False)
        
        # ========== SHEET 10: Recent Announcements ==========
        print("  - Generating Announcements sheet...")
        ann_query = """
            SELECT 
                a.symbol,
                t.name as company_name,
                a.headline,
                a.announcement_type,
                a.sentiment_score,
                a.announcement_date,
                a.pdf_url
            FROM announcements a
            LEFT JOIN tickers t ON a.symbol = t.symbol
            WHERE a.announcement_date >= date('now', '-7 days')
            ORDER BY a.announcement_date DESC, a.symbol
        """
        df_announcements = pd.read_sql_query(ann_query, conn)
        
        # Interpret sentiment
        def interpret_sentiment(score):
            if score is None:
                return 'Not Analyzed'
            elif score > 0.3:
                return 'Positive'
            elif score > -0.3:
                return 'Neutral'
            else:
                return 'Negative'
        
        df_announcements['Sentiment'] = df_announcements['sentiment_score'].apply(interpret_sentiment)
        df_announcements.columns = [
            'Symbol', 'Company Name', 'Headline', 'Type', 
            'Sentiment Score', 'Date', 'PDF Link', 'Sentiment'
        ]
        
        df_announcements.to_excel(writer, sheet_name='Recent Announcements', index=False)
        
        # ========== SHEET 11: Price Data ==========
        print("  - Generating Price Data sheet...")
        price_query = """
            SELECT 
                p.symbol,
                t.name as company_name,
                p.close_price,
                p.high_price,
                p.low_price,
                p.volume,
                p.date
            FROM price_history p
            LEFT JOIN tickers t ON p.symbol = t.symbol
            WHERE p.date = ?
            ORDER BY p.symbol
        """
        df_prices = pd.read_sql_query(price_query, conn, params=[today])
        df_prices.columns = [
            'Symbol', 'Company Name', 'Close Price', 'High', 'Low', 'Volume', 'Date'
        ]
        df_prices.to_excel(writer, sheet_name='Price Data', index=False)
        
        # ========== SHEET 12: Summary Stats ==========
        print("  - Generating Summary sheet...")
        summary_data = {
            'Metric': [
                'Total Tickers Analyzed',
                'Strong Buy (8-10)',
                'Buy (5-7)',
                'Hold (4)',
                'Sell/Avoid (1-3)',
                'Watchlist Tickers',
                'Volume Spikes Today',
                'Oversold Stocks (RSI < 40)',
                'Overbought Stocks (RSI > 70)',
                'Recent Announcements (7 days)',
                'Report Generated At'
            ],
            'Value': [
                len(df_analysis),
                len(df_strong_buy),
                len(df_buy),
                len(df_hold),
                len(df_sell),
                len(df_watchlist),
                len(df_volume),
                len(df_oversold),
                len(df_overbought),
                len(df_announcements),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        conn.close()
    
    print(f"\n[OK] Excel report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    export_analysis_to_excel()
