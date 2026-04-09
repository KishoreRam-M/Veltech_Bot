import json
import os
import time
import asyncio
import aiofiles
from server.config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "interactions.jsonl")
_lock = asyncio.Lock()

async def log_interaction(
    session_id: str,
    query: str,
    intent: str,
    domain: str,
    cache_hit: str,
    response_ms: float,
    language: str = "en",
    escalated: bool = False,
):
    entry = {
        "ts": time.time(),
        "session_id": session_id,
        "query": query[:200],
        "intent": intent,
        "domain": domain,
        "cache_hit": cache_hit,
        "response_ms": round(response_ms, 1),
        "language": language,
        "escalated": escalated,
    }
    async with _lock:
        async with aiofiles.open(LOG_FILE, "a", encoding="utf-8") as f:
            await f.write(json.dumps(entry) + "\n")
