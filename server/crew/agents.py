"""Defines the single CrewAI Agent for VelBot.

One agent — one job: given retrieved knowledge and a persuasion strategy,
produce a response that moves a student one step closer to enrolling.
"""

from crewai import Agent, LLM
from server.crew.tools import retrieve_knowledge, translate_query
from server.config import GEMINI_API_KEY, GEMINI_MODEL, TEMPERATURE, MAX_OUTPUT_TOKENS

# One LLM instance shared across all crew runs.
_llm = LLM(
    model=f"gemini/{GEMINI_MODEL}",
    api_key=GEMINI_API_KEY,
    temperature=TEMPERATURE,
    max_tokens=MAX_OUTPUT_TOKENS,
)

# The single counselor agent.
velbot_counselor = Agent(
    role="AI Admissions Counselor",
    goal=(
        "Answer every student query with a factually grounded, emotionally compelling "
        "response that makes them feel individually valued and moves them one concrete "
        "step closer to applying to Vel Tech Multi Tech Engineering College."
    ),
    backstory=(
        "VelBot is Vel Tech Multi Tech's passionate AI counselor — part mentor, "
        "part dream architect, fluent in the college's placements, courses, campus life, "
        "fees, and more. Every response ends with a clear call-to-action."
    ),
    tools=[retrieve_knowledge, translate_query],
    llm=_llm,
    verbose=False,
    allow_delegation=False,  # Single agent; delegation would create phantom agents
    max_iter=3,              # Cap tool-call loops; 3 is enough for any RAG task
)
