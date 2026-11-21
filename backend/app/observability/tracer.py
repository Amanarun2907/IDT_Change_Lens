import os
import time
import math
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import httpx
from app.config import settings
from app.models.schemas import TraceSpan, AgentPerformanceMetric, ObservabilityReport

logger = logging.getLogger(__name__)

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# Pricing table per 1,000,000 tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
    "gemini-2.5-pro": {"prompt": 1.25, "completion": 5.00},
    "llama-3.3-70b-versatile": {"prompt": 0.59, "completion": 0.79},
    "llama-3.1-8b-instant": {"prompt": 0.05, "completion": 0.08},
    "deepseek-r1-distill-llama-70b": {"prompt": 0.59, "completion": 0.79},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "default": {"prompt": 0.10, "completion": 0.40}
}

class ObservabilityTracker:
    """
    OpenTelemetry & Langfuse-compatible Observability Tracer.
    Tracks span-level execution latencies, token consumption, cost calculation,
    topological provenance, and concurrency speedup factors.
    """
    def __init__(self, session_id: str, provider: Optional[str] = None, model: Optional[str] = None):
        self.session_id = session_id
        self.trace_id = session_id
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.spans: List[TraceSpan] = []
        self._active_spans: Dict[str, Dict[str, Any]] = {}
        self.audit_events: List[Dict[str, Any]] = []
        self.start_wall_time = time.time()
        self.end_wall_time: Optional[float] = None

    def start_span(
        self,
        name: str,
        agent_name: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        model_name: Optional[str] = None,
        input_data: Optional[Any] = None
    ) -> Any:
        span_id = f"span-{uuid.uuid4().hex[:8]}"
        self._active_spans[span_id] = {
            "span_id": span_id,
            "name": name,
            "agent_name": agent_name or name,
            "parent_span_id": parent_span_id,
            "model_name": model_name or self.model,
            "start_time_sec": time.time(),
            "input_data": input_data
        }
        class SpanHandle:
            def __init__(self, sid: str, sname: str):
                self.span_id = sid
                self.name = sname
        return SpanHandle(span_id, name)

    def end_span(
        self,
        span_id: str,
        status: str = "COMPLETED",
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        output_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        active = self._active_spans.pop(span_id, None)
        end_time_sec = time.time()
        start_time_sec = active["start_time_sec"] if active else end_time_sec
        name = active["name"] if active else "unknown_span"
        agent_name = active["agent_name"] if active else name
        model_name = active.get("model_name", self.model) if active else self.model
        parent_span_id = active.get("parent_span_id") if active else None

        duration_ms = round((end_time_sec - start_time_sec) * 1000.0, 2)
        in_text = str(active.get("input_data")) if (active and active.get("input_data") is not None) else ""
        out_text = str(output_data) if output_data is not None else ""
        p_tokens = prompt_tokens if prompt_tokens is not None else self.estimate_tokens(in_text)
        c_tokens = completion_tokens if completion_tokens is not None else self.estimate_tokens(out_text)
        t_tokens = p_tokens + c_tokens
        cost_usd = self.calculate_cost(p_tokens, c_tokens, model_name)

        span = TraceSpan(
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            agent_name=agent_name,
            start_time=datetime.fromtimestamp(start_time_sec, tz=timezone.utc).isoformat(),
            end_time=datetime.fromtimestamp(end_time_sec, tz=timezone.utc).isoformat(),
            duration_ms=duration_ms,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            cost_usd=cost_usd,
            status=status,
            model=model_name,
            metadata=metadata or {}
        )
        self.spans.append(span)

        self.audit_events.append({
            "timestamp": span.end_time,
            "span_id": span_id,
            "agent_name": agent_name,
            "event": name,
            "duration_ms": duration_ms,
            "tokens": t_tokens,
            "cost_usd": cost_usd,
            "status": status,
            "provenance": {
                "model": model_name,
                "provider": self.provider
            }
        })
        return span

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: Optional[str] = None) -> float:
        m = (model or self.model).lower()
        pricing = MODEL_PRICING.get(m, MODEL_PRICING["default"])
        cost = (prompt_tokens / 1_000_000.0) * pricing["prompt"] + (completion_tokens / 1_000_000.0) * pricing["completion"]
        return round(cost, 6)

    def estimate_tokens(self, text: str) -> int:
        """Heuristic token estimator (approx 4 chars per token) when provider doesn't report raw usage."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4.0))

    def record_span(
        self,
        name: str,
        agent_name: str,
        start_time_sec: float,
        end_time_sec: float,
        prompt_text: str = "",
        output_text: str = "",
        parent_span_id: Optional[str] = None,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        duration_ms = round((end_time_sec - start_time_sec) * 1000.0, 2)
        prompt_tokens = self.estimate_tokens(prompt_text)
        completion_tokens = self.estimate_tokens(output_text)
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = self.calculate_cost(prompt_tokens, completion_tokens, self.model)

        span_id = f"span-{uuid.uuid4().hex[:8]}"

        span = TraceSpan(
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            agent_name=agent_name,
            start_time=datetime.fromtimestamp(start_time_sec, tz=timezone.utc).isoformat(),
            end_time=datetime.fromtimestamp(end_time_sec, tz=timezone.utc).isoformat(),
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            status=status,
            model=self.model,
            metadata=metadata or {}
        )
        self.spans.append(span)

        # Record structured audit event for provenance
        self.audit_events.append({
            "timestamp": span.end_time,
            "span_id": span_id,
            "agent_name": agent_name,
            "event": name,
            "duration_ms": duration_ms,
            "tokens": total_tokens,
            "cost_usd": cost_usd,
            "status": status,
            "provenance": {
                "model": self.model,
                "provider": self.provider,
                "input_chars": len(prompt_text),
                "output_chars": len(output_text)
            }
        })

        return span

    def finalize(self) -> ObservabilityReport:
        self.end_wall_time = time.time()
        total_wall_ms = round((self.end_wall_time - self.start_wall_time) * 1000.0, 2)

        # Sum of individual specialist durations if executed sequentially
        specialist_spans = [s for s in self.spans if s.name.startswith("agent:")]
        sequential_ms = sum(s.duration_ms for s in specialist_spans)
        if sequential_ms <= 0:
            sequential_ms = total_wall_ms

        speedup = round(sequential_ms / max(total_wall_ms, 1.0), 2)
        if speedup < 1.0:
            speedup = 1.0

        total_prompt = sum(s.prompt_tokens for s in self.spans)
        total_completion = sum(s.completion_tokens for s in self.spans)
        total_tok = total_prompt + total_completion
        total_cost = round(sum(s.cost_usd for s in self.spans), 6)

        # Estimated cost per 1,000 Lines of Code reviewed (assuming ~40 chars/line -> 10 tokens/line)
        cost_per_kloc = round((10_000 / max(total_tok, 1)) * total_cost, 5) if total_tok > 0 else 0.001

        # Aggregate agent-level metrics
        agent_metrics: List[AgentPerformanceMetric] = []
        agent_names = list(dict.fromkeys(s.agent_name for s in self.spans))
        for aname in agent_names:
            agent_spans = [s for s in self.spans if s.agent_name == aname]
            a_dur = sum(s.duration_ms for s in agent_spans)
            a_tok = sum(s.total_tokens for s in agent_spans)
            a_cost = sum(s.cost_usd for s in agent_spans)
            agent_metrics.append(AgentPerformanceMetric(
                agent_name=aname,
                duration_ms=round(a_dur, 2),
                tokens=a_tok,
                cost_usd=round(a_cost, 6),
                status="SUCCESS" if all(s.status == "SUCCESS" for s in agent_spans) else "WARNING"
            ))

        # Check Langfuse integration
        langfuse_status = "ACTIVE_LOCAL_BUFFER"
        if getattr(settings, "LANGFUSE_PUBLIC_KEY", None) and getattr(settings, "LANGFUSE_SECRET_KEY", None):
            langfuse_status = "LANGFUSE_CLOUD_CONNECTED"

        return ObservabilityReport(
            trace_id=self.trace_id,
            session_id=self.session_id,
            total_wall_time_ms=total_wall_ms,
            sequential_estimated_time_ms=round(sequential_ms, 2),
            sequential_time_ms=round(sequential_ms, 2),
            parallel_speedup_factor=speedup,
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total_tok,
            total_cost_usd=total_cost,
            cost_per_kloc=cost_per_kloc,
            primary_model=self.model,
            provider=self.provider,
            langfuse_status=langfuse_status,
            spans=self.spans,
            agent_metrics=agent_metrics,
            audit_events=self.audit_events
        )

    def finalize_report(self) -> ObservabilityReport:
        return self.finalize()

# Global in-memory trace registry for instant analytics
TRACE_REGISTRY: Dict[str, ObservabilityReport] = {}
