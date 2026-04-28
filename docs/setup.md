# ⚙️ Setup & Installation

Follow these steps to set up the VelBot application locally.

## 📋 Prerequisites

* **Python:** Version 3.10 or higher.
* **uv:** Fast Python package and project manager. (`pip install uv`)
* **API Keys:** You will need a Gemini API key.

## 🚀 Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd <project-directory>
   ```

2. **Set up Environment Variables**
   Create a `.env` file in the root directory and add your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Install Dependencies**
   The project uses `uv` for lightning-fast dependency management.
   ```bash
   uv sync
   # OR
   uv pip install -r pyproject.toml
   ```
   *(Note: The environment `.venv` will be automatically managed by uv).*

## 🏃 Running the Application

**Development Mode (Hot Reloading)**
```bash
python run.py
```
This script runs the Uvicorn server with `reload=True` and applies any Intel-specific optimizations (`intel_setup.py`) before starting.

**Production Mode**
```bash
python main.py
```
Runs the application without reloading for optimal performance.

## 🌐 Accessing the UI
Once the server is running, navigate to `http://localhost:8000` in your web browser to interact with VelBot.
