"""VelBot CrewAI entry point.

`run_counselor` is the single public function that replaces
`AdmissionAgent.process()`. It accepts pre-computed context (language,
intent, strategy, domains, personalization) and runs the one-agent crew
to produce a response.

Pre-processing (language detection, normalization, intent classification,
domain routing, cache lookups) is the caller's responsibility (app.py).
This keeps the crew pure: it receives clean inputs and returns a response.
"""

from __future__ import annotations

import asyncio
from crewai import Crew, Process

from server.crew.agents import velbot_counselor
from server.crew.tasks import make_counsel_task
from server.config import LANGUAGE_DIRECTIVES


_FALLBACK = (
    "I'm having a small hiccup right now, but your future at Vel Tech Multi Tech "
    "is BRIGHT! 🌟 Please call 044-2684 0070 — they'll take amazing care of you!"
)


def _run_crew_sync(
    query: str,
    domains: list[str],
    language: str,
    strategy_directive: str,
    personalization: str,
) -> str:
    """Synchronously kick off the one-agent crew and return its output."""
    language_directive = LANGUAGE_DIRECTIVES.get(language, LANGUAGE_DIRECTIVES["en"])
    domains_str = ",".join(domains)

    task = make_counsel_task(
        query=query,
        domains=domains_str,
        language_directive=language_directive,
        strategy_directive=strategy_directive,
        personalization=personalization,
    )

    crew = Crew(
        agents=[velbot_counselor],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    # CrewAI returns a CrewOutput object; .raw gives the plain string
    return str(result.raw).strip()


async def run_counselor(
    query: str,
    domains: list[str],
    language: str,
    strategy_directive: str,
    personalization: str,
) -> str:
    """Async wrapper: runs the synchronous crew in a thread so it doesn't
    block the FastAPI event loop.

    Args:
        query:              Normalized English query.
        domains:            Domain names for retrieval (pre-computed by caller).
        language:           Response language: 'en', 'ta', or 'tanglish'.
        strategy_directive: Persuasion strategy text.
        personalization:    Name, interests, conversation history block.

    Returns:
        Counselor response string, or a friendly fallback on error.
    """
    try:
        return await asyncio.to_thread(
            _run_crew_sync,
            query,
            domains,
            language,
            strategy_directive,
            personalization,
        )
    except Exception as e:
        print(f"[CREW] run_counselor failed: {e}")
        return _FALLBACK
