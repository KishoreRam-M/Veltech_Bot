import re

TAMIL_RANGE = range(0x0B80, 0x0BFF + 1)

# Common romanized Tamil words used in Tanglish
TANGLISH_MARKERS = {
    "namma", "enna", "inga", "anga", "oru", "oru", "romba", "konjam",
    "pannunga", "pannurom", "pannu", "panna", "pannalam", "pannidalam",
    "irukku", "irukke", "irukka", "illa", "illai", "illaye",
    "vanakkam", "nandri", "thala", "da", "di", "pa", "ma",
    "sollum", "sollu", "sollunga", "solren", "sollren",
    "porom", "poren", "poidalam", "pogalam", "pona",
    "vanga", "vaanga", "varunga", "vaarunga", "varuvom",
    "theriyum", "theriyathu", "theriyala", "therinja",
    "enga", "yenna", "yeppadi", "yeppa", "yeppo", "epdi",
    "paaru", "paarunga", "yaar", "ethuku", "ethu",
    "nan", "naan", "nee", "avan", "aval", "avanga",
    "apdina", "apdi", "appadiya", "ipdi", "ippadi",
    "sari", "seri", "ok", "okva",
    "kalakku", "mass", "vera", "level", "semma", "thara",
    "college", "join", "padikka", "padikkalam", "padichu",
    "veltech", "course", "seat", "admission",
    "unga", "ungaluku", "ungala", "enaku", "enakku",
    "bro", "anna", "akka", "thambi",
    "chance", "future", "life", "dream",
    "ah", "la", "le", "ku", "um", "uh",
    "mudiyum", "mudiyathu", "mudiyala", "venum", "vendum",
    "kastam", "kastamah", "nallathu", "nallaa",
    "super", "best", "top", "first",
    "idhu", "adhu", "andha", "indha",
    "pakkalam", "paakalam", "paakanum",
}


def detect_language(text: str, preference: str | None = None) -> str:
    """Detect language: 'ta' (pure Tamil), 'en' (English), or 'tanglish' (mixed).

    If a user preference is set and is not 'auto', return the preference directly.
    """
    if preference and preference != "auto":
        return preference

    tamil_count = sum(1 for ch in text if ord(ch) in TAMIL_RANGE)
    total = max(len(text.strip()), 1)
    tamil_ratio = tamil_count / total

    # Pure Tamil: >30% Tamil Unicode characters
    if tamil_ratio > 0.3:
        return "ta"

    # Tanglish: Latin script but contains romanized Tamil words
    words_lower = set(text.lower().split())
    tanglish_hits = words_lower.intersection(TANGLISH_MARKERS)
    if len(tanglish_hits) >= 2:
        return "tanglish"
    # Single tanglish marker + short message = likely tanglish
    if len(tanglish_hits) >= 1 and len(words_lower) <= 6:
        return "tanglish"

    return "en"



