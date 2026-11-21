from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.models.schemas import ObservabilityReport
from app.observability.tracer import TRACE_REGISTRY
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/observability", tags=["Observability & Performance"])

@router.get("/overview")
async def get_observability_overview() -> Dict[str, Any]:
    """
    Returns global observability metrics across all recorded agent analysis runs:
    Total tokens, total cost (USD), average latency, concurrency speedup, and agent metrics.
    """
    all_reports: List[ObservabilityReport] = list(TRACE_REGISTRY.values())

    if not all_reports:
        return {
            "total_sessions_tracked": 0,
            "total_tokens_consumed": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_wall_time_ms": 0.0,
            "avg_speedup_factor": 1.0,
            "agent_performance": [],
            "recent_traces": []
        }

    total_sessions = len(all_reports)
    total_tokens = sum(r.total_tokens for r in all_reports)
    total_prompt = sum(r.total_prompt_tokens for r in all_reports)
    total_completion = sum(r.total_completion_tokens for r in all_reports)
    total_cost = round(sum(r.total_cost_usd for r in all_reports), 6)
    avg_wall_time = round(sum(r.total_wall_time_ms for r in all_reports) / total_sessions, 2)
    avg_speedup = round(sum(r.parallel_speedup_factor for r in all_reports) / total_sessions, 2)

    # Aggregate agent breakdown
    agent_stats: Dict[str, Dict[str, Any]] = {}
    for r in all_reports:
        for m in r.agent_metrics:
            if m.agent_name not in agent_stats:
                agent_stats[m.agent_name] = {
                    "agent_name": m.agent_name,
                    "invocations": 0,
                    "total_duration_ms": 0.0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0
                }
            agent_stats[m.agent_name]["invocations"] += 1
            agent_stats[m.agent_name]["total_duration_ms"] += m.duration_ms
            agent_stats[m.agent_name]["total_tokens"] += m.tokens
            agent_stats[m.agent_name]["total_cost_usd"] += m.cost_usd

    agent_performance = []
    for a in agent_stats.values():
        inv = a["invocations"]
        agent_performance.append({
            "agent_name": a["agent_name"],
            "invocations": inv,
            "avg_duration_ms": round(a["total_duration_ms"] / max(inv, 1), 2),
            "total_tokens": a["total_tokens"],
            "total_cost_usd": round(a["total_cost_usd"], 6)
        })

    recent_traces = [
        {
            "trace_id": r.trace_id,
            "wall_time_ms": r.total_wall_time_ms,
            "speedup": r.parallel_speedup_factor,
            "tokens": r.total_tokens,
            "cost_usd": r.total_cost_usd,
            "model": r.primary_model,
            "status": r.langfuse_status
        }
        for r in all_reports[-10:]
    ]

    return {
        "total_sessions_tracked": total_sessions,
        "total_tokens_consumed": total_tokens,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_cost_usd": total_cost,
        "avg_wall_time_ms": avg_wall_time,
        "avg_speedup_factor": avg_speedup,
        "agent_performance": agent_performance,
        "recent_traces": recent_traces
    }

@router.get("/trace/{session_id}", response_model=ObservabilityReport)
async def get_session_trace(session_id: str):
    """
    Returns the fine-grained span waterfall, token breakdown, cost estimate,
    and provenance audit trail for a specific analysis session.
    """
    if session_id in TRACE_REGISTRY:
        return TRACE_REGISTRY[session_id]

    # Try retrieving from report cache
    report = await analysis_service.get_report(session_id)
    if report and report.observability:
        return report.observability

    raise HTTPException(status_code=404, detail="Observability trace not found for session.")
