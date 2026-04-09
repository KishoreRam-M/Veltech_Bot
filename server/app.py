import time
import uuid
import os
import hashlib
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from server.config import STATIC_DIR, AUDIO_DIR
from server.pipeline.language import detect_language, is_tamil
from server.pipeline.normalizer import normalize_query, compress_query
from server.pipeline.intent import classify_intent
from server.pipeline.domain_router import route_domain
from server.cache.l1_exact import l1_cache
from server.cache.l2_semantic import l2_cache
from server.rag.retriever import hybrid_retrieve
from server.rag.embeddings import embed_single
from server.rag.knowledge_loader import load_knowledge
from server.llm.gemini import generate_response, translate_text, generate_streaming
from server.logger import log_interaction

@asynccontextmanager
async def lifespan(app: FastAPI):
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

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "VelBot AI Admissions Counselor"}

async def process_query(query: str, session_id: str) -> dict:
    start = time.time()
    cache_hit = "none"
    language = detect_language(query)
    work_query = query
    if language == "ta":
        try:
            work_query = await translate_text(query, "ta", "en")
        except Exception:
            work_query = query
            language = "en"
    normalized = normalize_query(work_query)
    intent, confidence = classify_intent(normalized)
    l1_result = await l1_cache.get(normalized, intent)
    if l1_result:
        cache_hit = "L1"
        response_text = l1_result["response"]
        if language == "ta":
            try:
                response_text = await translate_text(response_text, "en", "ta")
            except Exception:
                pass
        elapsed = (time.time() - start) * 1000
        await log_interaction(session_id, query, intent, l1_result.get("domain", ""), cache_hit, elapsed, language)
        return {"response": response_text, "intent": intent, "cache": cache_hit, "ms": round(elapsed)}
    try:
        query_embedding = await embed_single(normalized)
        l2_result = await l2_cache.get(query_embedding)
        if l2_result:
            cache_hit = "L2"
            response_text = l2_result["response"]
            if language == "ta":
                try:
                    response_text = await translate_text(response_text, "en", "ta")
                except Exception:
                    pass
            elapsed = (time.time() - start) * 1000
            await log_interaction(session_id, query, intent, l2_result.get("domain", ""), cache_hit, elapsed, language)
            return {"response": response_text, "intent": intent, "cache": cache_hit, "ms": round(elapsed)}
    except Exception:
        query_embedding = None
    domains = route_domain(normalized, intent)
    domain_str = ",".join(domains)
    try:
        chunks = await hybrid_retrieve(normalized, domains)
    except Exception:
        chunks = []
    if not chunks:
        fallback = "I don't have specific information about that. Please contact our admissions office at 044-2684 0070 or email admissions@veltechmultitech.org for details."
        if language == "ta":
            try:
                fallback = await translate_text(fallback, "en", "ta")
            except Exception:
                pass
        elapsed = (time.time() - start) * 1000
        await log_interaction(session_id, query, intent, domain_str, cache_hit, elapsed, language)
        return {"response": fallback, "intent": intent, "cache": cache_hit, "ms": round(elapsed)}
    try:
        response_text = await generate_response(work_query, chunks)
    except Exception as e:
        response_text = "I'm having trouble connecting to my AI service right now. " + \
                       "Please try again in a moment, or contact the admissions office at 044-2684 0070."
    cache_data = {"response": response_text, "domain": domain_str}
    await l1_cache.put(normalized, intent, cache_data)
    if query_embedding is not None:
        await l2_cache.put(query_embedding, cache_data)
    if language == "ta":
        try:
            response_text = await translate_text(response_text, "en", "ta")
        except Exception:
            pass
    elapsed = (time.time() - start) * 1000
    await log_interaction(session_id, query, intent, domain_str, cache_hit, elapsed, language)
    return {"response": response_text, "intent": intent, "cache": cache_hit, "ms": round(elapsed)}

@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    query = body.get("query", "").strip()
    session_id = body.get("session_id", str(uuid.uuid4()))
    if not query:
        return JSONResponse({"error": "Empty query"}, status_code=400)
    if intent_check := _is_greeting(query):
        return JSONResponse({
            "response": intent_check,
            "intent": "greeting",
            "cache": "none",
            "ms": 0,
            "session_id": session_id,
        })
    result = await process_query(query, session_id)
    result["session_id"] = session_id
    return JSONResponse(result)

