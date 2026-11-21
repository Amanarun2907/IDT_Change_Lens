import asyncio
import logging
from typing import Dict, Any, Callable, Optional, Awaitable
from app.agents.base import BaseAgent
from app.agents.code_understanding import CodeUnderstandingAgent
from app.agents.bug_analysis import BugAnalysisAgent
from app.agents.security_analysis import SecurityAnalysisAgent
from app.agents.testing_agent import TestingAgent
from app.agents.risk_report import RiskReportAgent
from app.orchestration.state import MultiAgentState
from app.models.schemas import ProgressEvent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[ProgressEvent], Awaitable[None]]

class CoordinatorAgent(BaseAgent):
    """
    AGENT 1: COORDINATOR / ORCHESTRATOR AGENT
    Central orchestrator:
    - Receives the code change, understands the review objective, and prepares relevant context
    - Delegates analysis to the specialist agents
    - Collects their structured responses in parallel
    - Coordinates the final consolidated review and risk assessment
    - Emits live execution progress events to the client
    """
    def __init__(self, llm_service=None):
        super().__init__(
            name="coordinator",
            role="Lead Multi-Agent Systems Architect & Coordinator",
            llm_service=llm_service
        )
        self.code_agent = CodeUnderstandingAgent(llm_service)
        self.bug_agent = BugAnalysisAgent(llm_service)
        self.security_agent = SecurityAnalysisAgent(llm_service)
        self.testing_agent = TestingAgent(llm_service)
        self.report_agent = RiskReportAgent(llm_service)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinator interface compliance."""
        return state

    async def orchestrate_analysis(
        self,
        state: MultiAgentState,
        progress_cb: Optional[ProgressCallback] = None
    ) -> MultiAgentState:
        """
        Executes the full multi-agent pipeline with parallel specialist investigation.
        """
        async def notify(step_id: str, step_name: str, agent_name: str, status: str, message: str, percent: int, data: Optional[Dict[str, Any]] = None):
            if progress_cb:
                event = ProgressEvent(
                    session_id=state.session_id,
                    step_id=step_id,
                    step_name=step_name,
                    agent_name=agent_name,
                    status=status,
                    message=message,
                    percent=percent,
                    data=data
                )
                try:
                    await progress_cb(event)
                except Exception as e:
                    logger.warning(f"Failed to publish progress event: {e}")

        # Phase 1: Planning
        await notify("plan", "Coordinator Planning", self.name, "running", "Analyzing review objectives and preparing multi-agent context...", 10)
        logger.info(f"Session {state.session_id}: Planning multi-agent analysis for {len(state.changed_files)} files.")
        await notify("plan", "Coordinator Planning", self.name, "completed", f"Context prepared: {len(state.changed_files)} file(s), delegating to specialist agents.", 20)

        # Phase 2: Code Change Analysis Agent
        await notify("code_understanding", "Code Change Analysis", self.code_agent.name, "running", "Comprehending diff, intent, modified functions, and architectural impact...", 25)
        try:
            res_code = await self.code_agent.execute(state.to_dict())
            state.code_understanding = res_code.get("code_understanding")
            await notify("code_understanding", "Code Change Analysis", self.code_agent.name, "completed", "Code comprehension completed.", 45)
        except Exception as e:
            logger.error(f"CodeUnderstandingAgent failed: {e}")
            state.failed_agents.append(self.code_agent.name)
            await notify("code_understanding", "Code Change Analysis", self.code_agent.name, "failed", f"Code understanding error: {e}", 45)

        # Phase 3: Parallel Execution of Specialists (Bug, Security, Testing & Impact)
        await notify("specialists", "Specialist Investigation", "multi_agents", "running", "Executing Bug & Logic, Security Review, and Testing & Impact specialists in parallel...", 50)

        shared_dict = state.to_dict()

        async def run_specialist(agent: BaseAgent):
            try:
                res = await agent.execute(shared_dict)
                return agent.name, res, None
            except Exception as e:
                logger.error(f"Specialist {agent.name} failed: {e}")
                return agent.name, None, str(e)

        specialist_tasks = [
            run_specialist(self.bug_agent),
            run_specialist(self.security_agent),
            run_specialist(self.testing_agent)
        ]

        results = await asyncio.gather(*specialist_tasks)

        for agent_name, result, error in results:
            if error:
                state.failed_agents.append(agent_name)
                continue
            if result:
                if "bug_findings" in result:
                    state.bug_findings = result["bug_findings"]
                if "security_findings" in result:
                    state.security_findings = result["security_findings"]
                if "impact_items" in result:
                    state.impact_items = result["impact_items"]
                if "impact_graph" in result:
                    state.impact_graph = result["impact_graph"]
                if "blast_radius" in result:
                    state.blast_radius = result["blast_radius"]
                if "blast_radius_explanation" in result:
                    state.blast_radius_explanation = result["blast_radius_explanation"]
                if "regression_risks" in result:
                    state.regression_risks = result["regression_risks"]
                if "test_recommendations" in result:
                    state.test_recommendations = result["test_recommendations"]
                if "test_execution" in result:
                    state.test_execution = result["test_execution"]

        await notify("specialists", "Specialist Investigation", "multi_agents", "completed", "Specialist reviews completed and findings gathered.", 75)

        # Phase 4: Risk and Report Agent (Synthesis, Deduplication, Cross-Checking, Unified Findings)
        await notify("risk_report", "Risk & Report Synthesis", self.report_agent.name, "running", "Cross-checking claims, deduplicating findings, and compiling prioritized report...", 80)
        try:
            report_res = await self.report_agent.execute(state.to_dict())
            state.risk_assessment = report_res.get("risk_assessment")
            state.executive_summary = report_res.get("executive_summary", "")
            state.change_summary = report_res.get("change_summary", "")
            state.risk_justification = report_res.get("risk_justification", "")
            state.affected_components = report_res.get("affected_components", [])
            state.unified_findings = report_res.get("unified_findings", [])
            state.review_comments = report_res.get("review_comments", [])
            state.suggested_fixes = report_res.get("suggested_fixes", [])
            await notify("risk_report", "Risk & Report Synthesis", self.report_agent.name, "completed", "Consolidated review compiled successfully.", 95)
        except Exception as e:
            logger.error(f"Report agent failed: {e}")
            state.failed_agents.append(self.report_agent.name)
            await notify("risk_report", "Risk & Report Synthesis", self.report_agent.name, "failed", f"Report generation error: {e}", 95)

        await notify("complete", "Analysis Complete", self.name, "completed", "All agentic review workflows concluded.", 100)
        return state
