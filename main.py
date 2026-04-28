"""VelBot entry point.

Usage:
    python main.py          # production-style (no reload)
    python run.py           # development (reload=True, Intel optimisations)
"""

import intel_setup  # noqa: F401 — sets OMP/MKL thread counts before uvicorn starts

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
