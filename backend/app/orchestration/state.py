from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from app.models.schemas import (
    AnalysisMode, ChangedFile, CodeUnderstandingOutput,
    BugFinding, SecurityFinding, ImpactItem, ImpactGraph,
    RegressionRisk, TestRecommendation, TestExecutionResult,
    ReviewComment, FixPatch, RiskAssessment, UnifiedFinding,
    ObservabilityReport
)

@dataclass
class MultiAgentState:
    session_id: str
    mode: AnalysisMode
    repo_url: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    base_ref: Optional[str] = None
    head_ref: Optional[str] = None
    repo_dir: Optional[str] = None

    # Context
    diff_text: str = ""
    changed_files: List[ChangedFile] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    # Agent Findings
    code_understanding: Optional[CodeUnderstandingOutput] = None
    bug_findings: List[BugFinding] = field(default_factory=list)
    security_findings: List[SecurityFinding] = field(default_factory=list)
    impact_items: List[ImpactItem] = field(default_factory=list)
    impact_graph: Optional[ImpactGraph] = None
    blast_radius: str = "LOCALIZED"
    blast_radius_explanation: str = ""
    regression_risks: List[RegressionRisk] = field(default_factory=list)
    test_recommendations: List[TestRecommendation] = field(default_factory=list)
    test_execution: Optional[TestExecutionResult] = None
    unified_findings: List[UnifiedFinding] = field(default_factory=list)

    # Synthesis outputs
    review_comments: List[ReviewComment] = field(default_factory=list)
    suggested_fixes: List[FixPatch] = field(default_factory=list)
    risk_assessment: Optional[RiskAssessment] = None
    executive_summary: str = ""
    change_summary: str = ""
    risk_justification: str = ""
    affected_components: List[str] = field(default_factory=list)
    observability: Optional[ObservabilityReport] = None

    # Errors or partial failures
    failed_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "repo_url": self.repo_url,
            "pr_url": self.pr_url,
            "pr_number": self.pr_number,
            "pr_title": self.pr_title,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "repo_dir": self.repo_dir,
            "diff_text": self.diff_text,
            "changed_files": self.changed_files,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "code_understanding": self.code_understanding,
            "bug_findings": self.bug_findings,
            "security_findings": self.security_findings,
            "impact_items": self.impact_items,
            "impact_graph": self.impact_graph,
            "blast_radius": self.blast_radius,
            "blast_radius_explanation": self.blast_radius_explanation,
            "regression_risks": self.regression_risks,
            "test_recommendations": self.test_recommendations,
            "test_execution": self.test_execution,
            "unified_findings": self.unified_findings,
            "review_comments": self.review_comments,
            "suggested_fixes": self.suggested_fixes,
            "risk_assessment": self.risk_assessment,
            "executive_summary": self.executive_summary,
            "change_summary": self.change_summary,
            "risk_justification": self.risk_justification,
            "affected_components": self.affected_components,
            "observability": self.observability,
            "failed_agents": self.failed_agents
        }
