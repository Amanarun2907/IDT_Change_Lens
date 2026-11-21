import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models.schemas import (
    RiskAssessment, ReviewComment, FixPatch,
    BugFinding, SecurityFinding, RegressionRisk,
    TestRecommendation, BlastRadius, UnifiedFinding,
    FindingCategory, Severity, RiskCategory
)
from app.analysis.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

class ReportSynthesisWrapper(BaseModel):
    executive_summary: str = ""
    change_summary: str = ""
    risk_justification: str = ""
    affected_components: List[str] = Field(default_factory=list)
    review_comments: List[ReviewComment] = Field(default_factory=list)
    suggested_fixes: List[FixPatch] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)

class RiskReportAgent(BaseAgent):
    """
    AGENT 6: RISK AND REPORT AGENT
    Consolidates the findings from all specialist agents:
    - Cross-checks reasoning and eliminates unsupported or contradictory claims
    - Deduplicates overlapping findings across specialists
    - Populates standardized UnifiedFinding items with unique identifiers
    - Assigns an overall risk level of LOW, MEDIUM, or HIGH (or CRITICAL where justified)
    - Generates a clear, structured report with prioritized recommendations, executive summary,
      and suggested next steps.
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="risk_report",
            role="Chief Risk Officer & Principal Report Synthesizer",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing RiskReportAgent...")
        security_findings: List[SecurityFinding] = state.get("security_findings", [])
        bug_findings: List[BugFinding] = state.get("bug_findings", [])
        regression_risks: List[RegressionRisk] = state.get("regression_risks", [])
        blast_radius: BlastRadius = state.get("blast_radius", BlastRadius.LOCALIZED)
        blast_explanation: str = state.get("blast_radius_explanation", "Localized changes.")
        test_recommendations: List[TestRecommendation] = state.get("test_recommendations", [])
        diff_text: str = state.get("diff_text", "")
        code_understanding = state.get("code_understanding")

        # 1. Consolidate and deduplicate findings into UnifiedFinding items
        unified_findings: List[UnifiedFinding] = self._consolidate_and_deduplicate(
            bug_findings=bug_findings,
            security_findings=security_findings,
            regression_risks=regression_risks,
            test_recommendations=test_recommendations
        )

        # 2. Calculate evidence-based risk assessment
        risk_assessment = RiskEngine.calculate_risk(
            security_findings=security_findings,
            bug_findings=bug_findings,
            regression_risks=regression_risks,
            blast_radius=blast_radius,
            blast_explanation=blast_explanation,
            test_recommendations=test_recommendations
        )

        # 3. LLM: Synthesize executive summary, cross-check reasoning, and generate fix patches
        system_prompt = (
            "You are ChangeLens Risk and Report Agent.\n"
            "Your task is to synthesize the findings from all specialist agents into an executive review:\n"
            "1. Cross-check specialist reasoning and eliminate any unsupported or duplicate claims.\n"
            "2. Provide a concise technical change summary and affected components.\n"
            "3. State the risk justification grounded strictly in verified findings.\n"
            "4. Generate inline review comments and unified diff fix patches for identified issues.\n"
            "5. Provide actionable next steps for the engineering team.\n\n"
            "Return valid JSON adhering to:\n"
            "{\n"
            '  "executive_summary": "Comprehensive 2-paragraph overview of changes, risks, and verdict",\n'
            '  "change_summary": "Concise summary of functional code changes",\n'
            '  "risk_justification": "Evidence-based justification for the assigned risk level",\n'
            '  "affected_components": ["component1", "component2"],\n'
            '  "review_comments": [\n'
            "    {\n"
            '      "file_path": "path/to/file.py",\n'
            '      "line_number": 24,\n'
            '      "problem": "Concise statement of defect",\n'
            '      "evidence": "Code snippet",\n'
            '      "suggested_improvement": "Actionable feedback"\n'
            "    }\n"
            "  ],\n"
            '  "suggested_fixes": [\n'
            "    {\n"
            '      "issue_title": "Fix title",\n'
            '      "file_path": "path/to/file.py",\n'
            '      "explanation": "Why this resolves the issue",\n'
            '      "unified_diff": "--- a/file.py\\n+++ b/file.py\\n@@ -10,1 +10,3 @@\\n-unsafe()\\n+safe()",\n'
            '      "why_it_helps": "Safety explanation"\n'
            "    }\n"
            "  ],\n"
            '  "suggested_next_steps": ["step 1", "step 2"]\n'
            "}"
        )

        user_prompt = (
            f"Risk Score: {risk_assessment.overall_score}/100 ({risk_assessment.risk_category.value})\n"
            f"Blast Radius: {blast_radius.value} ({blast_explanation})\n"
            f"Advisory Recommendation: {risk_assessment.advisory_recommendation.value}\n"
            f"Consolidated Findings ({len(unified_findings)}): {[f.finding_title for f in unified_findings]}\n"
            f"Recommended Tests ({len(test_recommendations)}): {[t.test_name for t in test_recommendations]}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{diff_text[:12000]}\n```\n\n"
            "Synthesize the consolidated review report. Output JSON."
        )

        exec_summary = (
            f"Change analysis completed with overall risk evaluated at {risk_assessment.overall_score}/100 "
            f"({risk_assessment.risk_category.value}). {len(security_findings)} security finding(s) and "
            f"{len(bug_findings)} logic bug(s) identified. Blast radius assessed as {blast_radius.value}."
        )
        change_summary = code_understanding.change_summary if code_understanding else "Code modification reviewed."
        risk_justification = risk_assessment.score_explanation
        affected_comps = list(set(
            (code_understanding.modified_components if code_understanding else []) +
            [f.file_reference for f in unified_findings if f.file_reference]
        ))
        review_comments: List[ReviewComment] = []
        suggested_fixes: List[FixPatch] = []

        try:
            res = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=ReportSynthesisWrapper
            )
            if res.executive_summary:
                exec_summary = res.executive_summary
            if res.change_summary:
                change_summary = res.change_summary
            if res.risk_justification:
                risk_justification = res.risk_justification
            if res.affected_components:
                affected_comps = res.affected_components
            review_comments = res.review_comments
            suggested_fixes = res.suggested_fixes
            if res.suggested_next_steps:
                risk_assessment.recommendations_to_reduce_risk.extend(res.suggested_next_steps)
        except Exception as e:
            logger.warning(f"RiskReportAgent synthesis LLM call failed ({e}); using rule synthesis.")

        # If LLM didn't produce fix patches for critical/high issues, generate default patch templates
        if not suggested_fixes and unified_findings:
            high_sev_findings = [f for f in unified_findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
            for finding in high_sev_findings[:2]:
                file_p = finding.file_reference or "snippet.py"
                line_no = finding.line_start or 1
                suggested_fixes.append(FixPatch(
                    issue_title=finding.finding_title,
                    file_path=file_p,
                    explanation=f"Remediates {finding.finding_title} by addressing: {finding.explanation}",
                    unified_diff=f"--- a/{file_p}\n+++ b/{file_p}\n@@ -{line_no},1 +{line_no},1 @@\n-{finding.exact_evidence}\n+# TODO: Implement recommended fix: {finding.recommended_fix}",
                    why_it_helps="Prevents defect or security exposure at runtime."
                ))

        return {
            "risk_assessment": risk_assessment,
            "executive_summary": exec_summary,
            "change_summary": change_summary,
            "risk_justification": risk_justification,
            "affected_components": affected_comps,
            "unified_findings": unified_findings,
            "review_comments": review_comments,
            "suggested_fixes": suggested_fixes
        }

    def _consolidate_and_deduplicate(
        self,
        bug_findings: List[BugFinding],
        security_findings: List[SecurityFinding],
        regression_risks: List[RegressionRisk],
        test_recommendations: List[TestRecommendation]
    ) -> List[UnifiedFinding]:
        """
        Deduplicates overlapping findings across Bug, Security, and Regression agents.
        Assigns structured unique identifiers (FIND-001, etc.) and priority order.
        """
        unified: List[UnifiedFinding] = []
        counter = 1
        seen_keys = set()

        # Severity sort order
        severity_rank = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1
        }

        # 1. Process Security Findings (Highest Priority)
        for sec in security_findings:
            key = (sec.file_path.strip().lower(), sec.exact_line, sec.vulnerability_title.strip().lower())
            loc_key = (sec.file_path.strip().lower(), sec.exact_line)
            if key not in seen_keys:
                seen_keys.add(key)
                seen_keys.add(loc_key)
                related_tests = [
                    t.test_name for t in test_recommendations
                    if t.related_file == sec.file_path or sec.vulnerability_title.lower() in t.objective.lower()
                ]
                unified.append(UnifiedFinding(
                    id=f"FIND-{counter:03d}",
                    finding_title=sec.vulnerability_title,
                    category=FindingCategory.SECURITY,
                    severity=sec.severity,
                    confidence=sec.confidence,
                    file_reference=sec.file_path,
                    function_reference=None,
                    line_start=sec.exact_line,
                    line_end=sec.exact_line,
                    exact_evidence=sec.code_evidence,
                    explanation=f"{sec.explanation} Attack Scenario: {sec.attack_scenario}" if sec.attack_scenario else sec.explanation,
                    potential_impact=sec.potential_impact or "Security compromise of application components.",
                    recommended_fix=sec.remediation or "Remediate according to security guidelines.",
                    related_test_cases=related_tests,
                    source_agent="security_analysis",
                    is_ai_generated=True
                ))
                counter += 1

        # 2. Process Bug Findings
        for bug in bug_findings:
            key = (bug.file_path.strip().lower(), bug.line_start, bug.title.strip().lower())
            # Cross-check: If already covered under security at the same location, skip duplicate
            loc_key = (bug.file_path.strip().lower(), bug.line_start)
            if key not in seen_keys and loc_key not in seen_keys:
                seen_keys.add(key)
                seen_keys.add(loc_key)
                related_tests = [
                    t.test_name for t in test_recommendations
                    if t.related_file == bug.file_path or (t.related_function and t.related_function in bug.evidence)
                ]
                unified.append(UnifiedFinding(
                    id=f"FIND-{counter:03d}",
                    finding_title=bug.title,
                    category=FindingCategory.BUG_LOGIC,
                    severity=bug.severity,
                    confidence=bug.confidence,
                    file_reference=bug.file_path,
                    function_reference=None,
                    line_start=bug.line_start,
                    line_end=bug.line_end,
                    exact_evidence=bug.evidence,
                    explanation=bug.explanation,
                    potential_impact=bug.potential_impact or "Unexpected runtime behavior or calculation failure.",
                    recommended_fix=bug.recommended_correction or "Refactor logic to handle boundary conditions.",
                    related_test_cases=related_tests,
                    source_agent="bug_analysis",
                    is_ai_generated=True
                ))
                counter += 1

        # 3. Process Breaking Regression Risks
        for reg in regression_risks:
            if reg.breaking:
                unified.append(UnifiedFinding(
                    id=f"FIND-{counter:03d}",
                    finding_title=f"Breaking Contract in {reg.component}",
                    category=FindingCategory.REGRESSION,
                    severity=Severity.HIGH,
                    confidence=0.90,
                    file_reference=None,
                    function_reference=reg.component,
                    line_start=None,
                    line_end=None,
                    exact_evidence=f"Breaking change type: {reg.change_type} affecting {reg.callers_count} callers.",
                    explanation=reg.description or f"Downstream callers depend on the signature or contract of {reg.component}.",
                    potential_impact="Breaks existing downstream caller integrations.",
                    recommended_fix=reg.mitigation or "Maintain backward compatibility or update all downstream callers.",
                    related_test_cases=[],
                    source_agent="impact_analysis",
                    is_ai_generated=True
                ))
                counter += 1

        # Sort prioritized by severity (CRITICAL -> HIGH -> MEDIUM -> LOW)
        unified.sort(key=lambda f: severity_rank.get(f.severity, 0), reverse=True)
        return unified
