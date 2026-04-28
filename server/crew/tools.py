"""CrewAI @tool wrappers for retrieval and translation.

These are the only two external actions the counselor agent can invoke:
  - retrieve_knowledge: hybrid FAISS+BM25 search over the college knowledge base
  - translate_query:    Tamil / Tanglish → English via Gemini (cached)

All cache logic lives inside the tools, invisible to the agent.
"""

from __future__ import annotations

import asyncio
from crewai.tools import tool


@tool("retrieve_knowledge")
def retrieve_knowledge(query: str, domains: str) -> str:
    """Retrieve relevant knowledge chunks from the college knowledge base.

    Args:
        query:   The normalized English query string.
        domains: Comma-separated domain names, e.g. 'courses,placements'.

    Returns:
        Formatted knowledge chunks as a single string block, or an empty
        string if nothing was found above the confidence threshold.
    """
    from server.rag.retriever import hybrid_retrieve

    domain_list = [d.strip() for d in domains.split(",") if d.strip()]

    # Run the async retriever in the current event loop if one exists,
    # otherwise spin a new one.  CrewAI runs tools synchronously.
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                chunks = pool.submit(
                    asyncio.run, hybrid_retrieve(query, domain_list)
                ).result()
        else:
            chunks = loop.run_until_complete(hybrid_retrieve(query, domain_list))
    except RuntimeError:
        chunks = asyncio.run(hybrid_retrieve(query, domain_list))

    if not chunks:
        return ""

    return "\n\n".join(
        f"[{chunk.get('id', 'unknown')}] {chunk['text']}"
        for chunk in chunks
    )


@tool("translate_query")
def translate_query(text: str, source_lang: str) -> str:
    """Translate a Tamil or Tanglish query to English using Gemini (cached).

    Args:
        text:        The original query in Tamil or Tanglish.
        source_lang: Either 'ta' (pure Tamil) or 'tanglish'.

    Returns:
        The English translation of the query, or the original text if
        translation fails.
    """
    from server.llm.gemini import translate_text

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run, translate_text(text, source_lang, "en")
                ).result()
        else:
            result = loop.run_until_complete(translate_text(text, source_lang, "en"))
    except RuntimeError:
        result = asyncio.run(translate_text(text, source_lang, "en"))

    return result
