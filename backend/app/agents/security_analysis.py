import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models.schemas import SecurityFinding, ChangedFile, Severity
from app.analysis.static_analysis import StaticSecurityScanner
from app.security.secret_redaction import redact_secrets

logger = logging.getLogger(__name__)

class SecurityReviewWrapper(BaseModel):
    findings: List[SecurityFinding] = Field(default_factory=list)

class SecurityAnalysisAgent(BaseAgent):
    """
    AGENT 4: SECURITY REVIEW AGENT
    Conducts contextual application security reviews, detects OWASP/CWE vulnerabilities
    (hardcoded credentials, SQL injection, command injection, path traversal, unsafe deserialization,
    insecure auth/authz, sensitive data exposure), provides code-based evidence, and avoids
    generating false findings from keywords alone.
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="security_analysis",
            role="Senior Application Security & Cybersecurity Engineer",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing SecurityAnalysisAgent...")
        diff_text = state.get("diff_text", "")
        changed_files_raw = state.get("changed_files", [])

        # Parse changed files into ChangedFile objects
        changed_files: List[ChangedFile] = []
        for cf in changed_files_raw:
            if isinstance(cf, ChangedFile):
                changed_files.append(cf)
            elif isinstance(cf, dict):
                changed_files.append(ChangedFile(**cf))

        # 1. Run rule-based static security scanner first (fast baseline)
        static_findings = StaticSecurityScanner.scan_changed_files(changed_files)

        if not diff_text or not diff_text.strip():
            return {"security_findings": static_findings}

        truncated_diff = diff_text[:14000]

        system_prompt = (
            "You are ChangeLens Security Review Agent. Conduct contextual application security analysis on code modifications.\n"
            "Examine the code for vulnerabilities: Hard-coded credentials/secrets, SQL injection, Command injection, "
            "SSRF, Path traversal, Insecure deserialization, Broken authentication or authorization, Sensitive data leakage, "
            "and insecure cryptography.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Avoid generating false findings from variable names or harmless keywords alone. "
            "Verify whether the vulnerability is genuinely exploitable in the provided code context.\n"
            "2. NEVER output raw real passwords, secret tokens, or API keys in findings; ALWAYS redact them as [REDACTED].\n"
            "3. If the code changes do not introduce security risks, return an empty findings list: `{\"findings\": []}`.\n"
            "4. Return valid JSON conforming to this schema:\n"
            "{\n"
            '  "findings": [\n'
            "    {\n"
            '      "vulnerability_title": "Vulnerability Title",\n'
            '      "file_path": "path/to/file.ext",\n'
            '      "exact_line": 25,\n'
            '      "code_evidence": "Redacted code snippet demonstrating vulnerability",\n'
            '      "cwe": "CWE-798" | "CWE-89" | "CWE-78" | "CWE-22" | etc.,\n'
            '      "explanation": "Detailed explanation of the security weakness and mechanism",\n'
            '      "attack_scenario": "Realistic exploit scenario demonstrating security impact",\n'
            '      "potential_impact": "Impact on confidentiality, integrity, or system availability",\n'
            '      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            '      "confidence": 0.92,\n'
            '      "remediation": "Concrete developer instructions to secure the code"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Changed files: {[cf.file_path for cf in changed_files]}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{truncated_diff}\n```\n\n"
            "Perform contextual security analysis on modified code. Output JSON."
        )

        llm_findings: List[SecurityFinding] = []
        try:
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=SecurityReviewWrapper
            )
            llm_findings = result.findings
        except Exception as e:
            logger.warning(f"SecurityAnalysisAgent LLM review failed ({e}); using static security findings.")

        # Combine static scanner findings and LLM findings, deduplicating by file, line, and title
        combined: List[SecurityFinding] = list(static_findings)
        seen_keys = {(f.file_path, f.exact_line, f.vulnerability_title.lower()) for f in static_findings}

        for f in llm_findings:
            key = (f.file_path, f.exact_line, f.vulnerability_title.lower())
            if key not in seen_keys:
                f.code_evidence = redact_secrets(f.code_evidence)
                combined.append(f)
                seen_keys.add(key)

        return {"security_findings": combined}
