from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AnalysisMode(str, Enum):
    GITHUB_REPO = "github_repo"
    GITHUB_PR = "github_pr"
    MANUAL_DIFF = "manual_diff"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BlastRadius(str, Enum):
    LOCALIZED = "LOCALIZED"
    MODULE_LEVEL = "MODULE_LEVEL"
    CROSS_MODULE = "CROSS_MODULE"
    APPLICATION_WIDE = "APPLICATION_WIDE"

class AdvisoryRecommendation(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"

class FindingCategory(str, Enum):
    BUG_LOGIC = "BUG_LOGIC"
    SECURITY = "SECURITY"
    REGRESSION = "REGRESSION"
    EDGE_CASE = "EDGE_CASE"
    TESTING_GAP = "TESTING_GAP"
    PERFORMANCE = "PERFORMANCE"
    CODE_QUALITY = "CODE_QUALITY"

# Request Schemas
class RepoAnalysisRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")
    base_branch: Optional[str] = Field("main", description="Base branch or commit")
    target_branch: Optional[str] = Field(None, description="Target branch or comparison commit")
    commit_sha: Optional[str] = Field(None, description="Optional specific commit comparison")
    analysis_depth: Optional[str] = Field("comprehensive", description="shallow | standard | comprehensive")
    github_token: Optional[str] = Field(None, description="GitHub token for private repos or rate limit elevation")

class PRAnalysisRequest(BaseModel):
    pr_url: str = Field(..., description="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/15)")
    analysis_depth: Optional[str] = Field("comprehensive", description="shallow | standard | comprehensive")
    github_token: Optional[str] = Field(None, description="GitHub token for private repos or rate limit elevation")

class ManualDiffRequest(BaseModel):
    original_code: Optional[str] = Field(None, description="Original code before changes")
    updated_code: Optional[str] = Field(None, description="Updated code after changes")
    raw_diff: Optional[str] = Field(None, description="Raw unified Git diff string")
    language: str = Field("python", description="Language of the code (python, javascript, typescript, java, etc.)")
    filename: Optional[str] = Field("snippet.py", description="Filename or path context")

# Sub-structures
class ChangedFile(BaseModel):
    file_path: str
    status: str = Field("modified", description="added | modified | deleted | renamed")
    additions: int = 0
    deletions: int = 0
    old_path: Optional[str] = None
    diff_hunks: Optional[str] = None

class CodeUnderstandingOutput(BaseModel):
    change_summary: str = ""
    purpose: str = ""
    modified_components: List[str] = Field(default_factory=list)
    functional_impact: str = ""
    architectural_impact: str = ""
    potentially_affected_modules: List[str] = Field(default_factory=list)
    behavioral_changes: List[str] = Field(default_factory=list)
    changed_interfaces: List[str] = Field(default_factory=list)

class BugFinding(BaseModel):
    title: str
    file_path: str
    line_start: int = 1
    line_end: int = 1
    evidence: str
    explanation: str
    severity: Severity = Severity.MEDIUM
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    potential_impact: str = ""
    recommended_correction: str = ""

class SecurityFinding(BaseModel):
    vulnerability_title: str
    file_path: str
    exact_line: int = 1
    code_evidence: str
    cwe: Optional[str] = None
    explanation: str
    attack_scenario: str = ""
    potential_impact: str = ""
    severity: Severity = Severity.HIGH
    confidence: float = Field(0.9, ge=0.0, le=1.0)
    remediation: str = ""

# Unified Finding Schema (Enriched and Standardized)
class UnifiedFinding(BaseModel):
    id: str = Field(..., description="Unique finding ID (e.g. FIND-001)")
    finding_title: str
    category: FindingCategory = FindingCategory.BUG_LOGIC
    severity: Severity = Severity.MEDIUM
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    file_reference: Optional[str] = None
    function_reference: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    exact_evidence: str = Field(..., description="Exact code or diff snippet")
    explanation: str = Field(..., description="Why this is an issue")
    potential_impact: str = ""
    recommended_fix: str = ""
    related_test_cases: List[str] = Field(default_factory=list)
    source_agent: str = Field("coordinator", description="Agent or scanner that produced the finding")
    is_ai_generated: bool = True

class ImpactItem(BaseModel):
    modified_symbol: str
    symbol_type: str = Field("function", description="function | class | variable | api_route")
    file_path: str
    direct_callers: List[str] = Field(default_factory=list)
    indirect_callers: List[str] = Field(default_factory=list)
    dependent_modules: List[str] = Field(default_factory=list)
    affected_apis: List[str] = Field(default_factory=list)
    impact_type: str = Field("DIRECT", description="DIRECT | INDIRECT | DEPENDENCY | API | DATA_FLOW | ARCHITECTURAL")
    verified: bool = Field(True, description="True if proven by static AST/call graph, False if inferred")

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = Field("FUNCTION", description="FILE | FUNCTION | CLASS | API | SERVICE")
    severity: Optional[str] = "LOW"
    status: str = Field("MODIFIED", description="MODIFIED | CALLER | DEPENDENT | TARGET")
    details: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = "calls"
    relationship: str = Field("CALLS", description="CALLS | IMPORTS | DEPENDS_ON | EXPOSES")
    verified: bool = True

class ImpactGraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)

