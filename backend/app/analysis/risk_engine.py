from typing import List, Tuple
from app.models.schemas import (
    RiskAssessment, RiskCategory, BlastRadius, AdvisoryRecommendation,
    RiskContributor, SecurityFinding, BugFinding, RegressionRisk,
    TestRecommendation, Severity
)

class RiskEngine:
    """
    Transparent, evidence-based risk scoring engine.
    Calculates explainable 0-100 score based on actual verified findings,
    reachability, security severity, and test coverage.
    """

    @staticmethod
    def calculate_risk(
        security_findings: List[SecurityFinding],
        bug_findings: List[BugFinding],
        regression_risks: List[RegressionRisk],
        blast_radius: BlastRadius,
        blast_explanation: str,
        test_recommendations: List[TestRecommendation]
    ) -> RiskAssessment:
        score = 0
        contributors: List[RiskContributor] = []
        reduction_steps: List[str] = []
        review_checklist: List[str] = []

        # 1. Security Findings Impact
        crit_sec = [f for f in security_findings if f.severity == Severity.CRITICAL]
        high_sec = [f for f in security_findings if f.severity == Severity.HIGH]
        med_sec = [f for f in security_findings if f.severity == Severity.MEDIUM]

        if crit_sec:
            pts = min(len(crit_sec) * 55, 75)
            score += pts
            contributors.append(RiskContributor(
                factor=f"{len(crit_sec)} Critical Security Vulnerability(ies)",
                impact_weight=pts,
                description=f"Identified exploitable flaws ({crit_sec[0].vulnerability_title}) posing severe threat."
            ))
            reduction_steps.append(f"Remediate critical security flaw in {crit_sec[0].file_path} before deployment.")
            review_checklist.append("Verify secrets and input sanitization in modified files.")

        if high_sec:
            pts = min(len(high_sec) * 20, 35)
            score += pts
            contributors.append(RiskContributor(
                factor=f"{len(high_sec)} High-Severity Security Finding(s)",
                impact_weight=pts,
                description=f"Identified high-risk flaws ({high_sec[0].vulnerability_title})."
            ))
            reduction_steps.append("Address high-severity security recommendations.")

        if med_sec and not crit_sec and not high_sec:
            pts = min(len(med_sec) * 8, 15)
            score += pts
            contributors.append(RiskContributor(
                factor=f"{len(med_sec)} Medium Security Finding(s)",
                impact_weight=pts,
                description="Minor security posture concerns detected."
            ))

        # 2. Bug & Logic Findings Impact
        crit_bugs = [b for b in bug_findings if b.severity in (Severity.CRITICAL, Severity.HIGH)]
        med_bugs = [b for b in bug_findings if b.severity == Severity.MEDIUM]

        if crit_bugs:
            pts = min(len(crit_bugs) * 18, 40)
            score += pts
            contributors.append(RiskContributor(
                factor=f"{len(crit_bugs)} High/Critical Logic Bug(s)",
                impact_weight=pts,
                description=f"Logic flaws detected: {crit_bugs[0].title} in {crit_bugs[0].file_path}."
            ))
            reduction_steps.append(f"Fix logical defect: {crit_bugs[0].title}.")
            review_checklist.append("Verify edge case handling for empty inputs and boundary values.")

        if med_bugs and not crit_bugs:
            pts = min(len(med_bugs) * 6, 15)
            score += pts
            contributors.append(RiskContributor(
                factor=f"{len(med_bugs)} Medium Logic Issue(s)",
                impact_weight=pts,
                description="Potential unhandled conditions or formatting discrepancies."
            ))

        # 3. Blast Radius Impact
        if blast_radius == BlastRadius.APPLICATION_WIDE:
            score += 25
            contributors.append(RiskContributor(
                factor="Application-Wide Blast Radius",
                impact_weight=25,
                description="Changes propagate to shared core components and externally exposed APIs."
            ))
            reduction_steps.append("Run full end-to-end regression test suite across dependent services.")
            review_checklist.append("Inspect downstream callers and API consumers for contract breakages.")
        elif blast_radius == BlastRadius.CROSS_MODULE:
            score += 15
            contributors.append(RiskContributor(
                factor="Cross-Module Blast Radius",
                impact_weight=15,
                description="Changes cross module boundaries and impact multiple caller files."
            ))
            reduction_steps.append("Validate cross-module caller integration.")
        elif blast_radius == BlastRadius.MODULE_LEVEL:
            score += 8
            contributors.append(RiskContributor(
                factor="Module-Level Impact",
                impact_weight=8,
                description="Impact affects other functions within the same module."
            ))

        # 4. Regression Risks
        breaking_regs = [r for r in regression_risks if r.breaking]
        if breaking_regs:
            score += 20
            contributors.append(RiskContributor(
                factor="Breaking Interface / Signature Change",
                impact_weight=20,
                description=f"Backward compatibility broken in {breaking_regs[0].component}: {breaking_regs[0].description}"
            ))
            reduction_steps.append(f"Preserve backward compatibility for {breaking_regs[0].component} or update callers.")
            review_checklist.append("Check modified function signatures against all existing callers.")

        # 5. Missing Test Coverage
        high_pri_tests = [t for t in test_recommendations if t.priority in (Severity.CRITICAL, Severity.HIGH)]
        if high_pri_tests:
            score += 12
            contributors.append(RiskContributor(
                factor="Uncovered Critical Paths",
                impact_weight=12,
                description=f"{len(high_pri_tests)} critical test scenarios recommended for modified code."
            ))
            reduction_steps.append("Implement automated unit tests for modified components.")
            review_checklist.append("Ensure unit tests cover null/empty edge cases.")

        # Baseline clamp: 0 to 100
        overall_score = max(5, min(100, score)) if (security_findings or bug_findings or regression_risks or blast_radius != BlastRadius.LOCALIZED) else 5

        # Determine Category
        if overall_score >= 80 or crit_sec:
            risk_category = RiskCategory.CRITICAL
            recommendation = AdvisoryRecommendation.REQUEST_CHANGES
        elif overall_score >= 56 or high_sec or crit_bugs:
            risk_category = RiskCategory.HIGH
            recommendation = AdvisoryRecommendation.REQUEST_CHANGES
        elif overall_score >= 26:
            risk_category = RiskCategory.MEDIUM
            recommendation = AdvisoryRecommendation.NEEDS_HUMAN_REVIEW
        else:
            risk_category = RiskCategory.LOW
            recommendation = AdvisoryRecommendation.APPROVE

        if not reduction_steps:
            reduction_steps.append("Code changes appear clean with low blast radius. Proceed with standard CI verification.")

        if not review_checklist:
            review_checklist.extend([
                "Confirm CI passes successfully.",
                "Verify no unintended debug logs remain.",
                "Ensure commit message clearly describes the change."
            ])

        score_explanation = (
            f"Overall risk evaluated at {overall_score}/100 ({risk_category.value}). "
            f"Primary factors include: {', '.join([c.factor for c in contributors[:3]]) if contributors else 'Clean code changes with localized impact'}."
        )

        return RiskAssessment(
            overall_score=overall_score,
            risk_category=risk_category,
            blast_radius=blast_radius,
            blast_radius_explanation=blast_explanation,
            advisory_recommendation=recommendation,
            contributors=contributors,
            score_explanation=score_explanation,
            recommendations_to_reduce_risk=reduction_steps,
            human_review_checklist=review_checklist
        )
