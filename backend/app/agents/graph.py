"""LangGraph orchestrator wiring the nine agents into a stateful graph.

Topology (the "full job-hunt pipeline"):

    resume_analysis
          │
    job_discovery
          │
    semantic_matching
          │
        ┌─┴─────────────┐
   ats_scoring   missing_keywords     (analysis fan-out, run sequentially
        └─┬─────────────┘              for deterministic ordering)
   resume_optimization
          │
    cover_letter
          │
    career_strategy
          │
   application_tracker
          │
        END

LangGraph merges each node's partial dict back into the shared state and, thanks
to the ``Annotated[list, add]`` reducers, ``execution_history`` accumulates a
full trace across every node.

We expose:
* ``build_graph()``        — compile the full pipeline.
* ``build_analysis_graph`` — a lean graph for single-job ATS/keyword/cover flows
  that skips discovery (resume + a preloaded target job already in state).
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.ats_agent import ats_scoring_node
from app.agents.cover_letter_agent import cover_letter_node
from app.agents.job_discovery_agent import job_discovery_node
from app.agents.keyword_agent import missing_keywords_node
from app.agents.matching_agent import semantic_matching_node
from app.agents.optimization_agent import resume_optimization_node
from app.agents.resume_agent import resume_analysis_node
from app.agents.state import TalentTrailState
from app.agents.strategy_agent import career_strategy_node
from app.agents.tracker_agent import application_tracker_node


@lru_cache
def build_graph():
    g = StateGraph(TalentTrailState)

    g.add_node("resume_analysis", resume_analysis_node)
    g.add_node("job_discovery", job_discovery_node)
    g.add_node("semantic_matching", semantic_matching_node)
    g.add_node("ats_scoring", ats_scoring_node)
    # Node name must differ from the "missing_keywords" state key (LangGraph
    # forbids a node sharing a name with a state channel).
    g.add_node("keyword_gap", missing_keywords_node)
    g.add_node("resume_optimization", resume_optimization_node)
    g.add_node("cover_letter", cover_letter_node)
    g.add_node("career_strategy", career_strategy_node)
    g.add_node("application_tracker", application_tracker_node)

    g.add_edge(START, "resume_analysis")
    g.add_edge("resume_analysis", "job_discovery")
    g.add_edge("job_discovery", "semantic_matching")
    g.add_edge("semantic_matching", "ats_scoring")
    g.add_edge("ats_scoring", "keyword_gap")
    g.add_edge("keyword_gap", "resume_optimization")
    g.add_edge("resume_optimization", "cover_letter")
    g.add_edge("cover_letter", "career_strategy")
    g.add_edge("career_strategy", "application_tracker")
    g.add_edge("application_tracker", END)

    return g.compile()


@lru_cache
def build_analysis_graph():
    """Single-job flow: resume already parsed + a target job in ``jobs_found``."""
    g = StateGraph(TalentTrailState)
    g.add_node("ats_scoring", ats_scoring_node)
    g.add_node("keyword_gap", missing_keywords_node)
    g.add_node("resume_optimization", resume_optimization_node)
    g.add_node("cover_letter", cover_letter_node)

    g.add_edge(START, "ats_scoring")
    g.add_edge("ats_scoring", "keyword_gap")
    g.add_edge("keyword_gap", "resume_optimization")
    g.add_edge("resume_optimization", "cover_letter")
    g.add_edge("cover_letter", END)
    return g.compile()