class TestRecommendation(BaseModel):
    __test__ = False  # Instruct pytest to not treat this as a test class
    test_name: str
    objective: str
    input_data: str
    expected_output: str
    reason: str
    related_file: str
    related_function: Optional[str] = None
    priority: Severity = Severity.MEDIUM

class TestExecutionResult(BaseModel):
    __test__ = False  # Instruct pytest to not treat this as a test class
    tests_recommended: int = 0
    tests_found: int = 0
    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_not_executed: int = 0
    output_log: Optional[str] = None

class RegressionRisk(BaseModel):
    component: str
    change_type: str = Field("BEHAVIOR", description="SIGNATURE | RETURN_TYPE | API_CONTRACT | BEHAVIOR | DB_SCHEMA")
    callers_count: int = 0
    breaking: bool = False
    description: str = ""
    mitigation: str = ""

class ReviewComment(BaseModel):
    file_path: str
    line_number: int = 1
    problem: str
    evidence: str
    suggested_improvement: str

class FixPatch(BaseModel):
    issue_title: str
    file_path: str
    explanation: str
    unified_diff: str
    why_it_helps: str

class RiskContributor(BaseModel):
    factor: str
    impact_weight: int = Field(..., ge=0, le=100)
    description: str

class RiskAssessment(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    risk_category: RiskCategory
    blast_radius: BlastRadius
    blast_radius_explanation: str
    advisory_recommendation: AdvisoryRecommendation
    contributors: List[RiskContributor] = Field(default_factory=list)
    score_explanation: str = ""
    recommendations_to_reduce_risk: List[str] = Field(default_factory=list)
    human_review_checklist: List[str] = Field(default_factory=list)

# Full Consolidated Report
class AnalysisReport(BaseModel):
    session_id: str
    mode: AnalysisMode
    repo_url: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    base_ref: Optional[str] = None
    head_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    duration_seconds: float = 0.0

    # Summary & Impact
    executive_summary: str = ""
    change_summary: str = ""
    risk_justification: str = ""
    affected_components: List[str] = Field(default_factory=list)
    languages_detected: List[str] = Field(default_factory=list)
    frameworks_detected: List[str] = Field(default_factory=list)
    total_files_changed: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    changed_files: List[ChangedFile] = Field(default_factory=list)

    # Consolidated & Prioritized Findings
    unified_findings: List[UnifiedFinding] = Field(default_factory=list)

    # Specialist outputs
    code_understanding: Optional[CodeUnderstandingOutput] = None
    bug_findings: List[BugFinding] = Field(default_factory=list)
    security_findings: List[SecurityFinding] = Field(default_factory=list)
    impact_items: List[ImpactItem] = Field(default_factory=list)
    impact_graph: ImpactGraph = Field(default_factory=ImpactGraph)
    regression_risks: List[RegressionRisk] = Field(default_factory=list)
    test_recommendations: List[TestRecommendation] = Field(default_factory=list)
    test_execution: TestExecutionResult = Field(default_factory=TestExecutionResult)
    review_comments: List[ReviewComment] = Field(default_factory=list)
    suggested_fixes: List[FixPatch] = Field(default_factory=list)
    risk_assessment: RiskAssessment

# Progress Event for SSE / WebSocket
class ProgressEvent(BaseModel):
    session_id: str
    step_id: str
    step_name: str
    agent_name: Optional[str] = None
    status: str = Field("running", description="pending | running | completed | failed")
    message: str
    percent: int = Field(0, ge=0, le=100)
    timestamp: datetime = Field(default_factory=utc_now)
    data: Optional[Dict[str, Any]] = None
