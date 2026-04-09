from server.config import INTENTS

def classify_intent(query: str) -> tuple[str, float]:
    words = set(query.lower().split())
    best_intent = "general"
    best_score = 0.0
    for intent, keywords in INTENTS.items():
        matches = words.intersection(keywords)
        if not keywords:
            continue
        score = len(matches) / len(keywords)
        if matches:
            score = max(score, len(matches) / max(len(words), 1))
        if score > best_score:
            best_score = score
            best_intent = intent
    if best_score < 0.08:
        return "general", 0.5
    return best_intent, min(best_score * 2, 1.0)
