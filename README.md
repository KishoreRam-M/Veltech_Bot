# VelBot AI - Admissions Counselor 🎓🚀

VelBot is a production-grade AI Admissions Counselor built for Vel Tech Multi Tech Engineering College. It leverages a modern single-agent CrewAI architecture, Gemini-powered LLMs, and high-performance caching to provide highly responsive, multilingual voice and text counseling to prospective students.

## 🌟 Key Features

*   **CrewAI Powered:** Employs a highly optimized, single-agent architecture for deep reasoning and targeted persuasion.
*   **Multilingual Support:** Seamlessly detects and translates English, Tamil, and Tanglish.
*   **Voice Integration:** Includes real-time Speech-to-Text (STT) via Whisper and natural-sounding Text-to-Speech (TTS) via Microsoft Edge TTS (`NeerjaExpressive` & `Pallavi` neural voices).
*   **High-Performance Caching:** Utilizes L1 Exact and L2 Semantic (Sentence Transformer) caches to eliminate redundant LLM calls and achieve sub-100ms response times.
*   **Production-Grade FastAPI Backend:** Fully decoupled pre-processing pipeline (language detection, intent classification, name extraction) before handing context to the CrewAI agent.

## 📚 Documentation

Detailed documentation has been decoupled into modular files for easier navigation. Please refer to the `/docs` directory for:

- [System Architecture](docs/architecture.md): Deep dive into the data flow, CrewAI integration, and caching layers.
- [Setup & Installation](docs/setup.md): Complete guide to setting up the environment, installing dependencies via `uv`, and running the server.

## 🚀 Quick Start

1.  **Environment Variables:** Create a `.env` file with `GEMINI_API_KEY`.
2.  **Install Dependencies:** Run `uv sync` or `uv pip install -r pyproject.toml`.
3.  **Run Development Server:** `python run.py`
4.  **Run Production Server:** `python main.py`

*Built with ❤️ for Vel Tech Multi Tech.*
