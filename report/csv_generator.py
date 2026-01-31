"""
PSX Research Analyst - Professional CSV Report Generator
=========================================================
Generates comprehensive CSV reports with deep analysis for:
- Hourly news digest
- Daily stock analysis
- Sector breakdown
- Risk assessment
- Investment recommendations

Author: Professional Market Analyst System
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db


class ProfessionalReportGenerator:
    """
    Generates institutional-grade research reports with comprehensive analysis.
    Designed for serious investors who need detailed data for decision-making.
    """
    
    def __init__(self):
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # =========================================================================
    # HOURLY NEWS REPORT
    # =========================================================================
    
    def generate_hourly_news_csv(self, news_data: Dict) -> str:
        """
        Generate hourly news digest CSV with sentiment analysis.
        
        Returns: Path to generated CSV file
        """
        filepath = os.path.join(self.reports_dir, f'hourly_news_{self.timestamp}.csv')
        
        # Combine all news
        all_news = []
        
        for item in news_data.get('national', []):
            all_news.append({
                'Time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Category': 'National (Pakistan)',
                'Source': item.get('source', 'Unknown'),
                'Headline': item.get('headline', ''),
                'Sentiment_Score': round(item.get('sentiment', 0), 3),
                'Sentiment': 'Bullish' if item.get('sentiment', 0) > 0.1 else 'Bearish' if item.get('sentiment', 0) < -0.1 else 'Neutral',
                'Market_Impact': 'High' if abs(item.get('sentiment', 0)) > 0.5 else 'Medium' if abs(item.get('sentiment', 0)) > 0.2 else 'Low',
                'URL': item.get('url', '')
            })
        
        for item in news_data.get('international', []):
            all_news.append({
                'Time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Category': 'International',
                'Source': item.get('source', 'Unknown'),
                'Headline': item.get('headline', ''),
                'Sentiment_Score': round(item.get('sentiment', 0), 3),
                'Sentiment': 'Bullish' if item.get('sentiment', 0) > 0.1 else 'Bearish' if item.get('sentiment', 0) < -0.1 else 'Neutral',
                'Market_Impact': 'High' if abs(item.get('sentiment', 0)) > 0.5 else 'Medium' if abs(item.get('sentiment', 0)) > 0.2 else 'Low',
                'URL': item.get('url', '')
            })
        
        for item in news_data.get('announcements', []):
            all_news.append({
                'Time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Category': 'PSX Announcement',
                'Source': 'PSX Official',
                'Headline': item.get('headline', ''),
                'Sentiment_Score': round(item.get('sentiment', 0), 3),
                'Sentiment': 'Bullish' if item.get('sentiment', 0) > 0.1 else 'Bearish' if item.get('sentiment', 0) < -0.1 else 'Neutral',
                'Market_Impact': 'High',  # All PSX announcements are important
                'URL': item.get('url', '')
            })
        
        # Write CSV
        if all_news:
            df = pd.DataFrame(all_news)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        else:
            # Create empty template
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', 'Category', 'Source', 'Headline', 'Sentiment_Score', 'Sentiment', 'Market_Impact', 'URL'])
                writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M'), 'Info', 'System', 'No significant news at this hour', 0, 'Neutral', 'Low', ''])
        
        return filepath
    
    # =========================================================================
    # DAILY COMPREHENSIVE STOCK REPORT
    # =========================================================================
    
    def generate_daily_stock_analysis_csv(self) -> str:
        """
        Generate comprehensive daily stock analysis report.
        Includes: Price, Volume, Technical Indicators, Score, Recommendation
        
        Returns: Path to generated CSV file
        """
        filepath = os.path.join(self.reports_dir, f'daily_stock_analysis_{self.timestamp}.csv')
        
        # Get all stocks with latest data
        tickers = db.get_all_tickers() or []
        stocks_data = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            
            # Get latest price
            price_data = db.get_latest_price(symbol) or {}
            
            # Get stock score
            score_data = db.get_stock_score(symbol) or {}
            
            # Get technical indicators
            tech_data = db.get_technical_indicators(symbol) or {}
            
            # Calculate recommendation based on comprehensive analysis
            score = score_data.get('total_score', 0) or 0
            rsi = tech_data.get('rsi', 50) or 50
            
            recommendation = self._calculate_recommendation(score, rsi, price_data)
            risk_level = self._calculate_risk_level(price_data, tech_data)
            
            stocks_data.append({
                'Symbol': symbol,
                'Company': ticker.get('company_name', symbol),
                'Sector': ticker.get('sector', 'Unknown'),
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Close_Price': round(price_data.get('close', 0) or 0, 2),
                'Change_%': round(price_data.get('change_percent', 0) or 0, 2),
                'Volume': price_data.get('volume', 0) or 0,
                'Volume_Avg': price_data.get('avg_volume', 0) or 0,
                'Volume_Ratio': round((price_data.get('volume', 0) or 1) / max(price_data.get('avg_volume', 1) or 1, 1), 2),
                'Day_High': round(price_data.get('high', 0) or 0, 2),
                'Day_Low': round(price_data.get('low', 0) or 0, 2),
                'RSI_14': round(rsi, 2),
                'RSI_Signal': 'Oversold' if rsi < 30 else 'Overbought' if rsi > 70 else 'Neutral',
                'SMA_20': round(tech_data.get('sma_20', 0) or 0, 2),
                'SMA_50': round(tech_data.get('sma_50', 0) or 0, 2),
                'MACD': round(tech_data.get('macd', 0) or 0, 4),
                'MACD_Signal': 'Bullish' if (tech_data.get('macd', 0) or 0) > (tech_data.get('macd_signal', 0) or 0) else 'Bearish',
                'Total_Score': round(score, 1),
                'Score_Grade': self._score_to_grade(score),
                'Technical_Score': round(score_data.get('technical_score', 0) or 0, 1),
                'Fundamental_Score': round(score_data.get('fundamental_score', 0) or 0, 1),
                'Sentiment_Score': round(score_data.get('sentiment_score', 0) or 0, 1),
                'Momentum_Score': round(score_data.get('momentum_score', 0) or 0, 1),
                'Risk_Level': risk_level,
                'Recommendation': recommendation,
                'Target_Support': round(tech_data.get('support', price_data.get('close', 0) * 0.95) or 0, 2),
                'Target_Resistance': round(tech_data.get('resistance', price_data.get('close', 0) * 1.05) or 0, 2),
            })
        
        # Sort by score descending
        stocks_data.sort(key=lambda x: x['Total_Score'], reverse=True)
        
        # Write to CSV
        if stocks_data:
            df = pd.DataFrame(stocks_data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        else:
            # Create template
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Symbol', 'Company', 'Sector', 'Date', 'Close_Price', 'Change_%', 
                               'Volume', 'RSI_14', 'Total_Score', 'Recommendation', 'Risk_Level'])
        
        return filepath
    
    # =========================================================================
    # SECTOR ANALYSIS REPORT
    # =========================================================================
    
    def generate_sector_analysis_csv(self) -> str:
        """
        Generate sector-wise market analysis.
        
        Returns: Path to generated CSV file
        """
        filepath = os.path.join(self.reports_dir, f'sector_analysis_{self.timestamp}.csv')
        
        tickers = db.get_all_tickers() or []
        
        # Group by sector
        sectors = {}
        for ticker in tickers:
            sector = ticker.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'count': 0, 'gainers': 0, 'losers': 0, 'total_change': 0}
            
            price_data = db.get_latest_price(ticker['symbol']) or {}
            change = price_data.get('change_percent', 0) or 0
            
            sectors[sector]['count'] += 1
            sectors[sector]['total_change'] += change
            if change > 0:
                sectors[sector]['gainers'] += 1
            elif change < 0:
                sectors[sector]['losers'] += 1
        
        # Build sector data
        sector_data = []
        for sector, data in sectors.items():
            avg_change = data['total_change'] / max(data['count'], 1)
            breadth = (data['gainers'] - data['losers']) / max(data['count'], 1) * 100
            
            sector_data.append({
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Sector': sector,
                'Stocks_Count': data['count'],
                'Gainers': data['gainers'],
                'Losers': data['losers'],
                'Unchanged': data['count'] - data['gainers'] - data['losers'],
                'Avg_Change_%': round(avg_change, 2),
                'Market_Breadth_%': round(breadth, 1),
                'Sector_Trend': 'Bullish' if avg_change > 1 else 'Bearish' if avg_change < -1 else 'Neutral',
                'Sector_Strength': 'Strong' if breadth > 50 else 'Weak' if breadth < -50 else 'Mixed'
            })
        
        # Sort by average change
        sector_data.sort(key=lambda x: x['Avg_Change_%'], reverse=True)
        
        if sector_data:
            df = pd.DataFrame(sector_data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    # =========================================================================
    # TOP OPPORTUNITIES REPORT
    # =========================================================================
    
    def generate_top_opportunities_csv(self, limit: int = 20) -> str:
        """
        Generate top investment opportunities based on comprehensive scoring.
        
        Returns: Path to generated CSV file
        """
        filepath = os.path.join(self.reports_dir, f'top_opportunities_{self.timestamp}.csv')
        
        tickers = db.get_all_tickers() or []
        opportunities = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            score_data = db.get_stock_score(symbol) or {}
            price_data = db.get_latest_price(symbol) or {}
            tech_data = db.get_technical_indicators(symbol) or {}
            
            total_score = score_data.get('total_score', 0) or 0
            
            if total_score >= 60:  # Only high-scoring stocks
                rsi = tech_data.get('rsi', 50) or 50
                close = price_data.get('close', 0) or 0
                support = tech_data.get('support', close * 0.95) or (close * 0.95)
                resistance = tech_data.get('resistance', close * 1.05) or (close * 1.05)
                
                upside = ((resistance - close) / max(close, 1)) * 100 if close else 0
                downside = ((close - support) / max(close, 1)) * 100 if close else 0
                risk_reward = upside / max(downside, 0.1)
                
                opportunities.append({
                    'Rank': 0,  # Will be set after sorting
                    'Symbol': symbol,
                    'Company': ticker.get('company_name', symbol),
                    'Sector': ticker.get('sector', 'Unknown'),
                    'Current_Price': round(close, 2),
                    'Total_Score': round(total_score, 1),
                    'Grade': self._score_to_grade(total_score),
                    'RSI': round(rsi, 1),
                    'Support': round(support, 2),
                    'Resistance': round(resistance, 2),
                    'Upside_%': round(upside, 1),
                    'Downside_%': round(downside, 1),
                    'Risk_Reward_Ratio': round(risk_reward, 2),
                    'Recommendation': self._calculate_recommendation(total_score, rsi, price_data),
                    'Entry_Strategy': 'Buy at current' if rsi < 40 else 'Wait for pullback' if rsi > 60 else 'Accumulate',
                    'Stop_Loss': round(support * 0.97, 2),
                    'Target_1': round(resistance, 2),
                    'Target_2': round(resistance * 1.05, 2),
                })
        
        # Sort and rank
        opportunities.sort(key=lambda x: (x['Total_Score'], x['Risk_Reward_Ratio']), reverse=True)
        for i, opp in enumerate(opportunities[:limit], 1):
            opp['Rank'] = i
        
        if opportunities:
            df = pd.DataFrame(opportunities[:limit])
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    # =========================================================================
    # RISK ALERTS REPORT
    # =========================================================================
    
    def generate_risk_alerts_csv(self) -> str:
        """
        Generate risk alerts for stocks showing warning signs.
        
        Returns: Path to generated CSV file
        """
        filepath = os.path.join(self.reports_dir, f'risk_alerts_{self.timestamp}.csv')
        
        tickers = db.get_all_tickers() or []
        alerts = []
        
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            price_data = db.get_latest_price(symbol) or {}
            tech_data = db.get_technical_indicators(symbol) or {}
            
            risk_flags = []
            severity = 'Low'
            
            # Check for risk conditions
            change = price_data.get('change_percent', 0) or 0
            volume = price_data.get('volume', 0) or 0
            avg_volume = price_data.get('avg_volume', 1) or 1
            rsi = tech_data.get('rsi', 50) or 50
            
            if change < -5:
                risk_flags.append('Sharp decline (>5%)')
                severity = 'High'
            elif change < -3:
                risk_flags.append('Significant decline (>3%)')
                severity = 'Medium' if severity == 'Low' else severity
            
            if rsi > 80:
                risk_flags.append('Extremely overbought (RSI>80)')
                severity = 'High'
            elif rsi > 70:
                risk_flags.append('Overbought (RSI>70)')
                severity = 'Medium' if severity == 'Low' else severity
            
            if rsi < 20:
                risk_flags.append('Extremely oversold (RSI<20)')
                severity = 'Medium' if severity == 'Low' else severity
            
            if volume > avg_volume * 3:
                risk_flags.append('Abnormal volume spike (3x avg)')
                severity = 'High'
            elif volume > avg_volume * 2:
                risk_flags.append('High volume (2x avg)')
            
            if risk_flags:
                alerts.append({
                    'Date': datetime.now().strftime('%Y-%m-%d'),
                    'Time': datetime.now().strftime('%H:%M'),
                    'Symbol': symbol,
                    'Company': ticker.get('company_name', symbol),
                    'Severity': severity,
                    'Current_Price': round(price_data.get('close', 0) or 0, 2),
                    'Change_%': round(change, 2),
                    'RSI': round(rsi, 1),
                    'Volume_Ratio': round(volume / max(avg_volume, 1), 2),
                    'Risk_Flags': ' | '.join(risk_flags),
                    'Action_Required': 'Review immediately' if severity == 'High' else 'Monitor closely' if severity == 'Medium' else 'Watch',
                })
        
        # Sort by severity
        severity_order = {'High': 0, 'Medium': 1, 'Low': 2}
        alerts.sort(key=lambda x: (severity_order.get(x['Severity'], 3), x['Change_%']))
        
        if alerts:
            df = pd.DataFrame(alerts)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _calculate_recommendation(self, score: float, rsi: float, price_data: Dict) -> str:
        """Calculate investment recommendation based on multiple factors"""
        change = price_data.get('change_percent', 0) or 0
        
        if score >= 80 and rsi < 70:
            return 'STRONG BUY'
        elif score >= 70 and rsi < 65:
            return 'BUY'
        elif score >= 60 and rsi >= 30 and rsi <= 70:
            return 'ACCUMULATE'
        elif score >= 50:
            return 'HOLD'
        elif score >= 40 or rsi > 75:
            return 'REDUCE'
        elif score < 40 or rsi > 80:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_risk_level(self, price_data: Dict, tech_data: Dict) -> str:
        """Calculate risk level for a stock"""
        rsi = tech_data.get('rsi', 50) or 50
        change = abs(price_data.get('change_percent', 0) or 0)
        
        if rsi > 80 or rsi < 20 or change > 7:
            return 'Very High'
        elif rsi > 70 or rsi < 30 or change > 5:
            return 'High'
        elif rsi > 60 or rsi < 40 or change > 3:
            return 'Medium'
        else:
            return 'Low'
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    # =========================================================================
    # MASTER REPORT GENERATOR
    # =========================================================================
    
    def generate_all_reports(self) -> Dict[str, str]:
        """
        Generate all comprehensive reports.
        
        Returns: Dictionary of report names to file paths
        """
        print("📊 Generating comprehensive CSV reports...")
        
        reports = {}
        
        print("  → Daily Stock Analysis...")
        reports['daily_analysis'] = self.generate_daily_stock_analysis_csv()
        
        print("  → Sector Analysis...")
        reports['sector_analysis'] = self.generate_sector_analysis_csv()
        
        print("  → Top Opportunities...")
        reports['opportunities'] = self.generate_top_opportunities_csv()
        
        print("  → Risk Alerts...")
        reports['risk_alerts'] = self.generate_risk_alerts_csv()
        
        print(f"✅ Generated {len(reports)} CSV reports")
        
        return reports


# Singleton instance
report_generator = ProfessionalReportGenerator()


def generate_hourly_news_csv(news_data: Dict) -> str:
    """Generate hourly news CSV"""
    return report_generator.generate_hourly_news_csv(news_data)


def generate_all_daily_reports() -> Dict[str, str]:
    """Generate all daily reports"""
    return report_generator.generate_all_reports()


if __name__ == "__main__":
    print("=" * 60)
    print("PSX PROFESSIONAL CSV REPORT GENERATOR")
    print("=" * 60)
    
    reports = generate_all_daily_reports()
    
    print("\n📁 Reports generated:")
    for name, path in reports.items():
        print(f"  • {name}: {os.path.basename(path)}")
