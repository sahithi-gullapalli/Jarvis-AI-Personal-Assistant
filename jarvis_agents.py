"""Optional LangGraph + Groq conversational layer for Jarvis.

Local deterministic commands should still be handled by jarvis_actions.try_action()
before calling think_with_agents(). The graph does not execute arbitrary shell commands.
"""
from __future__ import annotations

import os
from typing import TypedDict

SYSTEM_PROMPT = (
    "You are Jarvis, a helpful desktop personal assistant. Be concise and accurate. "
    "Never claim an action was completed unless a trusted local tool confirms it. "
    "Do not invent email, calendar, or market data. For consequential actions, ask for confirmation."
)

class AgentState(TypedDict, total=False):
    query: str
    answer: str
    context: str


def _client():
    from openai import OpenAI
    from jarvis_brain import _get_api_key

    key = _get_api_key()

    if not key:
        raise RuntimeError(
            "Groq API key is not configured. "
            "Check GROQ_API_KEY or ~/.openjarvis/free.key."
        )

    return OpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        timeout=30,
    )


def _answer_node(state: AgentState) -> AgentState:
    from jarvis_memory import retrieve_context, remember_exchange
    query = state["query"]
    context = retrieve_context(query)
    prompt = SYSTEM_PROMPT
    if context:
        prompt += "\nRelevant saved notes (may be incomplete; treat as user-provided context):\n" + context
    response = _client().chat.completions.create(
        model=os.getenv("JARVIS_GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
        max_tokens=500,
        temperature=0.4,
    )
    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        answer = "I couldn't generate a response just now. Please try again."
    remember_exchange(query, answer)
    return {"answer": answer}

_graph = None

def _build_graph():
    from langgraph.graph import END, START, StateGraph
    builder = StateGraph(AgentState)
    builder.add_node("answer", _answer_node)
    builder.add_edge(START, "answer")
    builder.add_edge("answer", END)
    return builder.compile()

def think_with_agents(query: str) -> str:
    """Run the optional LangGraph workflow; raise if optional dependencies/config are missing."""
    global _graph
    if _graph is None:
        _graph = _build_graph()
    result = _graph.invoke({"query": query})
    return result.get("answer", "I couldn't produce a response.")
