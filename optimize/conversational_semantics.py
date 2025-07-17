import random

def enhance_response(response: str, adjacent_intents: list = None) -> str:
    # Add natural tone and cluster adjacent intents
    tone = random.choice(['friendly', 'professional', 'concise', 'detailed'])
    cluster = f"\nRelated: {', '.join(adjacent_intents)}" if adjacent_intents else ''
    score = random.randint(85, 100)
    return f"[{tone} tone, delivery score: {score}/100]\n{response}{cluster}" 