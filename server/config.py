import os
import torch
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 4096
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 2

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FALLBACK_LLM_MODEL = "google/flan-t5-large"
WHISPER_SIZE = "small"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")

DEVICE = "cpu"
TORCH_DTYPE = torch.float32
NUM_THREADS = 8          # conservative baseline — keeps CPU below throttle band
INTEROP_THREADS = 4
EMBED_BATCH_SIZE = 32    # smaller batches → less sustained heat
FAISS_THREADS = 8

TOP_K_RETRIEVAL = 5
TOP_K_FINAL = 3
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_CONTEXT_TOKENS = 1200
BM25_WEIGHT = 0.5
COSINE_WEIGHT = 0.5
CONFIDENCE_THRESHOLD = 0.35

MAX_SAFE_TEMP_C = 85       # true emergency ceiling
THROTTLE_TEMP_C = 75       # soft throttle kicks in early (was 78)
THROTTLE_THREADS = 6       # was 8 — drop harder to create headroom
EMERGENCY_THREADS = 4      # was 6

ANSWER_CACHE_SIZE = 10
L1_TTL_SECONDS = 3600
L2_TTL_SECONDS = 86400
L2_SIMILARITY_THRESHOLD = 0.92
L3_TTL_SECONDS = 14400
L4_TTL_SECONDS = 43200

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audio")

DOMAINS = {
    "basic_info": {"file": "01_basic_info.json", "keywords": ["about", "college", "university", "history", "overview", "veltech", "multitech", "established", "founded", "accreditation", "naac", "nba", "aicte"]},
    "courses": {"file": "02_courses.json", "keywords": ["course", "program", "btech", "mtech", "degree", "branch", "department", "cse", "ece", "mech", "it", "civil", "eee", "ai", "data science", "lateral", "specialization"]},
    "admission": {"file": "03_admission.json", "keywords": ["admission", "eligibility", "apply", "application", "cutoff", "counseling", "seat", "tnea", "management", "quota", "entrance", "process"]},
    "fees": {"file": "04_fees.json", "keywords": ["fee", "fees", "tuition", "cost", "scholarship", "payment", "installment", "concession", "expense", "amount", "lakh", "rupees"]},
    "infrastructure": {"file": "05_infrastructure.json", "keywords": ["infrastructure", "campus", "building", "facility", "library", "auditorium", "wifi", "classroom", "smart", "area", "acre"]},
    "labs": {"file": "06_labs.json", "keywords": ["lab", "laboratory", "computer", "workshop", "equipment", "hardware", "software", "research", "project"]},
    "placements": {"file": "07_placements.json", "keywords": ["placement", "job", "company", "recruit", "salary", "package", "lpa", "ctc", "offer", "internship", "tcs", "infosys", "wipro", "zoho", "career"]},
    "hostel": {"file": "08_hostel.json", "keywords": ["hostel", "room", "mess", "food", "accommodation", "warden", "stay", "boarding", "residential"]},
    "sports": {"file": "09_sports.json", "keywords": ["sport", "game", "cricket", "football", "basketball", "tournament", "athletic", "fitness", "gym", "ground", "play"]},
    "clubs": {"file": "10_clubs.json", "keywords": ["club", "society", "cultural", "technical", "nss", "ncc", "robotics", "coding", "debate", "music", "dance", "drama"]},
    "events": {"file": "11_events.json", "keywords": ["event", "fest", "symposium", "workshop", "seminar", "conference", "hackathon", "competition", "celebration", "annual"]},
    "faculty": {"file": "12_faculty.json", "keywords": ["faculty", "professor", "teacher", "staff", "hod", "dean", "phd", "qualification", "experience", "ratio"]},
    "industry": {"file": "13_industry.json", "keywords": ["industry", "collaboration", "mou", "partnership", "research", "startup", "incubation", "innovation", "tie-up"]},
    "transport": {"file": "14_transport.json", "keywords": ["transport", "bus", "route", "shuttle", "travel", "commute", "pick", "drop", "vehicle"]},
    "health_safety": {"file": "15_health_safety.json", "keywords": ["health", "medical", "hospital", "clinic", "safety", "security", "cctv", "first aid", "insurance", "emergency"]},
    "rankings": {"file": "16_rankings.json", "keywords": ["rank", "ranking", "nirf", "naac", "rating", "grade", "accreditation", "recognition", "achievement", "award"]},
    "contact": {"file": "17_contact.json", "keywords": ["contact", "phone", "email", "address", "location", "map", "direction", "reach", "office", "helpline", "number"]},
}

