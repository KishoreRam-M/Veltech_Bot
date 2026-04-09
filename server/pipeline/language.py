import re

TAMIL_RANGE = range(0x0B80, 0x0BFF + 1)

def detect_language(text: str) -> str:
    tamil_count = sum(1 for ch in text if ord(ch) in TAMIL_RANGE)
    total = max(len(text.strip()), 1)
    if tamil_count / total > 0.3:
        return "ta"
    return "en"

def is_tamil(text: str) -> bool:
    return detect_language(text) == "ta"
