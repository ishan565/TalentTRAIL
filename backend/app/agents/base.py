"""Shared helpers for agent nodes.

* ``track`` wraps a node so timing, status, and errors are recorded into the
  state's ``execution_history`` automatically — every agent gets uniform
  observability without boilerplate.
* ``llm_json`` performs a structured LLM call with robust JSON extraction and a
  schema-validated fallback so a malformed model response never crashes a graph.
"""
from __future__ import annotations

import json
import re
import time
from functools import wraps
from typing import Any, Callable

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import TalentTrailState
from app.core.llm import get_chat_model
from app.core.logging import get_logger

logger = get_logger(__name__)


def track(agent_name: str) -> Callable:
    """Decorator: time a node, capture errors, append an execution record."""

    def decorator(fn: Callable[[TalentTrailState], dict]) -> Callable[[TalentTrailState], dict]:
        @wraps(fn)
        def wrapper(state: TalentTrailState) -> dict:
            start = time.perf_counter()
            try:
                update = fn(state) or {}
                ms = int((time.perf_counter() - start) * 1000)
                logger.info("agent.done", agent=agent_name, ms=ms)
                history = {"agent": agent_name, "status": "ok", "ms": ms}
                return {**update, "execution_history": [history]}
            except Exception as exc:  # keep the graph resilient
                ms = int((time.perf_counter() - start) * 1000)
                logger.error("agent.error", agent=agent_name, error=str(exc))
                return {
                    "execution_history": [
                        {"agent": agent_name, "status": "error", "ms": ms, "note": str(exc)}
                    ],
                    "errors": [{"agent": agent_name, "error": str(exc)}],
                }

        return wrapper

    return decorator


def _extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of an LLM response."""
    text = text.strip()
    # Strip ```json fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    candidate = match.group(1) if match else text
    return json.loads(candidate)


def llm_json(
    system: str,
    user: str,
    *,
    temperature: float = 0.1,
    fallback: Any = None,
) -> Any:
    """Call the chat model and parse JSON; return ``fallback`` on any failure."""
    try:
        model = get_chat_model(temperature=temperature)
        resp = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return _extract_json(resp.content if hasattr(resp, "content") else str(resp))
    except Exception as exc:
        logger.warning("llm_json.fallback", error=str(exc))
        return fallback


def llm_text(system: str, user: str, *, temperature: float = 0.4, fallback: str = "") -> str:
    try:
        model = get_chat_model(temperature=temperature)
        resp = model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content if hasattr(resp, "content") else str(resp)
    except Exception as exc:
        logger.warning("llm_text.fallback", error=str(exc))
        return fallback
