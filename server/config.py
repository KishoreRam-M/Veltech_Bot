import os
import torch
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 300
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 2

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
FALLBACK_LLM_MODEL = "google/flan-t5-large"
WHISPER_SIZE = "small"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "models")

DEVICE = "cpu"
TORCH_DTYPE = torch.float32
NUM_THREADS = 12
INTEROP_THREADS = 4
EMBED_BATCH_SIZE = 64
FAISS_THREADS = 12

TOP_K_RETRIEVAL = 5
TOP_K_FINAL = 3
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_CONTEXT_TOKENS = 1500
BM25_WEIGHT = 0.5
COSINE_WEIGHT = 0.5
CONFIDENCE_THRESHOLD = 0.35

MAX_SAFE_TEMP_C = 82
THROTTLE_TEMP_C = 78
THROTTLE_THREADS = 8
EMERGENCY_THREADS = 6

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

SYSTEM_PROMPT = """You are the official AI Admissions Counselor for Vel Tech Multi Tech Dr. Rangarajan Dr. Sakunthala Engineering College, Chennai. Your name is VelBot.

STRICT RULES:
1. ONLY answer questions using the provided context chunks. Never make up information.
2. If the context does not contain enough information, say: "I don't have specific information about that. Please contact our admissions office at 044-2684 0070 for details."
3. Be warm, professional, and encouraging to prospective students and parents.
4. Format responses clearly with bullet points when listing multiple items.
5. Keep responses concise (3-5 sentences for simple queries, more for detailed ones).
6. Always mention official contact details when relevant.
7. If a question is completely unrelated to the college, politely redirect: "I'm here to help with queries about Vel Tech Multi Tech Engineering College. How can I assist you with admissions, courses, or campus life?"
8. Use ₹ for currency amounts.
9. Preserve all proper nouns, course names, and numerical data exactly as given in context.
10. When unsure between two data points, present both and suggest confirming with the office.

CONTEXT CHUNKS:
{context}

USER QUERY: {query}"""
