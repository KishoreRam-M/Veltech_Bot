# AI Admissions Counselor — Build Tasks

## Phase 1: Project Setup
- [/] Create .env template
- [/] Create run.py entry point
- [/] Update .gitignore

## Phase 2: Backend Core
- [x] server/config.py — all constants and settings
- [x] server/cache/ — L1 exact, L2 semantic, L3 chunk, L4 translation
- [x] server/pipeline/ — language detection, normalizer, intent classifier, domain router
- [x] server/rag/ — embeddings, FAISS vector store, BM25 store, retriever, knowledge loader
- [x] server/llm/gemini.py — Gemini 2.5 Flash streaming client
- [x] server/logger.py — async JSONL logging

## Phase 3: Knowledge Base
- [x] Create 17 domain JSON files with comprehensive seed data

## Phase 4: Main Application
- [x] server/app.py — FastAPI + WebSocket + full pipeline orchestration

## Phase 5: Frontend UI
- [x] static/index.html — semantic structure
- [x] static/style.css — premium glassmorphism dark UI
- [x] static/app.js — WebSocket, voice, streaming, chat logic

## Phase 6: Verification
- [x] Server starts without errors
- [x] Chat endpoint returns grounded responses
- [x] UI renders beautifully
