
"""
jarvis_brain.py - Hybrid Cloud + Local AI Brain
Integrates LangGraph agents and ChromaDB memory while preserving
existing Windows automation, Groq model failover and rate-limit handling.
"""

import os
import time
import re
from openai import OpenAI
import jarvis_actions

KEYFILE = os.path.expanduser("~/.openjarvis/free.key")

MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b"
]

_client = None
_history = []
_cooldown_until = 0.0

SYSTEM_PROMPT = """You are Jarvis, a fast, highly capable AI executive assistant running on the user's computer.
Respond concisely in 1-2 sentences. Be direct, helpful, and natural.
Do not use filler or formal corporate jargon.
"""


def _get_api_key():
    """Read the Groq API key from the environment or local key file."""
    env_key = os.environ.get("GROQ_API_KEY")

    if env_key:
        return env_key.strip()

    if os.path.exists(KEYFILE):
        with open(KEYFILE, "r", encoding="utf-8") as file:
            return file.read().strip()

    return None


def ready():
    """Check whether the cloud brain is configured and available."""
    key = _get_api_key()

    if not key:
        return False

    return time.time() >= _cooldown_until


def _is_rate_limited(e):
    """Identify Groq API rate-limit errors."""
    status = getattr(e, "status_code", None)

    if status == 429:
        return True

    error_message = str(e).lower()

    return any(
        word in error_message
        for word in (
            "429",
            "rate limit",
            "too many requests",
            "rate_limit",
            "exceeded"
        )
    )


def _retry_after_seconds(e, default=60):
    """Extract retry duration from an API error."""
    error_message = str(e).lower()

    match = re.search(
        r"try again in\s*(\d+)m\s*([0-9]+(?:\.[0-9]+)?)s",
        error_message
    )

    if match:
        return int(
            float(match.group(1)) * 60
            + float(match.group(2))
        ) + 2

    match = re.search(
        r"try again in\s*([0-9]+(?:\.[0-9]+)?)s",
        error_message
    )

    if match:
        return int(float(match.group(1))) + 2

    return default


def _set_cooldown(secs):
    """Activate API cooldown after rate limiting."""
    global _cooldown_until

    _cooldown_until = max(
        _cooldown_until,
        time.time() + float(secs)
    )


def _local_fallback(q):
    """Return a safe response when cloud AI is unavailable."""
    return (
        "Cloud AI is temporarily unavailable, but my local assistant "
        "is active. I can open your apps, check WhatsApp, or analyze "
        "stock charts for you."
    )


def _original_groq_response(q, key):
    """
    Original Groq fallback.
    Preserves three-model failover and conversation history.
    """
    global _client, _history

    if _client is None:
        _client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1"
        )

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + _history[-6:]
        + [{"role": "user", "content": q}]
    )

    for model in MODELS:
        try:
            response = _client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=350,
                temperature=0.6,
            )

            answer = (
                response.choices[0].message.content or ""
            ).strip()

            if answer:
                _history.extend([
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": answer}
                ])

                return answer

        except Exception as e:
            if _is_rate_limited(e):
                wait_seconds = _retry_after_seconds(e)
                _set_cooldown(wait_seconds)

                print(
                    f"[Rate-limit triggered: "
                    f"cooldown for {wait_seconds}s]"
                )

                return _local_fallback(q)

            print(f"[Model {model} failed: {e}]")

    return _local_fallback(q)


def think(q):
    """
    Main Jarvis entry point.

    1. Local Windows actions.
    2. LangGraph agent with ChromaDB memory.
    3. Original Groq model failover.
    4. Local fallback.
    """
    global _history

    if not isinstance(q, str) or not q.strip():
        return "Please tell me what you need."

    q = q.strip()

    # 1. Execute existing local actions first.
    local_result = jarvis_actions.try_action(q)

    if local_result:
        return local_result

    # 2. Check API availability.
    key = _get_api_key()

    if not key or time.time() < _cooldown_until:
        return _local_fallback(q)

    # 3. Try LangGraph agent with ChromaDB memory.
    try:
        from jarvis_agents import think_with_agents

        answer = think_with_agents(q)

        if answer and answer.strip():
            answer = answer.strip()

            _history.extend([
                {"role": "user", "content": q},
                {"role": "assistant", "content": answer}
            ])

            return answer

        print("[LangGraph returned an empty response]")

    except Exception as e:
        print(f"[LangGraph agent unavailable: {e}]")
        print("[Switching to original Groq model fallback]")

        # Apply cooldown if the agent encountered rate limiting.
        if _is_rate_limited(e):
            wait_seconds = _retry_after_seconds(e)
            _set_cooldown(wait_seconds)

            print(
                f"[Rate-limit triggered: "
                f"cooldown for {wait_seconds}s]"
            )

            return _local_fallback(q)

    # 4. Use the original Groq model failover.
    return _original_groq_response(q, key)


if __name__ == "__main__":
    print("Testing Jarvis Brain...")

    print("\nTest 1: Local command")
    print(think("what time is it"))

    print("\nTest 2: AI conversation")
    print(think("how are you"))