def _is_greeting(query: str) -> str | None:
    greetings = {"hello", "hi", "hey", "good morning", "good evening", "good afternoon"}
    q = query.lower().strip().rstrip("!.,")
    if q in greetings:
        return "Hello! 👋 Welcome to Vel Tech Multi Tech Engineering College! I'm VelBot, your AI Admissions Counselor. How can I help you today? You can ask me about courses, admissions, fees, placements, campus life, and more!"
    if q in {"namaste", "vanakkam"}:
        return "Vanakkam! 🙏 Welcome to Vel Tech Multi Tech Engineering College! I'm VelBot, your AI Admissions Counselor. How can I assist you today?"
    return None

@app.post("/api/stt")
async def stt_endpoint(file: UploadFile = File(...)):
    try:
        audio_path = os.path.join(AUDIO_DIR, f"{uuid.uuid4()}.wav")
        content = await file.read()
        with open(audio_path, "wb") as f:
            f.write(content)
        from server.stt import transcribe
        transcript = await transcribe(audio_path)
        try:
            os.remove(audio_path)
        except Exception:
            pass
        return JSONResponse({"transcript": transcript})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/tts")
async def tts_endpoint(request: Request):
    try:
        body = await request.json()
        text = body.get("text", "").strip()
        if not text:
            return JSONResponse({"error": "Empty text"}, status_code=400)
        from server.tts import speak_async
        speak_async(text)
        return JSONResponse({"status": "speaking"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    session_id = str(uuid.uuid4())
    await ws.send_json({"type": "session", "session_id": session_id})
    try:
        while True:
            data = await ws.receive_json()
            query = data.get("query", "").strip()
            if not query:
                continue
            greeting = _is_greeting(query)
            if greeting:
                await ws.send_json({"type": "response", "text": greeting, "intent": "greeting", "cache": "none", "ms": 0})
                continue
            start = time.time()
            language = detect_language(query)
            work_query = query
            if language == "ta":
                try:
                    work_query = await translate_text(query, "ta", "en")
                except Exception:
                    work_query = query
                    language = "en"
            normalized = normalize_query(work_query)
            intent, confidence = classify_intent(normalized)
            l1_result = await l1_cache.get(normalized, intent)
            if l1_result:
                response_text = l1_result["response"]
                if language == "ta":
                    try:
                        response_text = await translate_text(response_text, "en", "ta")
                    except Exception:
                        pass
                elapsed = (time.time() - start) * 1000
                await ws.send_json({"type": "response", "text": response_text, "intent": intent, "cache": "L1", "ms": round(elapsed)})
                await log_interaction(session_id, query, intent, l1_result.get("domain", ""), "L1", elapsed, language)
                continue
            domains = route_domain(normalized, intent)
            domain_str = ",".join(domains)
            try:
                chunks = await hybrid_retrieve(normalized, domains)
            except Exception:
                chunks = []
            if not chunks:
                fallback = "I don't have specific information about that. Please contact our admissions office at 044-2684 0070."
                if language == "ta":
                    try:
                        fallback = await translate_text(fallback, "en", "ta")
                    except Exception:
                        pass
                await ws.send_json({"type": "response", "text": fallback, "intent": intent, "cache": "none", "ms": round((time.time() - start) * 1000)})
                continue
            try:
                full_response = ""
                async for token in _stream_wrapper(work_query, chunks):
                    full_response += token
                    await ws.send_json({"type": "stream", "token": token})
                cache_data = {"response": full_response, "domain": domain_str}
                await l1_cache.put(normalized, intent, cache_data)
                if language == "ta":
                    try:
                        full_response = await translate_text(full_response, "en", "ta")
                    except Exception:
                        pass
                elapsed = (time.time() - start) * 1000
                await ws.send_json({"type": "done", "text": full_response, "intent": intent, "cache": "none", "ms": round(elapsed)})
                await log_interaction(session_id, query, intent, domain_str, "none", elapsed, language)
            except Exception as e:
                await ws.send_json({"type": "error", "text": "I'm having trouble right now. Please try again or contact 044-2684 0070."})
    except WebSocketDisconnect:
        pass

async def _stream_wrapper(query, chunks):
    async for token in generate_streaming(query, chunks):
        yield token
