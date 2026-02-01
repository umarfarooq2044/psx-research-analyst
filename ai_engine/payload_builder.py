from datetime import datetime
from typing import List, Dict
from global_data.sovereign_yields import sovereign_heartbeat
from analysis.future_mapper import future_mapper

def build_market_payload(tickers_data: List[Dict], news_data: List[Dict]) -> str:
    """
    Construct a massive high-frequency snapshot for SMI-v1.
    Triangulates Senses (Ticks) + Context (Macro) + Simulation (Monte Carlo).
    """
    sovereign_context = sovereign_heartbeat.get_sovereign_heartbeat()
    
    # Run simulations for the top movers provided in batch
    symbols = [t['symbol'] for t in tickers_data[:10]]
    future_map = future_mapper.get_market_future_map(symbols)
    
    payload = f"SMI-v1 COGNITIVE SNAPSHOT | TIMESTAMP: {datetime.now().isoformat()}\n"
    payload += "="*60 + "\n"
    payload += f"{sovereign_context}\n"
    payload += f"{future_map}\n"
    
    payload += "\n--- TICKER DATA (Senses) ---\n"
    payload += "Sym | Price | Vol | Change%\n"
    for t in tickers_data:
        payload += f"{t['symbol']} | {t.get('close_price', 0):.2f} | {t.get('volume', 0):,} | {t.get('change_percent', 0):.2f}%\n"
        
    payload += "\n--- NEWS STREAM ---\n"
    for n in news_data[:15]:
        payload += f"- {n['headline']} ({n['source']})\n"
        
    return payload
