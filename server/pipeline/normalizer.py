import re

FILLERS = {"um", "uh", "like", "you know", "basically", "actually", "so", "well", "right", "okay", "ok"}
CONTRACTIONS = {
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "cannot", "won't": "will not", "wouldn't": "would not",
    "shouldn't": "should not", "couldn't": "could not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "i'm": "i am", "you're": "you are", "they're": "they are",
    "we're": "we are", "it's": "it is", "that's": "that is",
    "what's": "what is", "where's": "where is", "who's": "who is",
}

def normalize_query(query: str) -> str:
    text = query.lower().strip()
    for contraction, expansion in CONTRACTIONS.items():
        text = text.replace(contraction, expansion)
    words = text.split()
    words = [w for w in words if w not in FILLERS]
    text = " ".join(words)
    text = re.sub(r"[^\w\s₹\-.]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


