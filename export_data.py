"""
PSX Research Analyst - Export Data to Excel/CSV
Exports all research data, prices, and news to Excel
"""
import os
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from database.db_manager import db, get_connection

def export_all_data():
    """Export all research data to Excel"""
    
    print("=" * 60)
    print("📊 EXPORTING PSX RESEARCH DATA TO EXCEL")
    print("=" * 60)
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'exports')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    excel_path = os.path.join(output_dir, f'psx_research_data_{timestamp}.xlsx')
    
    conn = get_connection()
    
    # Create Excel writer
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        
        # 1. Tickers
        print("\n[1/6] Exporting tickers...")
        try:
            df_tickers = pd.read_sql_query("SELECT * FROM tickers ORDER BY symbol", conn)
            df_tickers.to_excel(writer, sheet_name='Tickers', index=False)
            print(f"  ✓ {len(df_tickers)} tickers exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 2. Price History
        print("[2/6] Exporting prices...")
        try:
            df_prices = pd.read_sql_query("""
                SELECT * FROM price_history
                ORDER BY symbol, date DESC
                LIMIT 5000
            """, conn)
            df_prices.to_excel(writer, sheet_name='Prices', index=False)
            print(f"  ✓ {len(df_prices)} price records exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 3. Stock Scores
        print("[3/6] Exporting stock scores...")
        try:
            df_scores = pd.read_sql_query("""
                SELECT * FROM stock_scores
                ORDER BY total_score DESC
            """, conn)
            df_scores.to_excel(writer, sheet_name='Stock Scores', index=False)
            print(f"  ✓ {len(df_scores)} stock scores exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 4. Announcements
        print("[4/6] Exporting announcements...")
        try:
            df_announcements = pd.read_sql_query("""
                SELECT * FROM announcements
                ORDER BY announcement_date DESC
                LIMIT 1000
            """, conn)
            df_announcements.to_excel(writer, sheet_name='Announcements', index=False)
            print(f"  ✓ {len(df_announcements)} announcements exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 5. News Headlines
        print("[5/6] Exporting news...")
        try:
            df_news = pd.read_sql_query("""
                SELECT * FROM news_headlines
                ORDER BY id DESC
                LIMIT 500
            """, conn)
            df_news.to_excel(writer, sheet_name='News', index=False)
            print(f"  ✓ {len(df_news)} news records exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 6. Technical Indicators
        print("[6/6] Exporting technical indicators...")
        try:
            df_technical = pd.read_sql_query("""
                SELECT * FROM technical_indicators
                ORDER BY symbol, date DESC
            """, conn)
            df_technical.to_excel(writer, sheet_name='Technical Indicators', index=False)
            print(f"  ✓ {len(df_technical)} technical records exported")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    conn.close()
    
    print(f"\n✅ Excel file saved to: {excel_path}")
    
    # Also create individual CSV files
    print("\n📄 Creating CSV files...")
    csv_dir = os.path.join(output_dir, f'csv_{timestamp}')
    os.makedirs(csv_dir, exist_ok=True)
    
    conn = get_connection()
    
    # Get all tables in database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table_name in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5000", conn)
            csv_path = os.path.join(csv_dir, f'{table_name}.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  ✓ {table_name}.csv ({len(df)} rows)")
        except Exception as e:
            print(f"  ✗ {table_name}: {e}")
    
    conn.close()
    
    print(f"\n✅ CSV files saved to: {csv_dir}")
    
    return excel_path, csv_dir


if __name__ == "__main__":
    excel_path, csv_dir = export_all_data()
    print(f"\n\n=== EXPORT COMPLETE ===")
    print(f"Excel: {excel_path}")
    print(f"CSVs:  {csv_dir}")