INTENTS = {
    "greeting": ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "namaste", "vanakkam"],
    "course_inquiry": ["course", "program", "branch", "department", "btech", "mtech", "degree", "study", "specialization"],
    "admission_inquiry": ["admission", "apply", "eligibility", "cutoff", "counseling", "entrance", "seat", "tnea"],
    "fee_inquiry": ["fee", "fees", "cost", "tuition", "scholarship", "payment", "expense", "amount"],
    "placement_inquiry": ["placement", "job", "company", "salary", "package", "recruit", "career", "internship"],
    "hostel_inquiry": ["hostel", "room", "mess", "food", "accommodation", "stay", "boarding"],
    "infrastructure_inquiry": ["infrastructure", "campus", "facility", "library", "lab", "building", "wifi"],
    "faculty_inquiry": ["faculty", "professor", "teacher", "staff", "hod", "dean"],
    "event_inquiry": ["event", "fest", "symposium", "workshop", "seminar", "hackathon"],
    "transport_inquiry": ["transport", "bus", "route", "shuttle", "travel", "commute"],
    "ranking_inquiry": ["rank", "ranking", "nirf", "naac", "accreditation", "grade"],
    "contact_inquiry": ["contact", "phone", "email", "address", "location", "office"],
    "general": ["tell", "what", "how", "when", "where", "why", "can", "does", "is"],
}

# ── Persuasion strategies ────────────────────────────────────────────────────
# Moved here from the former agent.py so app.py and tests have a single import.

STRATEGIES: dict[str, str] = {
    "dream_building": (
        "Paint a vivid, cinematic picture of the student's future success. "
        "Describe the career, the salary, the respect, the lifestyle they will "
        "unlock after graduating from Vel Tech Multi Tech. Use aspirational "
        "language. Make them *feel* the success."
    ),
    "urgency": (
        "Create urgency — limited seats, high demand, cutoff dates approaching. "
        "Mention that other students are already applying. Emphasize scarcity "
        "and the cost of waiting. Use phrases like 'Don't miss this window.'"
    ),
    "social_proof": (
        "Share success stories, placement records, alumni achievements, and "
        "company tie-ups. Use real data from context. Emphasize that hundreds "
        "of students have already built amazing careers from here."
    ),
    "family_pride": (
        "Appeal to the student's desire to make their parents proud. Mention "
        "how their family will feel seeing them graduate, get placed, earn well. "
        "Use warm, emotional language about family happiness and social respect."
    ),
    "fomo": (
        "Trigger fear of missing out — peers are joining, top companies are "
        "visiting campus, scholarships are running out. Paint a picture of what "
        "they'd lose by NOT choosing Vel Tech Multi Tech."
    ),
    "relationship": (
        "Be deeply personal. Use the student's name if known, reference their "
        "interests, recall past conversation topics. Make them feel individually "
        "valued and personally chosen."
    ),
    "objection_handling": (
        "Address concerns gently but firmly. Reframe doubts as advantages. "
        "Compare favorably against competitors. Use empathetic language like "
        "'I completely understand your concern, and here's why you shouldn't worry…'"
    ),
    "campus_excitement": (
        "Make campus life sound thrilling — events, clubs, tech fests, smart "
        "classrooms, modern labs, sports facilities. Show that college is not "
        "just academics but a life-transforming experience."
    ),
}

# ── Intent → persuasion strategy mapping ─────────────────────────────────────

