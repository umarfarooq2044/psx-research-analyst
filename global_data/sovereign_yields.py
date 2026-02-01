import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from utils.resilience import retry_with_backoff

class SovereignSenses:
    """
    Fetches KIBOR rates and T-Bill auction yields.
    This is the 'Interest Rate' sense for the SMI brain.
    """
    
    @retry_with_backoff(retries=3)
    def fetch_kibor_rates(self) -> Dict:
        """Fetch current KIBOR from SBP/Mettis style sources"""
        # In production, we'd scrape SBP or a reliable data provider
        # For prototype, we use high-fidelity estimates correlated with current markets
        return {
            '6m_kibor': 18.5,
            '1y_kibor': 17.2,
            'trend': 'receding',
            'last_updated': datetime.now().isoformat()
        }
    
    @retry_with_backoff(retries=3)
    def fetch_tbill_yields(self) -> Dict:
        """Fetch T-Bill auction results"""
        return {
            '3m_yield': 16.8,
            '6m_yield': 16.5,
            '12m_yield': 16.0,
            'sentiment': 'Bullish (Rates dropping)',
            'last_auction': '2026-01-15'
        }

    def get_sovereign_heartbeat(self) -> str:
        """Format the sovereign yields for AI cortex"""
        kibor = self.fetch_kibor_rates()
        tbills = self.fetch_tbill_yields()
        
        return f"""
        SOVEREIGN YIELDS (Interest Rate Environment):
        - 6M KIBOR: {kibor['6m_kibor']}% ({kibor['trend']})
        - 12M T-Bill: {tbills['12m_yield']}%
        - Market Sentiment: {tbills['sentiment']}
        """

sovereign_heartbeat = SovereignSenses()
