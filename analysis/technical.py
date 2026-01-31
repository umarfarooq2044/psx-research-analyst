"""
PSX Research Analyst - Enhanced Technical Analysis
Comprehensive technical indicators: RSI, MACD, Bollinger Bands, Moving Averages,
Support/Resistance, Volume Analysis, and Trend Detection
"""
from typing import List, Dict, Optional, Tuple
import os
import sys
import math
import pandas as pd # Optimized math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    RSI_PERIOD, VOLUME_SPIKE_MULTIPLIER, VOLUME_AVERAGE_DAYS,
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    MA_SHORT, MA_MEDIUM, MA_LONG,
    MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BOLLINGER_PERIOD, BOLLINGER_STD
)
from database.db_manager import db


# ============================================================================
# MOVING AVERAGES (VECTORIZED)
# ============================================================================

def calculate_moving_averages(prices: List[float]) -> Dict:
    """Calculate all moving averages using pandas (Vectorized)"""
    if not prices or len(prices) < MA_SHORT:
        return {'ma_10': None, 'ma_50': None, 'ma_200': None, 'ema_10': None, 'ema_50': None}
    
    # Create Series (reverse to chronological for pandas calculation)
    # Input prices are [newest, ..., oldest]
    # Pandas needs [oldest, ..., newest]
    series = pd.Series(prices[::-1])
    
    ma_10 = series.rolling(window=MA_SHORT).mean().iloc[-1]
    ma_50 = series.rolling(window=MA_MEDIUM).mean().iloc[-1]
    ma_200 = series.rolling(window=MA_LONG).mean().iloc[-1]
    
    ema_10 = series.ewm(span=MA_SHORT, adjust=False).mean().iloc[-1]
    ema_50 = series.ewm(span=MA_MEDIUM, adjust=False).mean().iloc[-1]
    
    return {
        'ma_10': round(ma_10, 2) if not pd.isna(ma_10) else None,
        'ma_50': round(ma_50, 2) if not pd.isna(ma_50) else None,
        'ma_200': round(ma_200, 2) if not pd.isna(ma_200) else None,
        'ema_10': round(ema_10, 2) if not pd.isna(ema_10) else None,
        'ema_50': round(ema_50, 2) if not pd.isna(ema_50) else None
    }

# ============================================================================
# RSI (VECTORIZED)
# ============================================================================

def calculate_rsi(prices: List[float], period: int = RSI_PERIOD) -> Optional[float]:
    """Calculate RSI using pandas (Vectorized)"""
    if not prices or len(prices) < period + 1:
        return None
    
    # Chronological order
    series = pd.Series(prices[::-1])
    delta = series.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    val = rsi.iloc[-1]
    return round(val, 2) if not pd.isna(val) else 50.0


# ============================================================================
# MACD
# ============================================================================

# ============================================================================
# MACD (VECTORIZED)
# ============================================================================

def calculate_macd(prices: List[float]) -> Dict:
    """Calculate MACD using pandas (Vectorized)"""
    if not prices or len(prices) < MACD_SLOW + MACD_SIGNAL:
        return {'macd': None, 'signal': None, 'histogram': None, 'trend': None}
        
    series = pd.Series(prices[::-1])
    
    exp1 = series.ewm(span=MACD_FAST, adjust=False).mean()
    exp2 = series.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    histogram = macd - signal
    
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]
    hist_val = histogram.iloc[-1]
    
    # Determine trend
    if macd_val > signal_val and macd_val > 0:
        trend = 'bullish'
    elif macd_val < signal_val and macd_val < 0:
        trend = 'bearish'
    elif macd_val > signal_val:
        trend = 'turning_bullish'
    else:
        trend = 'turning_bearish'
        
    return {
        'macd': round(macd_val, 2),
        'signal': round(signal_val, 2),
        'histogram': round(hist_val, 2),
        'trend': trend
    }


# ============================================================================
# BOLLINGER BANDS
# ============================================================================

