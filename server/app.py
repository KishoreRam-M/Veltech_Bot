"""FastAPI application — VelBot AI Admissions Counselor.

Pipeline per request:
  1. Language detection  (pure Python, ~0 ms)
  2. Tamil/Tanglish → English translation  (Gemini, cached, conditional)
  3. Normalize query     (pure Python, ~0 ms)
  4. Classify intent     (keyword scoring, ~0 ms)
  5. Extract interests + name  (~0 ms)
  6. Pick persuasion strategy  (~0 ms)
  7. L1 exact cache lookup     (~0 ms, early-return if hit)
  8. Embed query (sentence-transformers, ~30–80 ms)
  9. L2 semantic cache lookup  (~0 ms, early-return if hit)
 10. Domain routing             (~0 ms)
 11. CrewAI run_counselor       (1 agent, 1 task — calls retrieve_knowledge @tool → Gemini)
 12. Write L1 + L2 caches
 13. Log interaction            (async, non-blocking)
"""

import time
import uuid
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr
import aiofiles

from server.config import (
    STATIC_DIR, AUDIO_DIR, GREETING_TEMPLATES, STRATEGIES, INTENT_STRATEGY_MAP,
)
from server.pipeline.language import detect_language
from server.pipeline.normalizer import normalize_query
from server.pipeline.intent import classify_intent, extract_interests
from server.pipeline.domain_router import route_domain
from server.pipeline.session import session_manager, SessionState
from server.cache.l1_exact import l1_cache
from server.cache.l2_semantic import l2_cache
from server.rag.embeddings import embed_single
from server.rag.knowledge_loader import load_knowledge
from server.llm.gemini import translate_text
from server.logger import log_interaction

import random
import re


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apply thread caps before any model load
    import torch
    from server.config import NUM_THREADS, INTEROP_THREADS
    torch.set_num_threads(NUM_THREADS)
    try:
        torch.set_num_interop_threads(INTEROP_THREADS)
    except RuntimeError:
        pass  # inter-op threads can only be set once

    print("[APP] Loading knowledge base...")
    try:
        await load_knowledge()
        print("[APP] Knowledge base loaded successfully")
    except Exception as e:
        print(f"[APP] Warning: Knowledge base loading failed: {e}")
        print("[APP] Server will run but RAG responses may be limited")
    try:
        from server.thermal_monitor import start_thermal_monitor
        start_thermal_monitor()
    except Exception as e:
        print(f"[APP] Thermal monitor unavailable: {e}")
    yield


