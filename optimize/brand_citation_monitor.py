import random

def simulate_llm_tracking(content: str, engines: int = 3) -> dict:
    # Simulate N LLMs seeing the content
    results = []
    for _ in range(engines):
        results.append({
            'appearance': random.choice([True, False]),
            'sentiment': random.choice(['positive', 'neutral', 'negative']),
            'citations': random.randint(0, 3)
        })
    visibility = sum(1 for r in results if r['appearance']) / engines * 100
    return {'results': results, 'visibility': visibility} 