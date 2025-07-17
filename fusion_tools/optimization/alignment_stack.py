from typing import Dict, Any, List

class AlignmentStack:
    """
    Implements RLHF, Direct Preference Optimization (DPO), and KTO-inspired emotional loss aversion for alignment.
    """
    def __init__(self):
        self.preference_history: List[Dict[str, Any]] = []

    def record_preference(self, model: str, response: str, preferred: bool, reason: str = ""):
        self.preference_history.append({
            "model": model,
            "response": response,
            "preferred": preferred,
            "reason": reason
        })

    def compute_alignment_score(self, model: str) -> float:
        # Placeholder: Score based on preference history
        prefs = [p for p in self.preference_history if p['model'] == model]
        if not prefs:
            return 0.5
        return sum(1.0 if p['preferred'] else 0.0 for p in prefs) / len(prefs)

    def emotional_loss_aversion(self, response: str) -> float:
        # Placeholder: Penalize emotionally negative responses
        negative_keywords = ["angry", "sad", "frustrated", "annoyed"]
        penalty = any(word in response.lower() for word in negative_keywords)
        return -1.0 if penalty else 0.0 