"""
PSX Research Analyst - Real-Time Alert System
Sends alerts via Email and Telegram for important market events
"""
import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS,
    TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    ALERT_THRESHOLDS
)
from database.db_manager import db


class AlertManager:
    """Manages real-time alerts via multiple channels"""
    
    def __init__(self):
        self.email_enabled = bool(EMAIL_SENDER and EMAIL_PASSWORD)
        self.telegram_enabled = TELEGRAM_ENABLED and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
    
    # ==================== EMAIL ALERTS ====================
    
    def send_email_alert(self, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email alert"""
        if not self.email_enabled:
            print("Email alerts not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 PSX ALERT: {subject}"
            msg['From'] = EMAIL_SENDER
            msg['To'] = ", ".join(EMAIL_RECIPIENTS)
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False
    
    # ==================== TELEGRAM ALERTS ====================
    
    def send_telegram_alert(self, message: str) -> bool:
        """Send Telegram alert"""
        if not self.telegram_enabled:
            print("Telegram alerts not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Telegram alert failed: {e}")
            return False
    
    # ==================== ALERT TYPES ====================
    
    def alert_price_spike(self, symbol: str, price: float, change_percent: float, 
                          direction: str = 'up') -> bool:
        """Alert on significant price movement"""
        
        threshold = ALERT_THRESHOLDS.get('price_move', 5)
        
        if abs(change_percent) < threshold:
            return False
        
        emoji = "🚀" if direction == 'up' else "📉"
        
        subject = f"{symbol} {emoji} {'+' if change_percent > 0 else ''}{change_percent:.2f}%"
        
        message = f"""
        <b>{emoji} PRICE ALERT: {symbol}</b>
        
        Price: Rs. {price:,.2f}
        Change: {'+' if change_percent > 0 else ''}{change_percent:.2f}%
        
        Time: {datetime.now().strftime('%I:%M %p')}
        """
        
        # Save to database
        db.save_alert(
            alert_type='price_spike',
            symbol=symbol,
            message=f"{symbol} moved {change_percent:.2f}%",
            trigger_value=change_percent,
            threshold_value=threshold
        )
        
        # Send alerts
        email_sent = self.send_email_alert(subject, message.strip(), is_html=True)
        telegram_sent = self.send_telegram_alert(message.strip())
        
        return email_sent or telegram_sent
    
    def alert_volume_spike(self, symbol: str, volume: int, avg_volume: float,
                           volume_ratio: float) -> bool:
        """Alert on unusual volume"""
        
        threshold = ALERT_THRESHOLDS.get('volume_spike', 2.0)
        
        if volume_ratio < threshold:
            return False
        
        subject = f"{symbol} Volume Spike {volume_ratio:.1f}x"
        
        message = f"""
        <b>📊 VOLUME ALERT: {symbol}</b>
        
        Current Volume: {volume:,}
        Average Volume: {avg_volume:,.0f}
        Volume Ratio: {volume_ratio:.1f}x average
        
        ⚡ Unusual activity detected!
        
        Time: {datetime.now().strftime('%I:%M %p')}
        """
        
        db.save_alert(
            alert_type='volume_spike',
            symbol=symbol,
            message=f"{symbol} volume {volume_ratio:.1f}x average",
            trigger_value=volume_ratio,
            threshold_value=threshold
        )
        
        email_sent = self.send_email_alert(subject, message.strip(), is_html=True)
        telegram_sent = self.send_telegram_alert(message.strip())
        
        return email_sent or telegram_sent
    
    def alert_support_break(self, symbol: str, price: float, support_level: float,
                            is_breakdown: bool = True) -> bool:
        """Alert on support/resistance break"""
        
        subject = f"{symbol} {'BREAKDOWN' if is_breakdown else 'BREAKOUT'}!"
        emoji = "⚠️" if is_breakdown else "🎯"
        
        message = f"""
        <b>{emoji} {'SUPPORT BREAK' if is_breakdown else 'RESISTANCE BREAK'}: {symbol}</b>
        
        Price: Rs. {price:,.2f}
        {'Support' if is_breakdown else 'Resistance'} Level: Rs. {support_level:,.2f}
        
        {'⚠️ CAUTION: Price broke below key support!' if is_breakdown else '🎯 BULLISH: Price broke above resistance!'}
        
        Time: {datetime.now().strftime('%I:%M %p')}
        """
        
        db.save_alert(
            alert_type='support_break' if is_breakdown else 'resistance_break',
            symbol=symbol,
            message=f"{symbol} broke {'support' if is_breakdown else 'resistance'} at {support_level}",
            trigger_value=price,
            threshold_value=support_level
        )
        
        email_sent = self.send_email_alert(subject, message.strip(), is_html=True)
        telegram_sent = self.send_telegram_alert(message.strip())
        
        return email_sent or telegram_sent
    
    def alert_kse100_level(self, current_value: float, level: float, 
                           level_type: str = 'support') -> bool:
        """Alert on KSE-100 key level breach"""
        
        is_breakdown = level_type == 'support' and current_value < level
        is_breakout = level_type == 'resistance' and current_value > level
        
        if not (is_breakdown or is_breakout):
            return False
        
        subject = f"KSE-100 {'BROKE SUPPORT' if is_breakdown else 'BROKE RESISTANCE'}"
        emoji = "🔴" if is_breakdown else "🟢"
        
        message = f"""
        <b>{emoji} KSE-100 ALERT</b>
        
        Current Level: {current_value:,.0f}
        {level_type.title()}: {level:,.0f}
        
        {'⚠️ Index broke below support - bearish signal' if is_breakdown else '🎯 Index broke above resistance - bullish signal'}
        
        Time: {datetime.now().strftime('%I:%M %p')}
        """
        
        db.save_alert(
            alert_type=f'kse100_{level_type}_break',
            symbol='KSE100',
            message=f"KSE-100 broke {level_type} at {level:,.0f}",
            trigger_value=current_value,
            threshold_value=level
        )
        
        email_sent = self.send_email_alert(subject, message.strip(), is_html=True)
        telegram_sent = self.send_telegram_alert(message.strip())
        
        return email_sent or telegram_sent
    
    def alert_high_score_stock(self, symbol: str, score: int, rating: str,
                               price: float) -> bool:
        """Alert on high-scoring stock opportunity"""
        
        if score < 80:  # Only alert on very high scores
            return False
        
        subject = f"🎯 TOP PICK: {symbol} - Score {score}/100"
        
        message = f"""
        <b>🎯 HIGH SCORE ALERT: {symbol}</b>
        
        Score: {score}/100
        Rating: <b>{rating}</b>
        Price: Rs. {price:,.2f}
        
        ✨ This stock scored exceptionally high in our 100-point analysis!
        
        Time: {datetime.now().strftime('%I:%M %p')}
        """
        
        db.save_alert(
            alert_type='high_score',
            symbol=symbol,
            message=f"{symbol} scored {score}/100",
            trigger_value=score,
            threshold_value=80
        )
        
        email_sent = self.send_email_alert(subject, message.strip(), is_html=True)
        telegram_sent = self.send_telegram_alert(message.strip())
        
        return email_sent or telegram_sent
    
    def alert_custom(self, title: str, message: str, alert_type: str = 'custom') -> bool:
        """Send a custom alert"""
        
        db.save_alert(
            alert_type=alert_type,
            message=message
        )
        
        email_sent = self.send_email_alert(title, f"<b>{title}</b>\n\n{message}", is_html=True)
        telegram_sent = self.send_telegram_alert(f"<b>{title}</b>\n\n{message}")
        
        return email_sent or telegram_sent


# Singleton instance
alert_manager = AlertManager()


def check_and_send_alerts(stock_data: Dict):
    """
    Check all alert conditions for a stock and send alerts
    
    Args:
        stock_data: Dict with symbol, price, change_percent, volume, etc.
    """
    symbol = stock_data.get('symbol')
    if not symbol:
        return
    
    # Check price spike
    change_percent = stock_data.get('change_percent', 0)
    if abs(change_percent) >= ALERT_THRESHOLDS.get('price_move', 5):
        direction = 'up' if change_percent > 0 else 'down'
        alert_manager.alert_price_spike(
            symbol, stock_data.get('price', 0), change_percent, direction
        )
    
    # Check volume spike
    volume_ratio = stock_data.get('volume_ratio', 0)
    if volume_ratio >= ALERT_THRESHOLDS.get('volume_spike', 2.0):
        alert_manager.alert_volume_spike(
            symbol,
            stock_data.get('volume', 0),
            stock_data.get('avg_volume', 0),
            volume_ratio
        )
    
    # Check support/resistance breaks
    sr = stock_data.get('support_resistance', {})
    if sr.get('below_support'):
        alert_manager.alert_support_break(
            symbol, stock_data.get('price', 0),
            stock_data.get('low_52w', 0), is_breakdown=True
        )
    elif sr.get('above_resistance'):
        alert_manager.alert_support_break(
            symbol, stock_data.get('price', 0),
            stock_data.get('high_52w', 0), is_breakdown=False
        )


if __name__ == "__main__":
    # Test alert system
    print("Testing Alert System...")
    
    manager = AlertManager()
    
    # Test custom alert
    manager.alert_custom(
        "Test Alert",
        "This is a test alert from PSX Research Analyst"
    )
    
    print("\nAlert test complete!")