app = FastAPI(title="VelBot - AI Admissions Counselor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


# ── Greeting shortcut (no LLM, no RAG) ───────────────────────────────────────

def _is_greeting(query: str, language: str = "en") -> str | None:
    greetings = {"hello", "hi", "hey", "good morning", "good evening", "good afternoon"}
    q = query.lower().strip().rstrip("!.,")
    if q in greetings:
        return GREETING_TEMPLATES.get(language, GREETING_TEMPLATES["en"])
    if q in {"namaste", "vanakkam"}:
        if language in ("ta", "tanglish"):
            return GREETING_TEMPLATES.get(language, GREETING_TEMPLATES["ta"])
        return GREETING_TEMPLATES["en"]
    return None


# ── Pre-processing helpers (moved out of the old AdmissionAgent) ───────────────

def _pick_strategy(intent: str, session: SessionState) -> str:
    """Select persuasion strategy, avoiding recent repetitions."""
    candidates = INTENT_STRATEGY_MAP.get(intent, ["dream_building", "relationship"])
    recent = set(session.strategies_used[-3:]) if session.strategies_used else set()
    fresh = [s for s in candidates if s not in recent]
    if not fresh:
        fresh = candidates
    return fresh[0] if len(fresh) == 1 else random.choice(fresh[:2])


def _build_strategy_directive(strategy: str) -> str:
    return STRATEGIES.get(strategy, STRATEGIES["dream_building"])


def _build_personalization(session: SessionState) -> str:
    parts: list[str] = []
    if session.user_name:
        parts.append(f"The student's name is {session.user_name}. Address them by name warmly.")
    if session.interests:
        parts.append(f"The student is interested in: {', '.join(session.interests)}. Weave these into your response.")
    if session.history:
        ctx = session.get_conversation_context(max_turns=4)
        parts.append(f"Recent conversation:\n{ctx}")
    return "\n".join(parts) if parts else "No prior context. This is a new student — make a great first impression!"


def _try_extract_name(query: str, session: SessionState):
    patterns = [r"(?i)(?:my name is|i am|i'm|call me)\s+([a-zA-Z\u0B80-\u0BFF]+(?:\s+[a-zA-Z\u0B80-\u0BFF]+)?)"]
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            session.user_name = match.group(1).strip().title()
            return


async def _process_query(query: str, session: SessionState) -> dict:
    """Full pipeline from raw query to response dict.

    Returns a dict with keys: text, language, intent, strategy, domains.
    """
    from server.crew.crew import run_counselor

    # 1. Language detection
    language = detect_language(query, session.language)

    # 2. Translate Tamil/Tanglish → English for pipeline processing
    work_query = query
    if language in ("ta", "tanglish"):
        try:
            work_query = await translate_text(query, language, "en")
        except Exception:
            work_query = query
            language = "en"

    # 3. Normalize
    normalized = normalize_query(work_query)

    # 4. Intent classification
    intent, confidence = classify_intent(normalized)

    # 5. Extract interests and update session
    for interest in extract_interests(work_query):
        session.add_interest(interest)

    # 6. Extract name if personal
    if intent == "personal":
        _try_extract_name(work_query, session)

    # 7. Pick persuasion strategy
    strategy = _pick_strategy(intent, session)
    session.mark_strategy(strategy)

    # 8. Record user message
    session.add_user_message(query)

    # 9. L1 exact cache check
    l1_result = await l1_cache.get(normalized, intent, language)
    if l1_result:
        response_text = l1_result["response"]
        session.add_bot_message(response_text)
        return {
            "text": response_text, "language": language, "intent": intent,
            "strategy": strategy, "domains": l1_result.get("domain", "").split(","),
        }

    # 10. Embed for L2 cache check
    query_embedding = None
    try:
        query_embedding = await embed_single(normalized)
        l2_result = await l2_cache.get(query_embedding, language)
        if l2_result:
            response_text = l2_result["response"]
            session.add_bot_message(response_text)
            return {
                "text": response_text, "language": language, "intent": intent,
                "strategy": strategy, "domains": l2_result.get("domain", "").split(","),
            }
    except Exception:
        query_embedding = None

    # 11. Domain routing
    domains = route_domain(normalized, intent)

    # 12. Build context strings for the crew
    strategy_directive = _build_strategy_directive(strategy)
    personalization = _build_personalization(session)

    # 13. Run the CrewAI counselor (1 agent, 1 task, sequential)
    response_text = await run_counselor(
        query=work_query,
        domains=domains,
        language=language,
        strategy_directive=strategy_directive,
        personalization=personalization,
    )

    # 14. Cache the response
    if response_text != "I'm having a small hiccup right now, but your future at Vel Tech Multi Tech is BRIGHT! 🌟 Please call 044-2684 0070 — they'll take amazing care of you!":
        domain_str = ",".join(domains)
        cache_data = {"response": response_text, "domain": domain_str}
        await l1_cache.put(normalized, intent, cache_data, language)
        if query_embedding is not None:
            await l2_cache.put(query_embedding, cache_data, language)

    session.add_bot_message(response_text)

    return {
        "text": response_text, "language": language, "intent": intent,
        "strategy": strategy, "domains": domains,
    }


# ── Pydantic Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    session_id: str | None = None
    language: str | None = None

class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000)
    lang: str = "en"

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "VelBot AI Admissions Counselor"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    query = request.query.strip()
    sid = request.session_id or str(uuid.uuid4())
    language_pref = request.language

    if not query:
        raise HTTPException(status_code=400, detail="Empty query")

    session = session_manager.get_or_create(sid)
    if language_pref:
        session.language = language_pref

    lang = detect_language(query, session.language)

    if greeting := _is_greeting(query, lang):
        session.add_user_message(query)
        session.add_bot_message(greeting)
        return JSONResponse({
            "response": greeting, "intent": "greeting",
            "cache": "none", "ms": 0,
            "session_id": sid, "language": lang, "audio": True,
        })

    start = time.time()
    result = await _process_query(query, session)
    elapsed = round((time.time() - start) * 1000)

    await log_interaction(
        sid, query, result["intent"],
        ",".join(result["domains"]), "crew", elapsed, result["language"],
    )

    return JSONResponse({
        "response": result["text"],
        "intent": result["intent"],
        "strategy": result["strategy"],
        "cache": "crew",
        "ms": elapsed,
        "session_id": sid,
        "language": result["language"],
        "audio": True,
    })


