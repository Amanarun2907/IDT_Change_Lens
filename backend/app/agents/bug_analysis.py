import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models.schemas import BugFinding, Severity

logger = logging.getLogger(__name__)

class BugReviewWrapper(BaseModel):
    findings: List[BugFinding] = Field(default_factory=list)

class BugAnalysisAgent(BaseAgent):
    """
    AGENT 3: BUG AND LOGIC REVIEW AGENT
    Analyzes changed code for:
    - Logical errors and incorrect condition branches
    - Edge cases, null / None dereferences, and empty collection handling
    - Boundary condition flaws (off-by-one, zero-division, type mismatches)
    - Broken invariants and unexpected runtime exceptions
    - Removed input validation checks and regressions
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="bug_analysis",
            role="Senior Software Quality & Logic Review Engineer",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing BugAnalysisAgent...")
        diff_text = state.get("diff_text", "")
        changed_files = state.get("changed_files", [])

        if not diff_text or not diff_text.strip():
            return {"bug_findings": []}

        file_names = []
        for cf in changed_files:
            if isinstance(cf, dict):
                file_names.append(cf.get("file_path", "unknown"))
            elif hasattr(cf, "file_path"):
                file_names.append(cf.file_path)

        truncated_diff = diff_text[:14000]

        system_prompt = (
            "You are ChangeLens Bug and Logic Review Agent. Your primary role is to detect logical bugs, "
            "unhandled edge cases, boundary conditions, null/empty pointer dereferences, off-by-one errors, "
            "incorrect conditional logic, and regressions introduced by code modifications.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Only flag genuine logic flaws supported by direct evidence in the diff.\n"
            "2. If the code change is harmless (e.g. documentation, comments, variable renaming, simple formatting), "
            "you MUST return an empty findings list: `{\"findings\": []}`.\n"
            "3. Cite exact line numbers and exact code evidence from the diff.\n"
            "4. Return strictly valid JSON matching this schema:\n"
            "{\n"
            '  "findings": [\n'
            "    {\n"
            '      "title": "Concise bug title",\n'
            '      "file_path": "path/to/file.ext",\n'
            '      "line_start": 10,\n'
            '      "line_end": 15,\n'
            '      "evidence": "Exact code statement triggering the bug",\n'
            '      "explanation": "Why this logic causes unexpected behavior or failures",\n'
            '      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            '      "confidence": 0.88,\n'
            '      "potential_impact": "Impact on runtime execution or data integrity",\n'
            '      "recommended_correction": "Exact code fix or refactor suggested"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Changed Files: {file_names}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{truncated_diff}\n```\n\n"
            "Perform rigorous logic analysis on the changed lines. Output findings JSON."
        )

        try:
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=BugReviewWrapper
            )
            return {"bug_findings": result.findings}
        except Exception as e:
            logger.warning(f"BugAnalysisAgent LLM review failed ({e}); executing grounded heuristic inspection.")
            # Heuristic inspection for removed validation / common bugs when LLM is unavailable
            heuristic_findings: List[BugFinding] = []
            
            # Check for removed validation patterns (e.g. - if ... raise or - if ... return error)
            removed_lines = [l[1:].strip() for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---")]
            added_lines = [l[1:].strip() for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
            
            has_removed_guard = any(
                "raise" in rl or "if" in rl or "assert" in rl or "error" in rl.lower() or "<=" in rl or ">=" in rl
                for rl in removed_lines
            )
            has_added_guard = any(
                "raise" in al or "assert" in al or ("if" in al and ("return" in al or "raise" in al))
                for al in added_lines
            )
            
            if has_removed_guard and not has_added_guard:
                heuristic_findings.append(BugFinding(
                    title="Removed Input Validation Check Allows Invalid State",
                    file_path=file_names[0] if file_names else "snippet.py",
                    line_start=1,
                    line_end=10,
                    evidence="Removed guard check: " + "; ".join(removed_lines[:2]),
                    explanation="Input parameter validation check was removed without replacement, allowing non-positive or malformed values to pass through.",
                    severity=Severity.HIGH,
                    confidence=0.85,
                    potential_impact="Silent calculation errors, negative transactions, or unexpected exceptions downstream.",
                    recommended_correction="Restore parameter boundary validation before executing core calculations."
                ))

            # Check for potential division by zero
            for idx, al in enumerate(added_lines, 1):
                if re.search(r"/\s*[a-zA-Z0-9_]+", al) and not re.search(r"if\s+.*!=?\s*0", "\n".join(added_lines)):
                    if "/" in al and not "//" in al and not "http" in al:
                        heuristic_findings.append(BugFinding(
                            title="Potential Zero-Division Without Prior Guard Check",
                            file_path=file_names[0] if file_names else "snippet.py",
                            line_start=idx,
                            line_end=idx,
                            evidence=al,
                            explanation="Denominator variable is used in division without verifying non-zero value.",
                            severity=Severity.MEDIUM,
                            confidence=0.80,
                            potential_impact="ZeroDivisionError exception at runtime.",
                            recommended_correction="Add explicit check: if denominator == 0: raise ValueError(...)"
                        ))
                        break

            return {"bug_findings": heuristic_findings}
