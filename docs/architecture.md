# 🏗️ System Architecture

VelBot is a hybrid, multi-layered application designed for high performance and low latency. The architecture follows a strict decoupled pipeline approach.

## 🔄 The Pipeline

When a user submits a query (text or audio), the FastAPI backend (`server/app.py`) processes it through the following stages:

1. **Language Detection & Translation:** Detects English, Tamil, or Tanglish. If necessary, translates the query to English using Gemini to standardize processing.
2. **Pre-Processing (Pure Python):**
   * **Normalization:** Cleans and normalizes the query.
   * **Intent Classification:** Scores keywords to classify intent (e.g., `course_inquiry`, `fee_inquiry`, `greeting`).
   * **Extraction:** Pulls names and core interests (e.g., "Computer Science") to build session context.
3. **Persuasion Strategy Engine:** Selects a persuasion directive (e.g., `dream_building`, `social_proof`, `fomo`) based on the intent to guide the LLM's tone.
4. **Caching Layer (Crucial for Speed):**
   * **L1 Exact Cache:** Fast dictionary lookup. Returns immediately on a hit.
   * **L2 Semantic Cache:** Embeds the query using `sentence-transformers` and performs cosine similarity search. Capped at 500 entries to prevent memory leaks. Returns immediately on a high-confidence match.
5. **Domain Routing:** Determines which knowledge JSON files are relevant based on intent and keywords.
6. **CrewAI Execution:** 
   * A single, focused CrewAI Agent executes the counselor task.
   * Uses `@tool` decorators for knowledge retrieval and translation.
   * Receives perfectly clean input context (no logic handling required by the agent).
7. **Response & TTS Output:** The text response is cached, logged, and synthesized into an MP3 file via Edge-TTS if audio is requested.

## 📂 Code Structure

* `server/app.py`: FastAPI entry point and pipeline orchestrator.
* `server/crew/`: CrewAI specific components (agents, tasks, tools, and the main `crew.py` runner).
* `server/cache/`: L1 and L2 caching mechanisms.
* `server/pipeline/`: Pre-processing utilities (intent, normalizer, language).
* `server/config.py`: Global configuration, directories, and mappings.
* `static/`: React/Vanilla JS frontend with built-in TTS playback handling.
