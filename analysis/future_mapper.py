import numpy as np
import pandas as pd
from typing import Dict, List
from database.db_manager import db
from utils.resilience import safe_execute

class FutureMapper:
    """
    Runs Monte Carlo simulations to generate T+7 price probability maps.
    This is the 'Simulation' layer of the SMI-v1 brain.
    """
    
    @safe_execute(default_return={"range_90": "N/A", "drift": 0})
    def simulate_path(self, symbol: str, days: int = 7, simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo for a specific ticker.
        """
        latest = db.get_latest_price(symbol)
        if not latest: return {"range_90": "N/A", "drift": 0}
        
        current_price = latest['close_price']
        volatility = 0.02 # Default 2% daily vol (will pull from history in V2)
        
        # SBP/Macro Drift Factor
        # If rates are dropping, drift is positive
        drift = 0.001 # 0.1% daily drift
        
        # Stochastic Simulation
        # Price_t = Price_0 * exp((drift - 0.5 * vol^2) * t + vol * sqrt(t) * Z)
        # We simplify to a normal distribution on returns for speed
        returns = np.random.normal(drift, volatility, (simulations, days))
        final_prices = current_price * np.prod(1 + returns, axis=1)
        
        # Probability Map
        low_90 = np.percentile(final_prices, 5)
        high_90 = np.percentile(final_prices, 95)
        
        return {
            "symbol": symbol,
            "current": current_price,
            "range_90": f"{low_90:,.2f} - {high_90:,.2f}",
            "mean": np.mean(final_prices),
            "confidence": "High" if len(final_prices) > 500 else "Low"
        }

    def get_market_future_map(self, symbols: List[str]) -> str:
        """Generate simulation results for key leaders"""
        results = [self.simulate_path(s) for s in symbols]
        
        output = "--- MONTE CARLO FUTURE SIMULATIONS (T+7) ---\n"
        for r in results:
            if r['range_90'] != "N/A":
                output += f"Ticker: {r['symbol']} | Probable Range: {r['range_90']} | Drift: {'Positive' if r['mean'] > r['current'] else 'Negative'}\n"
        
        return output

future_mapper = FutureMapper()
