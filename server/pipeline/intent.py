from server.config import INTENTS

# Additional persuasion-relevant intents
PERSUASION_INTENTS = {
    "objection": ["expensive", "costly", "far", "distance", "not sure", "doubt", "better", "other college", "confused", "compare", "worth", "waste"],
    "comparison": ["vs", "versus", "compared", "better than", "difference", "anna university", "srm", "vit", "sairam", "saveetha", "other"],
    "commitment": ["apply", "join", "register", "enroll", "admit", "interested", "want to join", "ready", "confirm", "sign up"],
    "personal": ["name", "my name", "call me", "i am", "i'm from", "i live", "my goal", "my dream", "i want to become"],
    "parent_concern": ["parent", "father", "mother", "amma", "appa", "family", "safe", "security", "worried"],
    "scholarship_need": ["scholarship", "financial", "poor", "afford", "discount", "free seat", "help", "support", "concession"],
    "campus_visit": ["visit", "come", "see", "tour", "campus visit", "look around", "when can i come"],
}


def classify_intent(query: str) -> tuple[str, float]:
    words = set(query.lower().split())
    query_lower = query.lower()

    best_intent = "general"
    best_score = 0.0

    # Check standard intents
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

    # Check persuasion intents (override if stronger)
    for intent, keywords in PERSUASION_INTENTS.items():
        matches = sum(1 for kw in keywords if kw in query_lower)
        if not keywords:
            continue
        score = matches / len(keywords)
        if matches:
            score = max(score, matches / max(len(words), 1))
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score < 0.08:
        return "out_of_scope", 0.5
    return best_intent, min(best_score * 2, 1.0)


def extract_interests(query: str) -> list[str]:
    """Extract mentioned course/career interests from query."""
    interest_keywords = {
        "cse": "Computer Science", "computer science": "Computer Science",
        "ece": "Electronics", "electronics": "Electronics",
        "mech": "Mechanical", "mechanical": "Mechanical",
        "civil": "Civil", "eee": "Electrical",
        "it": "Information Technology", "ai": "Artificial Intelligence",
        "data science": "Data Science", "cyber": "Cyber Security",
        "robotics": "Robotics", "iot": "IoT",
        "software": "Software Engineering", "btech": "B.Tech",
        "mtech": "M.Tech", "mba": "MBA",
        "engineer": "Engineering", "doctor": "Doctor",
        "developer": "Software Developer", "placement": "Placements",
        "job": "Career/Job", "salary": "Good Salary",
        "startup": "Entrepreneurship", "research": "Research",
        "abroad": "Study Abroad", "ms": "MS/Higher Studies",
    }
    query_lower = query.lower()
    found = []
    for keyword, label in interest_keywords.items():
        if keyword in query_lower and label not in found:
            found.append(label)
    return found
