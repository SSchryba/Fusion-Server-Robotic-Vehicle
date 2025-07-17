import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class FusionInsight:
    """
    FusionInsight: Logs model outputs, feedback, and self-reflection for compound optimization.
    Provides hooks for feedback, meta-learning, and recursive self-improvement.
    """
    def __init__(self, log_file: str = "fusion_insight.log"):
        self.log_file = log_file
        self.logs: List[Dict[str, Any]] = []
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def log_model_output(self, model: str, prompt: str, response: str, score: float, meta: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt": prompt,
            "response": response,
            "score": score,
            "meta": meta or {}
        }
        self.logs.append(entry)
        self._persist(entry)

    def log_feedback(self, model: str, feedback: str, rating: Optional[float] = None, user: Optional[str] = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "feedback": feedback,
            "rating": rating,
            "user": user
        }
        self.logs.append(entry)
        self._persist(entry)

    def log_self_reflection(self, model: str, reflection: str, context: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "reflection": reflection,
            "context": context or {}
        }
        self.logs.append(entry)
        self._persist(entry)

    def _persist(self, entry: Dict[str, Any]):
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"{entry}\n")
        except Exception as e:
            logging.error(f"Failed to persist FusionInsight log: {e}")

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.logs[-limit:] 