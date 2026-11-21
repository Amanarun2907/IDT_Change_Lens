import pytest
from app.models.schemas import (
    ManualDiffRequest, AnalysisMode, Severity, FindingCategory, UnifiedFinding
)
from app.orchestration.state import MultiAgentState
from app.agents.coordinator import CoordinatorAgent
from app.agents.risk_report import RiskReportAgent
from app.models.schemas import BugFinding, SecurityFinding

@pytest.mark.asyncio
async def test_coordinator_agent_orchestration():
    state = MultiAgentState(
        session_id="test-session-agent",
        mode=AnalysisMode.MANUAL_DIFF,
        diff_text="--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,3 @@\n def calc(x):\n-    return 10 / x\n+    if x == 0: raise ValueError()\n+    return 10 / x",
        languages=["python"]
    )
    coordinator = CoordinatorAgent()
    final_state = await coordinator.orchestrate_analysis(state)
    assert final_state.risk_assessment is not None
    assert final_state.risk_assessment.overall_score >= 0
    assert final_state.code_understanding is not None

def test_risk_report_deduplication():
    agent = RiskReportAgent()
    bug = BugFinding(
        title="Unvalidated Password",
        file_path="auth.py",
        line_start=15,
        line_end=15,
        evidence="passwd = '123'",
        explanation="Hardcoded password",
        severity=Severity.HIGH,
        confidence=0.9
    )
    sec = SecurityFinding(
        vulnerability_title="Hardcoded Password Detected",
        file_path="auth.py",
        exact_line=15,
        code_evidence="passwd = '[REDACTED]'",
        cwe="CWE-798",
        explanation="Hardcoded secret in source code",
        severity=Severity.CRITICAL,
        confidence=0.95
    )

    unified = agent._consolidate_and_deduplicate(
        bug_findings=[bug],
        security_findings=[sec],
        regression_risks=[],
        test_recommendations=[]
    )

    # Should deduplicate line 15 and prioritize the security finding
    assert len(unified) == 1
    assert unified[0].category == FindingCategory.SECURITY
    assert unified[0].severity == Severity.CRITICAL
    assert unified[0].id == "FIND-001"
