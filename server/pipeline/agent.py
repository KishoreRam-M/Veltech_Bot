"""REMOVED — replaced by CrewAI.

The AdmissionAgent class that lived here has been migrated to:

  server/crew/agents.py  — CrewAI Agent definition
  server/crew/tasks.py   — Task factory (make_counsel_task)
  server/crew/tools.py   — @tool-decorated retrieve_knowledge, translate_query
  server/crew/crew.py    — run_counselor() async entry point

All pre-processing logic (strategy selection, personalization building,
name/interest extraction) moved to server/app.py where it belongs.

STRATEGIES and INTENT_STRATEGY_MAP constants moved to server/config.py.

This file is kept as a tombstone so git history is navigable.
Do not import from here.
"""