INTENT_STRATEGY_MAP: dict[str, list[str]] = {
    "greeting":              ["relationship", "dream_building"],
    "course_inquiry":        ["dream_building", "social_proof"],
    "admission_inquiry":     ["urgency", "dream_building"],
    "fee_inquiry":           ["family_pride", "social_proof", "objection_handling"],
    "placement_inquiry":     ["social_proof", "dream_building"],
    "hostel_inquiry":        ["campus_excitement", "relationship"],
    "infrastructure_inquiry":["campus_excitement", "social_proof"],
    "faculty_inquiry":       ["social_proof", "campus_excitement"],
    "event_inquiry":         ["campus_excitement", "fomo"],
    "transport_inquiry":     ["relationship", "campus_excitement"],
    "ranking_inquiry":       ["social_proof", "family_pride"],
    "contact_inquiry":       ["urgency", "relationship"],
    "general":               ["dream_building", "relationship"],
    "objection":             ["objection_handling", "social_proof", "family_pride"],
    "comparison":            ["objection_handling", "social_proof"],
    "commitment":            ["relationship", "urgency"],
    "personal":              ["relationship", "dream_building"],
    "parent_concern":        ["family_pride", "campus_excitement", "social_proof"],
    "scholarship_need":      ["family_pride", "social_proof", "urgency"],
    "campus_visit":          ["campus_excitement", "urgency", "relationship"],
}



# ── Language-specific directives ─────────────────────────────────────────────

LANGUAGE_DIRECTIVES = {
    "en": "Respond in fluent, natural English. Use Indian English expressions where they add warmth (e.g., 'yaar', 'no worries').",
    "ta": "Respond in pure Tamil (தமிழ்). Use formal but warm Tamil. Preserve all proper nouns, course names (B.Tech, M.Tech), numbers, and acronyms in English.",
    "tanglish": (
        "Respond in Tanglish — a natural mix of Tamil and English as spoken by Chennai college students. "
        "Use Tamil particles (da, pa, la, ah, le, um) and expressions (namma college, semma placement, "
        "vera level, romba nalla, seri va) blended with English words. Sound like a friendly senior talking "
        "in a college canteen. Example: 'Bro, namma Vel Tech la placement vera level da! Top companies "
        "ellam varum, package um semma ah irukku 🔥'"
    ),
}

# ── Greeting templates by language ───────────────────────────────────────────

GREETING_TEMPLATES = {
    "en": (
        "Hey there! 👋✨ Welcome to Vel Tech Multi Tech Engineering College! "
        "I'm VelBot — your personal AI Admission Counselor. I'm SO excited to "
        "help you discover why this could be the most life-changing decision "
        "you'll ever make! 🚀\n\n"
        "Whether it's world-class courses, incredible placements, or a campus "
        "that feels like home — I've got all the answers. What's on your mind? "
        "Let's build your dream future together! 🌟"
    ),
    "ta": (
        "வணக்கம்! 👋✨ Vel Tech Multi Tech Engineering College-க்கு வரவேற்கிறோம்! "
        "நான் VelBot — உங்கள் AI Admission Counselor. உங்கள் எதிர்காலத்தை "
        "அற்புதமாக மாற்றும் வாய்ப்பைப் பற்றி பேச நான் மிகவும் உற்சாகமாக "
        "இருக்கிறேன்! 🚀\n\n"
        "Courses, placements, campus life — எதைப் பற்றியும் கேளுங்கள். "
        "உங்கள் கனவு எதிர்காலத்தை சேர்ந்து கட்டமைப்போம்! 🌟"
    ),
    "tanglish": (
        "Heyy! 👋✨ Namma Vel Tech Multi Tech Engineering College-ku welcome da! "
        "Naan VelBot — unga personal AI Admission Counselor. Bro, un future-a "
        "vera level-a maaththura chance pathi pesa romba excited ah irukken! 🚀\n\n"
        "Best courses, semma placements, home maari campus — ellathukum answer "
        "en kitta irukku. Enna kelvi kekka poreenga? Let's gooo! 🔥🌟"
    ),
}
