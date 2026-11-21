import logging
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.schemas import CodeUnderstandingOutput, ChangedFile
from app.analysis.ast_analyzer import ASTAnalyzer

logger = logging.getLogger(__name__)

class CodeUnderstandingAgent(BaseAgent):
    """
    AGENT 2: CODE CHANGE ANALYSIS AGENT
    Uses an LLM to understand the diff, summarize what changed,
    identify modified functions, classes, modules, and dependencies,
    and explain the potential functional and architectural impact of the changes.
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="code_understanding",
            role="Senior Software Architect & Code Comprehension Specialist",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing CodeUnderstandingAgent...")
        diff_text = state.get("diff_text", "")
        changed_files_raw = state.get("changed_files", [])
        languages = state.get("languages", ["Python"])
        frameworks = state.get("frameworks", [])

        # Parse changed file names
        changed_file_paths = []
        for cf in changed_files_raw:
            if isinstance(cf, dict):
                changed_file_paths.append(cf.get("file_path", ""))
            elif hasattr(cf, "file_path"):
                changed_file_paths.append(cf.file_path)

        truncated_diff = diff_text[:14000] if len(diff_text) > 14000 else diff_text

        system_prompt = (
            "You are ChangeLens Code Change Analysis Agent. Your responsibility is to deeply understand source code modifications.\n"
            "Analyze the Git unified diff:\n"
            "1. Technical summary of what was added, modified, or removed.\n"
            "2. Inferred intent or purpose (feature, refactor, bugfix, security fix).\n"
            "3. Modified functions, classes, modules, and external dependencies.\n"
            "4. Functional impact on runtime behavior.\n"
            "5. Architectural impact on system design and interfaces.\n"
            "6. Potential behavioral changes and modified public API contracts.\n\n"
            "DO NOT hallucinate symbols not present in the diff.\n"
            "Output strictly valid JSON with this schema:\n"
            "{\n"
            '  "change_summary": "Concise technical summary of modified logic",\n'
            '  "purpose": "Inferred architectural goal or developer intent",\n'
            '  "modified_components": ["function_or_class_1", "function_or_class_2"],\n'
            '  "functional_impact": "How behavior changes for callers or end users",\n'
            '  "architectural_impact": "Impact on system layers, modules, or services",\n'
            '  "potentially_affected_modules": ["affected_module_1"],\n'
            '  "behavioral_changes": ["behavior change description 1"],\n'
            '  "changed_interfaces": ["interface contract change 1"]\n'
            "}"
        )

        user_prompt = (
            f"Repository Context:\n"
            f"- Languages Detected: {', '.join(languages)}\n"
            f"- Frameworks: {', '.join(frameworks) if frameworks else 'Standard Library'}\n"
            f"- Changed Files: {changed_file_paths}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{truncated_diff}\n```\n\n"
            "Analyze the code changes thoroughly and return structured JSON."
        )

        try:
            result = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=CodeUnderstandingOutput
            )
            return {"code_understanding": result}
        except Exception as e:
            logger.warning(f"CodeUnderstandingAgent LLM call failed ({e}); generating AST-grounded fallback.")
            # Grounded AST symbol extraction fallback
            extracted_symbols = []
            for path in changed_file_paths:
                ast_info = ASTAnalyzer.analyze_polyglot_code(diff_text, path)
                extracted_symbols.extend([f["name"] for f in ast_info.get("functions", [])])
                extracted_symbols.extend([c["name"] for c in ast_info.get("classes", [])])

            fallback = CodeUnderstandingOutput(
                change_summary=f"Modified {len(changed_file_paths)} file(s): {', '.join(changed_file_paths[:3])}.",
                purpose="Code modification analysis",
                modified_components=list(set(extracted_symbols))[:5] or changed_file_paths[:3],
                functional_impact="Changes require developer review to confirm intended runtime behavior.",
                architectural_impact="Localized component updates.",
                potentially_affected_modules=changed_file_paths[:3],
                behavioral_changes=["Code modified in active diff hunks."],
                changed_interfaces=[]
            )
            return {"code_understanding": fallback}
