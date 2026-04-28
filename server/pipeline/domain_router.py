from server.config import DOMAINS

INTENT_TO_DOMAIN = {
    "greeting": ["basic_info"],
    "course_inquiry": ["courses"],
    "admission_inquiry": ["admission"],
    "fee_inquiry": ["fees"],
    "placement_inquiry": ["placements"],
    "hostel_inquiry": ["hostel"],
    "infrastructure_inquiry": ["infrastructure", "labs"],
    "faculty_inquiry": ["faculty"],
    "event_inquiry": ["events", "clubs"],
    "transport_inquiry": ["transport"],
    "ranking_inquiry": ["rankings"],
    "contact_inquiry": ["contact"],
    "general": ["basic_info"],
    # Persuasion intents → domain routing
    "objection": ["placements", "rankings", "fees"],
    "comparison": ["rankings", "placements", "basic_info"],
    "commitment": ["admission", "contact"],
    "personal": ["basic_info", "courses"],
    "parent_concern": ["health_safety", "hostel", "infrastructure"],
    "scholarship_need": ["fees", "admission"],
    "campus_visit": ["infrastructure", "contact", "events"],
}

def route_domain(query: str, intent: str) -> list[str]:
    domains = INTENT_TO_DOMAIN.get(intent, ["basic_info"])
    words = set(query.lower().split())
    scored = []
    for domain_name, domain_cfg in DOMAINS.items():
        overlap = len(words.intersection(domain_cfg["keywords"]))
        if overlap > 0:
            scored.append((domain_name, overlap))
    scored.sort(key=lambda x: x[1], reverse=True)
    if scored:
        result = [s[0] for s in scored[:2]]
        for d in domains:
            if d not in result:
                result.append(d)
        return result[:3]
    return domains[:2]
