"""
PSX Research Analyst - Top 100 Deep Research with PDF Analysis
Enhanced analysis with actual financial report extraction
"""
import pandas as pd
from datetime import datetime
import os
import sys
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db_manager import db
from database.models import get_connection
from config import WATCHLIST
from analysis.sentiment import interpret_sentiment
from scraper.pdf_analyzer import analyze_company_reports, get_company_pdf_reports
from top100_research import TOP_100_TICKERS, get_company_deep_analysis


def run_top100_with_pdf_analysis(max_pdf_per_company: int = 2):
    """
    Run comprehensive Top 100 analysis including PDF financial report extraction
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        os.path.dirname(__file__),
        "reports",
        f"psx_top100_detailed_{timestamp}.xlsx"
    )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("="*70)
    print("TOP 100 COMPREHENSIVE RESEARCH WITH PDF FINANCIAL ANALYSIS")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Companies to analyze: {len(TOP_100_TICKERS)}")
    print(f"PDFs per company: {max_pdf_per_company}")
    print()
    
    results = []
    
    for i, symbol in enumerate(tqdm(TOP_100_TICKERS, desc="Analyzing companies"), 1):
        try:
            # Get basic analysis
            basic = get_company_deep_analysis(symbol)
            
            # Get PDF analysis
            pdf_result = analyze_company_reports(symbol, max_reports=max_pdf_per_company)
            
            # Merge results
            result = {
                **basic,
                'pdf_reports_found': pdf_result.get('reports_found', 0),
                'financial_analysis': pdf_result.get('analysis', ''),
                'revenue': pdf_result.get('metrics', {}).get('revenue'),
                'revenue_growth': pdf_result.get('metrics', {}).get('revenue_growth'),
                'net_profit': pdf_result.get('metrics', {}).get('profit'),
                'profit_growth': pdf_result.get('metrics', {}).get('profit_growth'),
                'eps': pdf_result.get('metrics', {}).get('eps'),
                'eps_growth': pdf_result.get('metrics', {}).get('eps_growth'),
                'dividend_per_share': pdf_result.get('metrics', {}).get('dividend'),
                'gross_margin': pdf_result.get('metrics', {}).get('gross_margin'),
                'net_margin': pdf_result.get('metrics', {}).get('net_margin'),
                'roe': pdf_result.get('metrics', {}).get('roe'),
                'book_value': pdf_result.get('metrics', {}).get('book_value')
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"\n  Error analyzing {symbol}: {e}")
            # Still add basic result
            try:
                basic = get_company_deep_analysis(symbol)
                basic['pdf_reports_found'] = 0
                basic['financial_analysis'] = f"Error: {str(e)}"
                results.append(basic)
            except:
                pass
    
    print("\n")
    print("Generating comprehensive Excel report...")
    
    # Generate Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # ========== SHEET 1: Full Analysis with Financial Data ==========
        full_data = []
        for r in sorted(results, key=lambda x: x.get('buy_score', 0), reverse=True):
            full_data.append({
                'Symbol': r.get('symbol', ''),
                'Company': r.get('company_name', ''),
                'Price': r.get('current_price', 0),
                'Buy Score': r.get('buy_score', 5),
                'Recommendation': r.get('recommendation', 'HOLD'),
                '1D %': r.get('price_change_1d', 0),
                '7D %': r.get('price_change_7d', 0),
                '30D %': r.get('price_change_30d', 0),
                '52W Pos %': r.get('position_52w', 0),
                'RSI': r.get('rsi', ''),
                'Revenue (M)': r.get('revenue', ''),
                'Rev Growth %': r.get('revenue_growth', ''),
                'Net Profit (M)': r.get('net_profit', ''),
                'Profit Growth %': r.get('profit_growth', ''),
                'EPS': r.get('eps', ''),
                'EPS Growth %': r.get('eps_growth', ''),
                'Dividend/Share': r.get('dividend_per_share', ''),
                'Gross Margin %': r.get('gross_margin', ''),
                'Net Margin %': r.get('net_margin', ''),
                'ROE %': r.get('roe', ''),
                'Book Value': r.get('book_value', ''),
                'PDFs Analyzed': r.get('pdf_reports_found', 0),
                'Financial Analysis': r.get('financial_analysis', ''),
                'Growth Outlook': r.get('growth_outlook', '')
            })
        
        df_full = pd.DataFrame(full_data)
        df_full.to_excel(writer, sheet_name='Full Analysis', index=False)
        
        # ========== SHEET 2: Top Picks (Score 7+) ==========
        df_top = df_full[df_full['Buy Score'] >= 7].copy()
        df_top.to_excel(writer, sheet_name='Top Picks (7+)', index=False)
        
        # ========== SHEET 3: Growth Leaders ==========
        df_growth = df_full[
            (df_full['Profit Growth %'].notna()) | 
            (df_full['Rev Growth %'].notna())
        ].copy()
        df_growth = df_growth.sort_values('Profit Growth %', ascending=False, na_position='last')
        df_growth.to_excel(writer, sheet_name='Growth Leaders', index=False)
        
        # ========== SHEET 4: High ROE Companies ==========
        df_roe = df_full[df_full['ROE %'].notna()].copy()
        df_roe = df_roe.sort_values('ROE %', ascending=False)
        df_roe.to_excel(writer, sheet_name='High ROE', index=False)
        
        # ========== SHEET 5: Dividend Payers ==========
        df_div = df_full[df_full['Dividend/Share'].notna()].copy()
        df_div = df_div.sort_values('Dividend/Share', ascending=False)
        df_div.to_excel(writer, sheet_name='Dividend Payers', index=False)
        
        # ========== SHEET 6: Value Plays (Low 52W + Good Score) ==========
        df_value = df_full[(df_full['52W Pos %'] < 40) & (df_full['Buy Score'] >= 5)].copy()
        df_value = df_value.sort_values('Buy Score', ascending=False)
        df_value.to_excel(writer, sheet_name='Value Plays', index=False)
        
        # ========== SHEET 7: Momentum Plays (High 52W + Volume) ==========
        df_momentum = df_full[
            (df_full['30D %'] > 5) | 
            (df_full['52W Pos %'] > 70)
        ].copy()
        df_momentum = df_momentum.sort_values('30D %', ascending=False)
        df_momentum.to_excel(writer, sheet_name='Momentum Plays', index=False)
        
        # ========== SHEET 8: Detailed Financial Narratives ==========
        narrative_data = []
        for r in results:
            if r.get('financial_analysis') and len(r.get('financial_analysis', '')) > 50:
                narrative_data.append({
                    'Symbol': r.get('symbol', ''),
                    'Company': r.get('company_name', ''),
                    'Buy Score': r.get('buy_score', 5),
                    'Recommendation': r.get('recommendation', ''),
                    'Financial Analysis (from PDF)': r.get('financial_analysis', ''),
                    'Growth Outlook': r.get('growth_outlook', '')
                })
        
        df_narrative = pd.DataFrame(narrative_data)
        df_narrative.to_excel(writer, sheet_name='Detailed Narratives', index=False)
        
        # ========== SHEET 9: Sector Performance ==========
        sector_mapping = {
            'Oil & Gas': ['OGDC', 'PPL', 'POL', 'MARI', 'PSO', 'APL', 'SNGP', 'SSGC'],
            'Banking': ['HBL', 'MCB', 'UBL', 'NBP', 'ABL', 'BAFL', 'BAHL', 'MEBL'],
            'Cement': ['LUCK', 'DGKC', 'MLCF', 'FCCL', 'KOHC', 'CHCC', 'PIOC', 'ACPL'],
            'Power': ['HUBC', 'KAPCO', 'NPL', 'PKGP', 'KEL', 'NCPL'],
            'Fertilizer': ['ENGRO', 'FFC', 'FFBL', 'FATIMA', 'EFERT'],
            'Pharma': ['GLAXO', 'SEARL', 'FEROZ', 'HINOON', 'ABOT'],
            'Auto': ['INDU', 'HCAR', 'PSMC', 'MTL', 'GHNL'],
            'Tech': ['TRG', 'SYS', 'NETSOL', 'AVN', 'AIRLINK'],
            'FMCG': ['NESTLE', 'COLG', 'UNITY', 'FFL', 'TREET']
        }
        
        sector_data = []
        for sector, tickers in sector_mapping.items():
            sector_results = [r for r in results if r.get('symbol') in tickers]
            if sector_results:
                avg_score = sum(r.get('buy_score', 5) for r in sector_results) / len(sector_results)
                avg_change = sum(r.get('price_change_30d', 0) or 0 for r in sector_results) / len(sector_results)
                
                # Find companies with profit data
                profit_companies = [r for r in sector_results if r.get('profit_growth')]
                avg_profit_growth = sum(r.get('profit_growth', 0) for r in profit_companies) / len(profit_companies) if profit_companies else None
                
                best = max(sector_results, key=lambda x: x.get('buy_score', 0))
                
                sector_data.append({
                    'Sector': sector,
                    'Avg Score': round(avg_score, 1),
                    'Avg 30D %': round(avg_change, 1),
                    'Avg Profit Growth %': round(avg_profit_growth, 1) if avg_profit_growth else 'N/A',
                    'Top Pick': best.get('symbol', ''),
                    'Top Score': best.get('buy_score', 0),
                    'Companies': len(sector_results)
                })
        
        df_sector = pd.DataFrame(sector_data)
        df_sector = df_sector.sort_values('Avg Score', ascending=False)
        df_sector.to_excel(writer, sheet_name='Sector Performance', index=False)
        
        # ========== SHEET 10: Summary ==========
        summary = {
            'Metric': [
                'Report Generated',
                'Companies Analyzed',
                'PDFs Processed',
                'Top Picks (7+)',
                'Buy Recommendations (5-6)',
                'Hold/Avoid (<5)',
                'Best Sector',
                'Top Overall Pick',
                'Highest Growth Stock',
                'Best Dividend Stock'
            ],
            'Value': [
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                len(results),
                sum(1 for r in results if r.get('pdf_reports_found', 0) > 0),
                len(df_top),
                len(df_full[(df_full['Buy Score'] >= 5) & (df_full['Buy Score'] < 7)]),
                len(df_full[df_full['Buy Score'] < 5]),
                df_sector.iloc[0]['Sector'] if len(df_sector) > 0 else 'N/A',
                df_full.iloc[0]['Symbol'] if len(df_full) > 0 else 'N/A',
                df_growth.iloc[0]['Symbol'] if len(df_growth) > 0 and df_growth.iloc[0]['Profit Growth %'] else 'N/A',
                df_div.iloc[0]['Symbol'] if len(df_div) > 0 else 'N/A'
            ]
        }
        
        df_summary = pd.DataFrame(summary)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\n[OK] Report saved to: {output_path}")
    print()
    print("="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    
    # Print top 10
    print("\nTOP 10 PICKS WITH FINANCIAL METRICS:")
    print("-"*70)
    for i, r in enumerate(sorted(results, key=lambda x: x.get('buy_score', 0), reverse=True)[:10], 1):
        eps = f"EPS: {r.get('eps', 'N/A')}" if r.get('eps') else ""
        growth = f"Profit Growth: {r.get('profit_growth', 'N/A')}%" if r.get('profit_growth') else ""
        
        print(f"{i:2d}. {r.get('symbol', ''):8s} | Score: {r.get('buy_score', 0)}/10 | "
              f"{r.get('recommendation', ''):12s} | {eps} {growth}")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Top 100 Research with PDF Analysis')
    parser.add_argument('--pdfs', type=int, default=2, help='Max PDFs to analyze per company')
    args = parser.parse_args()
    
    run_top100_with_pdf_analysis(max_pdf_per_company=args.pdfs)