# ============================================================================
# BOLLINGER BANDS (VECTORIZED)
# ============================================================================

def calculate_bollinger_bands(prices: List[float], period: int = BOLLINGER_PERIOD, 
                              std_dev: int = BOLLINGER_STD) -> Dict:
    """Calculate Bollinger Bands using pandas (Vectorized)"""
    if not prices or len(prices) < period:
        return {
            'upper': None, 'middle': None, 'lower': None,
            'bandwidth': None, 'position': None, 'signal': None
        }
        
    series = pd.Series(prices[::-1])
    
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    upper_val = upper.iloc[-1]
    lower_val = lower.iloc[-1]
    middle_val = middle.iloc[-1]
    
    # Calculate additional metrics
    if not pd.isna(middle_val) and middle_val != 0:
        bandwidth = round((upper_val - lower_val) / middle_val * 100, 2)
    else:
        bandwidth = None
        
    current_price = prices[0]
    if upper_val != lower_val:
        position = round((current_price - lower_val) / (upper_val - lower_val) * 100, 2)
    else:
        position = 50
        
    # Determine signal
    if position < 5:
        signal = 'oversold'
    elif position > 95:
        signal = 'overbought'
    elif position < 20:
        signal = 'near_lower'
    elif position > 80:
        signal = 'near_upper'
    else:
        signal = 'neutral'
        
    return {
        'upper': round(upper_val, 2) if not pd.isna(upper_val) else None,
        'middle': round(middle_val, 2) if not pd.isna(middle_val) else None,
        'lower': round(lower_val, 2) if not pd.isna(lower_val) else None,
        'bandwidth': bandwidth,
        'position': position,
        'signal': signal
    }


# ============================================================================
# VOLUME ANALYSIS
# ============================================================================

def detect_volume_spike(current_volume: int, avg_volume: float,
                        multiplier: float = VOLUME_SPIKE_MULTIPLIER) -> bool:
    """Detect if current volume is a spike compared to average"""
    if not avg_volume or avg_volume == 0:
        return False
    return current_volume > (avg_volume * multiplier)


def calculate_volume_ratio(current_volume: int, avg_volume: float) -> float:
    """Calculate ratio of current volume to average volume"""
    if not avg_volume or avg_volume == 0:
        return 0
    return round(current_volume / avg_volume, 2)


def analyze_volume(volumes: List[int], current_volume: int) -> Dict:
    """Comprehensive volume analysis"""
    if not volumes:
        return {'avg_volume': 0, 'volume_ratio': 0, 'volume_trend': 'unknown', 'spike': False}
    
    avg_volume = sum(volumes[:VOLUME_AVERAGE_DAYS]) / min(len(volumes), VOLUME_AVERAGE_DAYS)
    volume_ratio = calculate_volume_ratio(current_volume, avg_volume)
    spike = detect_volume_spike(current_volume, avg_volume)
    
    # Volume trend
    if len(volumes) >= 5:
        recent_avg = sum(volumes[:5]) / 5
        older_avg = sum(volumes[5:10]) / min(len(volumes[5:10]), 5) if len(volumes) > 5 else recent_avg
        if recent_avg > older_avg * 1.2:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'unknown'
    
    return {
        'avg_volume': avg_volume,
        'volume_ratio': volume_ratio,
        'volume_trend': trend,
        'spike': spike
    }


# ============================================================================
# SUPPORT & RESISTANCE
# ============================================================================

def check_support_resistance(current_price: float, high_52w: float, low_52w: float) -> Dict:
    """Check price position relative to 52-week high/low"""
    result = {
        'distance_from_high': 0,
        'distance_from_low': 0,
        'near_support': False,
        'near_resistance': False,
        'below_support': False,
        'above_resistance': False
    }
    
    if not high_52w or not low_52w or not current_price:
        return result
    
    if high_52w > 0:
        result['distance_from_high'] = round(((high_52w - current_price) / high_52w) * 100, 2)
        result['near_resistance'] = result['distance_from_high'] <= 5
        result['above_resistance'] = current_price > high_52w
    
    if low_52w > 0:
        result['distance_from_low'] = round(((current_price - low_52w) / low_52w) * 100, 2)
        result['near_support'] = result['distance_from_low'] <= 5
        result['below_support'] = current_price < low_52w
    
    return result


