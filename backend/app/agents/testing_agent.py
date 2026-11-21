import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.models.schemas import TestRecommendation, TestExecutionResult, Severity, ChangedFile
from app.analysis.dependency_analyzer import DependencyAnalyzer
from app.analysis.call_graph import CallGraphBuilder

logger = logging.getLogger(__name__)

class TestRecWrapper(BaseModel):
    test_recommendations: List[TestRecommendation] = Field(default_factory=list)
    potentially_affected_modules: List[str] = Field(default_factory=list)

class TestingAgent(BaseAgent):
    """
    AGENT 5: TESTING AND IMPACT AGENT
    Determines which unit tests, integration tests, regression tests,
    and edge-case tests should be added or executed based on specific code changes.
    Identifies potentially affected modules or downstream functionality.
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="testing_agent",
            role="Senior Test Automation & Impact Verification Specialist",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing TestingAgent...")
        diff_text = state.get("diff_text", "")
        changed_files_raw = state.get("changed_files", [])
        repo_dir_str = state.get("repo_dir")
        repo_dir = Path(repo_dir_str) if repo_dir_str else None

        changed_files: List[ChangedFile] = []
        for cf in changed_files_raw:
            if isinstance(cf, ChangedFile):
                changed_files.append(cf)
            elif isinstance(cf, dict):
                changed_files.append(ChangedFile(**cf))

        # 1. Discover existing test files in repository if repo path available
        existing_test_files = []
        if repo_dir and repo_dir.exists():
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", "__pycache__"}]
                for f in files:
                    if f.startswith("test_") or f.endswith("_test.py") or ".spec." in f or ".test." in f or f.endswith("Test.java"):
                        full_p = Path(root) / f
                        rel_p = str(full_p.relative_to(repo_dir)).replace("\\", "/")
                        existing_test_files.append(rel_p)

        # 2. Run AST Dependency Analyzer for affected modules & blast radius
        dep_analyzer = DependencyAnalyzer(repo_dir=repo_dir)
        impact_items = dep_analyzer.analyze_impact(changed_files)
        impact_graph, blast_radius, blast_explanation = CallGraphBuilder.build_graph_and_blast_radius(impact_items)

        # 3. LLM: Recommend targeted test scenarios
        system_prompt = (
            "You are ChangeLens Testing and Impact Agent.\n"
            "Based on the code changes and affected functions, determine the critical automated tests "
            "that must be added or executed: unit tests, integration tests, regression tests, and edge-case tests.\n"
            "Provide concrete inputs and expected outputs.\n"
            "Return valid JSON matching this schema:\n"
            "{\n"
            '  "test_recommendations": [\n'
            "    {\n"
            '      "test_name": "test_payment_rejects_negative_amount",\n'
            '      "objective": "Verify calculate_payment raises ValueError for negative amounts",\n'
            '      "input_data": "amount = -50.0, discount = 0.1",\n'
            '      "expected_output": "Raises ValueError(\'Amount must be positive\')",\n'
            '      "reason": "Boundary condition test ensuring negative transactions are prevented",\n'
            '      "related_file": "payment_service.py",\n'
            '      "related_function": "calculate_payment",\n'
            '      "priority": "HIGH" | "MEDIUM" | "LOW"\n'
            "    }\n"
            "  ],\n"
            '  "potentially_affected_modules": ["payment_service", "billing_api"]\n'
            "}"
        )

        user_prompt = (
            f"Changed files: {[cf.file_path for cf in changed_files]}\n"
            f"Impacted symbols: {[item.modified_symbol for item in impact_items]}\n"
            f"Existing tests found: {existing_test_files[:8]}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{diff_text[:12000]}\n```\n\n"
            "Determine unit, integration, edge-case, and regression test requirements. Output JSON."
        )

        test_recommendations: List[TestRecommendation] = []
        try:
            res = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=TestRecWrapper
            )
            test_recommendations = res.test_recommendations
        except Exception as e:
            logger.warning(f"TestingAgent LLM call failed ({e}); generating rule-based test recommendations.")
            # Rule-based fallback recommendations
            for cf in changed_files[:2]:
                test_recommendations.append(TestRecommendation(
                    test_name=f"test_{Path(cf.file_path).stem}_regression",
                    objective=f"Verify {cf.file_path} functions execute without unexpected exceptions",
                    input_data="Standard test fixture and boundary values",
                    expected_output="Valid return value matching method contract",
                    reason="Verify backward compatibility following modifications",
                    related_file=cf.file_path,
                    related_function=None,
                    priority=Severity.MEDIUM
                ))

        execution_result = TestExecutionResult(
            tests_recommended=len(test_recommendations),
            tests_found=len(existing_test_files),
            tests_executed=0,
            tests_passed=0,
            tests_failed=0,
            tests_not_executed=len(existing_test_files),
            output_log="Test suites identified; automated execution deferred to human developer approval." if existing_test_files else "No existing automated test suites detected."
        )

        return {
            "test_recommendations": test_recommendations,
            "test_execution": execution_result,
            "impact_items": impact_items,
            "impact_graph": impact_graph,
            "blast_radius": blast_radius,
            "blast_radius_explanation": blast_explanation
        }
