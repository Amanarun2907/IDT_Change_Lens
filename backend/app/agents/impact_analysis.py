import logging
from typing import Dict, Any, List
from pathlib import Path
from pydantic import BaseModel
from app.agents.base import BaseAgent
from app.models.schemas import ImpactItem, RegressionRisk, ChangedFile
from app.analysis.dependency_analyzer import DependencyAnalyzer
from app.analysis.call_graph import CallGraphBuilder

logger = logging.getLogger(__name__)

class RegressionWrapper(BaseModel):
    regression_risks: List[RegressionRisk] = []

class ImpactAnalysisAgent(BaseAgent):
    """
    AGENT 5: DEPENDENCY AND CHANGE IMPACT ANALYSIS AGENT
    ChangeLens Signature Agent:
    Traces function definitions, callers, dependent modules, affected APIs,
    builds the interactive impact graph, and evaluates backward compatibility regressions.
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="impact_analysis",
            role="Principal Software Architect & Impact Analysis Specialist",
            llm_service=llm_service
        )

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing ImpactAnalysisAgent...")
        diff_text = state.get("diff_text", "")
        changed_files_raw = state.get("changed_files", [])
        repo_dir = state.get("repo_dir")

        changed_files: List[ChangedFile] = []
        for cf in changed_files_raw:
            if isinstance(cf, ChangedFile):
                changed_files.append(cf)
            elif isinstance(cf, dict):
                changed_files.append(ChangedFile(**cf))

        # 1. Run Repository AST & Call-Graph Dependency Analysis
        dep_analyzer = DependencyAnalyzer(repo_dir=Path(repo_dir) if repo_dir else None)
        impact_items = dep_analyzer.analyze_impact(changed_files)

        # 2. Build React Flow Graph and Blast Radius
        impact_graph, blast_radius, blast_explanation = CallGraphBuilder.build_graph_and_blast_radius(impact_items)

        # 3. LLM Analysis for Backward Compatibility and Contract Regressions
        system_prompt = (
            "You are ChangeLens Regression & Contract Prediction Specialist.\n"
            "Analyze the code diff and downstream callers to detect whether changes break function signatures, "
            "return types, API contracts, or existing callers.\n"
            "Return valid JSON adhering to:\n"
            "{\n"
            '  "regression_risks": [\n'
            "    {\n"
            '      "component": "function_or_module_name",\n'
            '      "change_type": "SIGNATURE" | "RETURN_TYPE" | "API_CONTRACT" | "BEHAVIOR" | "DB_SCHEMA",\n'
            '      "callers_count": 2,\n'
            '      "breaking": true,\n'
            '      "description": "Explains why existing callers could break",\n'
            '      "mitigation": "How to preserve backward compatibility"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Impacted symbols identified: {[item.modified_symbol for item in impact_items]}\n"
            f"Direct callers found: {[caller for item in impact_items for caller in item.direct_callers]}\n"
            f"Affected APIs: {[api for item in impact_items for api in item.affected_apis]}\n\n"
            f"Git Unified Diff:\n"
            f"```\n{diff_text[:10000]}\n```\n\n"
            "Analyze backward compatibility and regression risks. Output JSON."
        )

        regression_risks: List[RegressionRisk] = []
        try:
            res = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_schema=RegressionWrapper
            )
            regression_risks = res.regression_risks
        except Exception as e:
            logger.warning(f"ImpactAnalysisAgent regression LLM failed: {e}")

        return {
            "impact_items": impact_items,
            "impact_graph": impact_graph,
            "blast_radius": blast_radius,
            "blast_radius_explanation": blast_explanation,
            "regression_risks": regression_risks
        }