def calculate_pivot_points(high: float, low: float, close: float) -> Dict:
    """Calculate pivot points for support/resistance"""
    if not all([high, low, close]):
        return {}
    
    pivot = (high + low + close) / 3
    
    return {
        'pivot': round(pivot, 2),
        'r1': round(2 * pivot - low, 2),
        'r2': round(pivot + (high - low), 2),
        's1': round(2 * pivot - high, 2),
        's2': round(pivot - (high - low), 2)
    }


# ============================================================================
# TREND DETECTION
# ============================================================================

def detect_trend(prices: List[float], ma_10: float, ma_50: float, ma_200: float) -> Dict:
    """
    Detect price trend using multiple methods
    """
    if not prices or len(prices) < 2:
        return {'trend': 'unknown', 'strength': 0, 'description': 'Insufficient data'}
    
    current_price = prices[0]
    trend_signals = []
    
    # Price vs Moving Averages
    if ma_10 and current_price > ma_10:
        trend_signals.append(1)
    elif ma_10:
        trend_signals.append(-1)
    
    if ma_50 and current_price > ma_50:
        trend_signals.append(1)
    elif ma_50:
        trend_signals.append(-1)
    
    if ma_200 and current_price > ma_200:
        trend_signals.append(1)
    elif ma_200:
        trend_signals.append(-1)
    
    # MA alignment (Golden/Death Cross)
    if ma_10 and ma_50:
        if ma_10 > ma_50:
            trend_signals.append(1)
        else:
            trend_signals.append(-1)
    
    if ma_50 and ma_200:
        if ma_50 > ma_200:
            trend_signals.append(1)
        else:
            trend_signals.append(-1)
    
    # Calculate overall trend
    if not trend_signals:
        return {'trend': 'unknown', 'strength': 0, 'description': 'Insufficient data'}
    
    avg_signal = sum(trend_signals) / len(trend_signals)
    
    if avg_signal > 0.6:
        trend = 'strong_uptrend'
        description = 'Strong bullish trend - price above all MAs'
    elif avg_signal > 0.2:
        trend = 'uptrend'
        description = 'Moderate uptrend'
    elif avg_signal < -0.6:
        trend = 'strong_downtrend'
        description = 'Strong bearish trend - price below all MAs'
    elif avg_signal < -0.2:
        trend = 'downtrend'
        description = 'Moderate downtrend'
    else:
        trend = 'consolidating'
        description = 'Sideways/consolidating market'
    
    return {
        'trend': trend,
        'strength': round(abs(avg_signal) * 100, 0),
        'description': description
    }


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def analyze_ticker_technical(symbol: str) -> Optional[Dict]:
    """
    Perform comprehensive technical analysis for a ticker
    Returns dict with all technical indicators
    """
    # Get price history (200+ days for all MAs)
    history = db.get_price_history(symbol, days=250)
    
    if not history or len(history) < 2:
        return None
    
    # Extract data
    latest = history[0]
    current_price = latest.get('close_price', 0)
    current_volume = latest.get('volume', 0)
    current_high = latest.get('high_price', current_price)
    current_low = latest.get('low_price', current_price)
    
    closing_prices = [h['close_price'] for h in history if h.get('close_price')]
    volumes = [h['volume'] for h in history if h.get('volume')]
    
    # Calculate all indicators
    
    # 1. Moving Averages
    mas = calculate_moving_averages(closing_prices)
    
    # 2. RSI
    rsi = calculate_rsi(closing_prices, RSI_PERIOD)
    
    # 3. MACD
    macd_data = calculate_macd(closing_prices)
    
    # 4. Bollinger Bands
    bollinger = calculate_bollinger_bands(closing_prices)
    
    # 5. Volume Analysis
    volume_analysis = analyze_volume(volumes, current_volume)
    
    # 6. 52-Week High/Low
    high_52w, low_52w = db.get_52_week_high_low(symbol)
    
    # 7. Support/Resistance
    sr_analysis = check_support_resistance(current_price, high_52w, low_52w)
    
    # 8. Pivot Points
    pivots = calculate_pivot_points(current_high, current_low, current_price)
    
    # 9. Trend Detection
    trend = detect_trend(closing_prices, mas.get('ma_10'), mas.get('ma_50'), mas.get('ma_200'))
    
    # Generate signals
    signals = []
    
    if rsi is not None:
        if rsi < RSI_OVERSOLD:
            signals.append(f"RSI Oversold ({rsi:.1f})")
        elif rsi > RSI_OVERBOUGHT:
            signals.append(f"RSI Overbought ({rsi:.1f})")
    
    if volume_analysis['spike']:
        signals.append(f"Volume Spike ({volume_analysis['volume_ratio']:.1f}x)")
    
    if bollinger['signal'] == 'oversold':
        signals.append("Below Bollinger Lower Band")
    elif bollinger['signal'] == 'overbought':
        signals.append("Above Bollinger Upper Band")
    
    if macd_data['trend'] == 'bullish':
        signals.append("MACD Bullish")
    elif macd_data['trend'] == 'bearish':
        signals.append("MACD Bearish")
    
    if sr_analysis['near_support']:
        signals.append("Near 52W Support")
    elif sr_analysis['near_resistance']:
        signals.append("Near 52W Resistance")
    
    if sr_analysis['below_support']:
        signals.append("BROKE 52W Support!")
    elif sr_analysis['above_resistance']:
        signals.append("NEW 52W High!")
    
    # Save to database
    db.save_technical_indicators(symbol, {
        'ma_10': mas.get('ma_10'),
        'ma_50': mas.get('ma_50'),
        'ma_200': mas.get('ma_200'),
        'rsi': rsi,
        'macd': macd_data.get('macd'),
        'macd_signal': macd_data.get('signal'),
        'macd_histogram': macd_data.get('histogram'),
        'bollinger_upper': bollinger.get('upper'),
        'bollinger_middle': bollinger.get('middle'),
        'bollinger_lower': bollinger.get('lower'),
        'support_level': low_52w,
        'resistance_level': high_52w,
        'trend': trend.get('trend')
    })
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'current_volume': current_volume,
        'rsi': rsi,
        'moving_averages': mas,
        'macd': macd_data,
        'bollinger': bollinger,
        'volume_analysis': volume_analysis,
        'high_52w': high_52w,
        'low_52w': low_52w,
        'support_resistance': sr_analysis,
        'pivots': pivots,
        'trend': trend,
        'signals': signals,
        'is_oversold': rsi < RSI_OVERSOLD if rsi else False,
        'is_overbought': rsi > RSI_OVERBOUGHT if rsi else False
    }