@app.post("/api/stt")
async def stt_endpoint(file: UploadFile = File(...)):
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    audio_path = None
    try:
        content = await file.read()
        if len(content) > MAX_SIZE:
            return JSONResponse({"error": "File too large"}, status_code=400)
        
        ext = ".webm"
        if file.filename:
            ext = os.path.splitext(file.filename)[1] or ".webm"
        audio_path = os.path.join(AUDIO_DIR, f"{uuid.uuid4()}{ext}")
        
        async with aiofiles.open(audio_path, "wb") as f:
            await f.write(content)
        from server.stt import transcribe
        transcript = await transcribe(audio_path)
        return JSONResponse({"transcript": transcript})
    except Exception as e:
        print(f"[STT] Endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass


@app.post("/api/tts")
async def tts_endpoint(request: TTSRequest):
    try:
        text = request.text.strip()
        lang = request.lang
        if not text:
            return JSONResponse({"error": "Empty text"}, status_code=400)
        from server.tts import generate_tts_audio
        filename = await generate_tts_audio(text, lang)
        if not filename:
            # TTS unavailable (all voices exhausted) — return 200 so the
            # frontend can degrade gracefully instead of showing an error.
            return JSONResponse({"audio_url": None, "tts_available": False})
        return JSONResponse({"audio_url": f"/audio/{filename}", "tts_available": True})
    except Exception as e:
        print(f"[TTS] Endpoint error: {e}")
        return JSONResponse({"audio_url": None, "tts_available": False})


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    sid = str(uuid.uuid4())
    session = session_manager.get_or_create(sid)
    await ws.send_json({"type": "session", "session_id": sid})
    try:
        while True:
            data = await ws.receive_json()
            query = data.get("query", "").strip()
            language_pref = data.get("language", None)
            if not query:
                continue

            if language_pref:
                session.language = language_pref

            lang = detect_language(query, session.language)

            if greeting := _is_greeting(query, lang):
                session.add_user_message(query)
                session.add_bot_message(greeting)
                await ws.send_json({
                    "type": "response", "text": greeting,
                    "intent": "greeting", "cache": "none",
                    "ms": 0, "language": lang, "audio": True,
                })
                continue

            start = time.time()
            result = await _process_query(query, session)
            elapsed = round((time.time() - start) * 1000)

            await ws.send_json({
                "type": "response",
                "text": result["text"],
                "intent": result["intent"],
                "strategy": result["strategy"],
                "cache": "crew",
                "ms": elapsed,
                "language": result["language"],
                "audio": True,
            })

            await log_interaction(
                sid, query, result["intent"],
                ",".join(result["domains"]), "crew", elapsed, result["language"],
            )

    except WebSocketDisconnect:
        pass
