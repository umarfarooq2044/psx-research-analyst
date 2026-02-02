import logging
import json
import os
from datetime import datetime

class StructuredLogger:
    """
    SMI-v2 Professional Logging System.
    Outputs logs in JSON format for easy ingestion and auditing.
    """
    
    def __init__(self, name="AI_ENGINE"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # File Handler (JSON)
        log_file = os.path.join(log_dir, f"{name.lower()}_{datetime.now().strftime('%Y%m%d')}.log")
        fh = logging.FileHandler(log_file)
        self.logger.addHandler(fh)
        
        # Console Handler (Simple)
        ch = logging.StreamHandler()
        self.logger.addHandler(ch)

    def info(self, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": message,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))

    def error(self, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": message,
            **kwargs
        }
        self.logger.error(json.dumps(log_entry))

    def signal(self, symbol: str, signal: str, confidence: int, reason: str):
        """Specialized logger for AI signals"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "TRADING_SIGNAL",
            "symbol": symbol,
            "signal": signal,
            "confidence": f"{confidence}%",
            "reason": reason
        }
        self.logger.info(json.dumps(log_entry))

# Global Logger
smi_logger = StructuredLogger()