def get_technical_score(analysis: Dict) -> int:
    """
    Convert technical analysis to a score (0-5)
    Higher score = more bullish
    """
    if not analysis:
        return 3
    
    score = 3  # Start neutral
    
    # RSI component
    rsi = analysis.get('rsi')
    if rsi is not None:
        if rsi < 30:
            score += 2
        elif rsi < RSI_OVERSOLD:
            score += 1
        elif rsi > 80:
            score -= 2
        elif rsi > RSI_OVERBOUGHT:
            score -= 1
    
    # MACD component
    macd = analysis.get('macd', {})
    if macd.get('trend') == 'bullish':
        score += 1
    elif macd.get('trend') == 'bearish':
        score -= 1
    
    # Trend component
    trend = analysis.get('trend', {})
    if trend.get('trend') in ['uptrend', 'strong_uptrend']:
        score += 1
    elif trend.get('trend') in ['downtrend', 'strong_downtrend']:
        score -= 1
    
    # Volume spike
    if analysis.get('volume_analysis', {}).get('spike'):
        score += 0.5
    
    # Support/Resistance
    sr = analysis.get('support_resistance', {})
    if sr.get('near_support') and not sr.get('below_support'):
        score += 1
    elif sr.get('below_support'):
        score -= 2
    elif sr.get('above_resistance'):
        score += 1
    
    return max(0, min(5, int(round(score))))


