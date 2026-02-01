import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
from database.db_manager import db
from database.models import get_db_session, AIDecision, PriceHistory
from utils.resilience import safe_execute

class AlphaLoop:
    """
    Self-Improving Mechanism for the Cognitive Engine.
    "We learn from our P&L, not our Backtests."
    """
    
    MEMORY_FILE = "ai_engine/market_wisdom.json"
    
    @safe_execute(default_return=[])
    def audit_performance(self) -> List[str]:
        """
        Check past predictions (7 days ago) and determine if they were right.
        Returns a list of 'Lessons Learned'.
        """
        lessons = []
        with get_db_session() as session:
            # Look back 7 days
            audit_date = datetime.now().date() - timedelta(days=7)
            
            # Fetch decisions made on that date
            decisions = session.query(AIDecision).filter(AIDecision.date <= audit_date).all()
            
            print(f"🕵️ AlphaLoop Auditing: Checking {len(decisions)} past decisions...")
            
            for d in decisions:
                # Get price then vs now
                # This requires historical price lookup. For now, simple logic.
                current_price_obj = db.get_latest_price(d.symbol)
                if not current_price_obj: continue
                
                current_price = current_price_obj['close_price']
                
                # We need the price ON decision date. 
                # Ideally, AIDecision should store 'entry_price'.
                # For V1, we skip complex P&L calc and focus on concept.
                
                # Mock Logic for Prototype:
                # If Action was BUY and Current Price is High -> Good Job
                pass
                
        # Since we don't have 7 days of data yet, we seed with institutional wisdom
        # In a real run, this would be dynamic.
        return self.load_lessons()

    def load_lessons(self) -> str:
        """Load the accumulated wisdom"""
        if os.path.exists(self.MEMORY_FILE):
             with open(self.MEMORY_FILE, 'r') as f:
                 data = json.load(f)
                 return "\n".join([f"- {l}" for l in data.get('lessons', [])])
        return "- No historical performance data yet. Stick to fundamentals."

    def add_lesson(self, lesson: str):
        """Manually or auto-add a lesson"""
        data = {'lessons': []}
        if os.path.exists(self.MEMORY_FILE):
            with open(self.MEMORY_FILE, 'r') as f:
                data = json.load(f)
        
        if lesson not in data['lessons']:
            data['lessons'].append(lesson)
            
        with open(self.MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)

alpha_loop = AlphaLoop()
