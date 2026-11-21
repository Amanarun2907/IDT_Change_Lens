import pytest
import time
from app.observability.tracer import ObservabilityTracker, TRACE_REGISTRY
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tracker_span_creation_and_cost():
    tracker = ObservabilityTracker(session_id="test_obs_session_1")
    
    # Root span
    root = tracker.start_span("test_root")
    time.sleep(0.01) # 10ms
    
    # Child span with tokens
    child = tracker.start_span(
        name="agent:security_analysis",
        parent_span_id=root.span_id,
        agent_name="agent:security_analysis",
        model_name="llama-3.3-70b-versatile",
        input_data={"code": "password = '123'"}
    )
    time.sleep(0.02) # 20ms
    
    # End child span with token usage
    tracker.end_span(
        span_id=child.span_id,
        status="COMPLETED",
        prompt_tokens=1000,
        completion_tokens=500,
        output_data={"findings": [{"title": "Hardcoded secret"}]}
    )
    
    # End root span
    tracker.end_span(span_id=root.span_id, status="COMPLETED")
    
    report = tracker.finalize_report()
    
    assert report.session_id == "test_obs_session_1"
    assert len(report.spans) == 2
    assert report.total_prompt_tokens == 1000
    assert report.total_completion_tokens == 500
    assert report.total_tokens == 1500
    # Cost for Groq 70b: (1000/1M * 0.59) + (500/1M * 0.79) = 0.00059 + 0.000395 = 0.000985
    assert report.total_cost_usd > 0
    assert len(report.agent_metrics) >= 1
    assert any(m.agent_name == "agent:security_analysis" for m in report.agent_metrics)
    assert len(report.audit_events) >= 2


def test_tracker_concurrency_speedup():
    tracker = ObservabilityTracker(session_id="test_obs_session_speedup")
    root = tracker.start_span("orchestration")
    
    # Simulate 3 parallel agent spans
    s1 = tracker.start_span("agent:bug_analysis", agent_name="agent:bug_analysis", model_name="gemini-2.5-flash")
    s2 = tracker.start_span("agent:security_analysis", agent_name="agent:security_analysis", model_name="gemini-2.5-flash")
    s3 = tracker.start_span("agent:testing_agent", agent_name="agent:testing_agent", model_name="gemini-2.5-flash")
    
    time.sleep(0.02)
    
    tracker.end_span(s1.span_id, prompt_tokens=200, completion_tokens=100)
    tracker.end_span(s2.span_id, prompt_tokens=200, completion_tokens=100)
    tracker.end_span(s3.span_id, prompt_tokens=200, completion_tokens=100)
    tracker.end_span(root.span_id)
    
    report = tracker.finalize_report()
    assert report.sequential_time_ms >= report.total_wall_time_ms
    assert report.parallel_speedup_factor >= 1.0


def test_observability_endpoints():
    # Populate a trace in TRACE_REGISTRY
    tracker = ObservabilityTracker(session_id="sample_reg_session")
    root = tracker.start_span("test_span", agent_name="agent:code_understanding")
    tracker.end_span(root.span_id, prompt_tokens=500, completion_tokens=200)
    rep = tracker.finalize_report()
    TRACE_REGISTRY["sample_reg_session"] = rep
    
    # Overview endpoint
    resp = client.get("/api/observability/overview")
    assert resp.status_code == 200
    overview = resp.json()
    assert overview["total_sessions_tracked"] >= 1
    assert overview["total_tokens_consumed"] >= 700
    assert "agent_performance" in overview
    
    # Trace by session ID endpoint
    trace_resp = client.get("/api/observability/trace/sample_reg_session")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["session_id"] == "sample_reg_session"
    assert len(trace_data["spans"]) >= 1
    
    # Non-existent session
    not_found = client.get("/api/observability/trace/non_existent_123456")
    assert not_found.status_code == 404