def get_technical_score_20(analysis: Dict) -> int:
    """
    Get technical score out of 20 for 100-point stock scoring system
    """
    if not analysis:
        return 10  # Neutral
    
    score = 10  # Start neutral
    
    # RSI (0-4 points)
    rsi = analysis.get('rsi')
    if rsi is not None:
        if rsi < 30:
            score += 4
        elif rsi < 40:
            score += 2
        elif rsi > 80:
            score -= 4
        elif rsi > 70:
            score -= 2
    
    # Trend (0-4 points)
    trend = analysis.get('trend', {})
    trend_name = trend.get('trend', '')
    if trend_name == 'strong_uptrend':
        score += 4
    elif trend_name == 'uptrend':
        score += 2
    elif trend_name == 'strong_downtrend':
        score -= 4
    elif trend_name == 'downtrend':
        score -= 2
    
    # MACD (0-3 points)
    macd = analysis.get('macd', {})
    if macd.get('trend') == 'bullish':
        score += 3
    elif macd.get('trend') == 'turning_bullish':
        score += 1
    elif macd.get('trend') == 'bearish':
        score -= 3
    elif macd.get('trend') == 'turning_bearish':
        score -= 1
    
    # Volume (0-2 points)
    vol = analysis.get('volume_analysis', {})
    if vol.get('spike') and vol.get('volume_trend') == 'increasing':
        score += 2
    elif vol.get('volume_trend') == 'increasing':
        score += 1
    elif vol.get('volume_trend') == 'decreasing':
        score -= 1
    
    # Bollinger (0-2 points)
    bb = analysis.get('bollinger', {})
    if bb.get('signal') == 'oversold':
        score += 2
    elif bb.get('signal') == 'overbought':
        score -= 2
    
    return max(0, min(20, score))


if __name__ == "__main__":
    # Test with sample tickers
    test_symbols = ["MARI", "OGDC", "HBL"]
    
    for symbol in test_symbols:
        analysis = analyze_ticker_technical(symbol)
        if analysis:
            print(f"\n{'='*50}")
            print(f"{symbol} COMPREHENSIVE TECHNICAL ANALYSIS")
            print(f"{'='*50}")
            print(f"Price: Rs. {analysis['current_price']:.2f}")
            print(f"\nMoving Averages:")
            mas = analysis['moving_averages']
            print(f"  10-DMA: {mas.get('ma_10')}")
            print(f"  50-DMA: {mas.get('ma_50')}")
            print(f"  200-DMA: {mas.get('ma_200')}")
            print(f"\nRSI(14): {analysis['rsi']}")
            print(f"\nMACD:")
            macd = analysis['macd']
            print(f"  Line: {macd.get('macd')}")
            print(f"  Signal: {macd.get('signal')}")
            print(f"  Trend: {macd.get('trend')}")
            print(f"\nBollinger Bands:")
            bb = analysis['bollinger']
            print(f"  Upper: {bb.get('upper')}")
            print(f"  Middle: {bb.get('middle')}")
            print(f"  Lower: {bb.get('lower')}")
            print(f"  Signal: {bb.get('signal')}")
            print(f"\nTrend: {analysis['trend']}")
            print(f"\nSignals: {analysis['signals']}")
            print(f"\nTechnical Score: {get_technical_score(analysis)}/5")
            print(f"Technical Score (20pt): {get_technical_score_20(analysis)}/20")
        else:
            print(f"\n{symbol}: Not enough data for analysis")
