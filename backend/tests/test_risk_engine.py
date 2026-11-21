from app.analysis.risk_engine import RiskEngine
from app.models.schemas import (
    SecurityFinding, BugFinding, RegressionRisk,
    BlastRadius, RiskCategory, AdvisoryRecommendation, Severity, TestRecommendation
)

def test_risk_engine_low_risk():
    res = RiskEngine.calculate_risk(
        security_findings=[],
        bug_findings=[],
        regression_risks=[],
        blast_radius=BlastRadius.LOCALIZED,
        blast_explanation="Clean change",
        test_recommendations=[]
    )
    assert res.overall_score <= 25
    assert res.risk_category == RiskCategory.LOW
    assert res.advisory_recommendation == AdvisoryRecommendation.APPROVE

def test_risk_engine_critical_security():
    sec_finding = SecurityFinding(
        vulnerability_title="Hardcoded API Key",
        file_path="config.py",
        exact_line=12,
        code_evidence="KEY = '12345'",
        cwe="CWE-798",
        explanation="Secret in code",
        attack_scenario="Attacker extracts key",
        potential_impact="Data breach",
        severity=Severity.CRITICAL,
        confidence=0.95,
        remediation="Use env var"
    )
    res = RiskEngine.calculate_risk(
        security_findings=[sec_finding],
        bug_findings=[],
        regression_risks=[],
        blast_radius=BlastRadius.APPLICATION_WIDE,
        blast_explanation="Cross-service impact",
        test_recommendations=[]
    )
    assert res.overall_score >= 80
    assert res.risk_category == RiskCategory.CRITICAL
    assert res.advisory_recommendation == AdvisoryRecommendation.REQUEST_CHANGES
