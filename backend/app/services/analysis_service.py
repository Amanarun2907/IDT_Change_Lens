import time
import uuid
import json
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncGenerator
from sqlalchemy import select, update
from app.models.database import AsyncSessionLocal, AnalysisSessionModel
from app.models.schemas import (
    AnalysisMode, AnalysisStatus, ProgressEvent, AnalysisReport,
    RepoAnalysisRequest, PRAnalysisRequest, ManualDiffRequest,
    ChangedFile
)
from app.github.client import GitHubClient
from app.github.repository_manager import RepositoryManager
from app.github.diff_engine import DiffEngine
from app.security.repository_sandbox import RepositorySandbox
from app.security.validators import validate_github_url, validate_git_ref
from app.orchestration.state import MultiAgentState
from app.agents.coordinator import CoordinatorAgent
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Optimized high-performance orchestrator:
    - Non-blocking async execution
    - Instant event replay for smooth UI updates
    - Multi-mode support: GitHub Repo, Pull Request, and Manual Code/Git Diff
    - Parallel specialist agent pipeline and structured review synthesis
    """
    def __init__(self):
        self.active_queues: Dict[str, asyncio.Queue] = {}
        self.event_history: Dict[str, List[ProgressEvent]] = {}
        self.cached_reports: Dict[str, AnalysisReport] = {}

    def get_or_create_queue(self, session_id: str) -> asyncio.Queue:
        if session_id not in self.active_queues:
            self.active_queues[session_id] = asyncio.Queue()
        return self.active_queues[session_id]

    async def emit_progress(self, event: ProgressEvent):
        """Pushes event into queue and persistent in-memory history."""
        if event.session_id not in self.event_history:
            self.event_history[event.session_id] = []
        self.event_history[event.session_id].append(event)

        q = self.active_queues.get(event.session_id)
        if q:
            await q.put(event)

        # Update status in DB
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(AnalysisSessionModel)
                    .where(AnalysisSessionModel.id == event.session_id)
                    .values(
                        progress_percent=event.percent,
                        current_step=event.step_name
                    )
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to update session status in DB: {e}")

    async def stream_progress(self, session_id: str) -> AsyncGenerator[str, None]:
        """SSE generator with historical event replay."""
        if session_id in self.event_history:
            for ev in list(self.event_history[session_id]):
                yield f"data: {json.dumps(ev.model_dump(mode='json'))}\n\n"
                if ev.status in ("completed", "failed") and ev.percent == 100:
                    return

        q = self.get_or_create_queue(session_id)
        try:
            while True:
                try:
                    event: ProgressEvent = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
                    if event.status in ("completed", "failed") and event.percent == 100:
                        break
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        finally:
            pass

    async def start_repo_analysis(self, req: RepoAnalysisRequest) -> str:
        session_id = str(uuid.uuid4())
        validated_info = validate_github_url(req.repo_url)

        async with AsyncSessionLocal() as session:
            db_session = AnalysisSessionModel(
                id=session_id,
                mode=AnalysisMode.GITHUB_REPO.value,
                repo_url=validated_info["normalized_url"],
                base_ref=req.base_branch or "main",
                head_ref=req.target_branch,
                status=AnalysisStatus.QUEUED.value,
                current_step="Queued"
            )
            session.add(db_session)
            await session.commit()

        asyncio.create_task(self._run_repo_analysis(session_id, req, validated_info))
        return session_id

    async def start_pr_analysis(self, req: PRAnalysisRequest) -> str:
        session_id = str(uuid.uuid4())
        validated_info = validate_github_url(req.pr_url)
        if validated_info["type"] != "pr":
            raise ValueError("URL must point to a specific Pull Request (e.g. https://github.com/owner/repo/pull/15)")

        async with AsyncSessionLocal() as session:
            db_session = AnalysisSessionModel(
                id=session_id,
                mode=AnalysisMode.GITHUB_PR.value,
                pr_url=validated_info["normalized_url"],
                status=AnalysisStatus.QUEUED.value,
                current_step="Queued"
            )
            session.add(db_session)
            await session.commit()

        asyncio.create_task(self._run_pr_analysis(session_id, req, validated_info))
        return session_id

    async def start_manual_analysis(self, req: ManualDiffRequest) -> str:
        session_id = str(uuid.uuid4())

        async with AsyncSessionLocal() as session:
            db_session = AnalysisSessionModel(
                id=session_id,
                mode=AnalysisMode.MANUAL_DIFF.value,
                status=AnalysisStatus.QUEUED.value,
                current_step="Queued"
            )
            session.add(db_session)
            await session.commit()

        asyncio.create_task(self._run_manual_analysis(session_id, req))
        return session_id

    # Internal Executors
    async def _run_repo_analysis(self, session_id: str, req: RepoAnalysisRequest, info: Dict[str, Any]):
        start_time = time.time()
        sandbox = RepositorySandbox(session_id)
        try:
            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="Repository Retrieval",
                agent_name="system",
                status="running",
                message=f"Connecting to GitHub API for {info['owner']}/{info['repo']}...",
                percent=5
            ))

            client = GitHubClient(token=req.github_token)

            # Step 1: Fast metadata & language detection via GitHub API with fallback
            repo_info = {}
            detected_languages = ["Python"]
            default_branch = "main"
            try:
                repo_info = await client.get_repo_info(info["owner"], info["repo"])
                detected_languages = await client.get_languages(info["owner"], info["repo"])
                default_branch = repo_info.get("default_branch", "main")
            except Exception as e:
                logger.warning(f"GitHub API metadata retrieval warning: {e}. Proceeding via Git clone.")
            base_ref = req.base_branch or default_branch

            # Step 2: Diff extraction via GitHub Compare API with fallback
            diff_text = ""
            try:
                if req.target_branch and req.target_branch != base_ref:
                    diff_text = await client.get_compare_diff(info["owner"], info["repo"], base_ref, req.target_branch)
                else:
                    commits = await client.get_commits(info["owner"], info["repo"], branch=base_ref, limit=2)
                    if len(commits) >= 2:
                        diff_text = await client.get_compare_diff(info["owner"], info["repo"], commits[1]["sha"], commits[0]["sha"])
                    elif len(commits) == 1:
                        diff_text = await client.get_commit_diff(info["owner"], info["repo"], commits[0]["sha"])
            except Exception as e:
                logger.warning(f"GitHub diff API retrieval warning: {e}. Will extract diff from clone.")

            changed_files = DiffEngine.parse_unified_diff(diff_text)

            # Step 3: Fast shallow clone (depth=1) in background thread
            repo_mgr = RepositoryManager(sandbox, token=req.github_token)
            repo_path = None
            try:
                repo_path = await asyncio.wait_for(
                    asyncio.to_thread(
                        repo_mgr.clone_or_fetch,
                        info["normalized_url"],
                        base_ref,
                        req.target_branch
                    ),
                    timeout=10.0
                )
            except Exception as e:
                logger.warning(f"Shallow clone skipped/timeout: {e}")

            if not changed_files:
                if repo_path:
                    meta = repo_mgr.inspect_project_metadata()
                    if meta["source_files"]:
                        sample_file = meta["source_files"][0]
                        content = repo_mgr.read_file_content(sample_file) or ""
                        changed_files = [ChangedFile(
                            file_path=sample_file,
                            status="modified",
                            additions=len(content.splitlines()),
                            deletions=0,
                            diff_hunks=f"@@ -1,1 +1,{len(content.splitlines())} @@\n+" + "\n+".join(content.splitlines()[:100])
                        )]
                        diff_text = changed_files[0].diff_hunks
                else:
                    sample_readme = await client.get_file_content(info["owner"], info["repo"], "README.md", ref=base_ref)
                    if sample_readme:
                        changed_files = [ChangedFile(
                            file_path="README.md",
                            status="modified",
                            additions=len(sample_readme.splitlines()),
                            deletions=0,
                            diff_hunks=f"@@ -1,1 +1,{len(sample_readme.splitlines())} @@\n+" + "\n+".join(sample_readme.splitlines()[:100])
                        )]
                        diff_text = changed_files[0].diff_hunks

            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="Repository Retrieval",
                agent_name="system",
                status="completed",
                message=f"Retrieved {len(changed_files)} changed file(s).",
                percent=15
            ))

            state = MultiAgentState(
                session_id=session_id,
                mode=AnalysisMode.GITHUB_REPO,
                repo_url=info["normalized_url"],
                base_ref=base_ref,
                head_ref=req.target_branch or "HEAD",
                repo_dir=str(repo_path) if repo_path else None,
                diff_text=diff_text,
                changed_files=changed_files,
                languages=detected_languages or ["Python"]
            )

            coordinator = CoordinatorAgent()
            final_state = await coordinator.orchestrate_analysis(state, progress_cb=self.emit_progress)
            await self._finalize_report(session_id, final_state, start_time)

        except Exception as e:
            logger.exception(f"Repository analysis failed: {e}")
            await self._record_failure(session_id, str(e))
        finally:
            sandbox.cleanup()

    async def _run_pr_analysis(self, session_id: str, req: PRAnalysisRequest, info: Dict[str, Any]):
        start_time = time.time()
        try:
            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="PR Metadata Retrieval",
                agent_name="system",
                status="running",
                message=f"Fetching Pull Request #{info['pr_number']} metadata from GitHub...",
                percent=5
            ))

            client = GitHubClient(token=req.github_token)
            pr_data = {}
            diff_text = ""
            try:
                pr_data = await client.get_pull_request(info["owner"], info["repo"], info["pr_number"])
            except Exception as e:
                logger.warning(f"PR metadata retrieval warning: {e}")
                pr_data = {"title": f"PR #{info['pr_number']}", "base": {"ref": "main"}, "head": {"ref": ""}}

            try:
                diff_text = await client.get_pull_request_diff(info["owner"], info["repo"], info["pr_number"])
            except Exception as e:
                logger.warning(f"PR diff retrieval warning: {e}")

            changed_files = DiffEngine.parse_unified_diff(diff_text)

            langs = list(set([Path(f.file_path).suffix[1:] for f in changed_files if Path(f.file_path).suffix]))

            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="PR Metadata Retrieval",
                agent_name="system",
                status="completed",
                message=f"Retrieved PR #{info['pr_number']} with {len(changed_files)} changed files.",
                percent=15
            ))

            state = MultiAgentState(
                session_id=session_id,
                mode=AnalysisMode.GITHUB_PR,
                pr_url=info["normalized_url"],
                pr_number=info["pr_number"],
                pr_title=pr_data.get("title", f"PR #{info['pr_number']}"),
                base_ref=pr_data.get("base", {}).get("ref", "main"),
                head_ref=pr_data.get("head", {}).get("ref", ""),
                diff_text=diff_text,
                changed_files=changed_files,
                languages=langs or ["code"]
            )

            coordinator = CoordinatorAgent()
            final_state = await coordinator.orchestrate_analysis(state, progress_cb=self.emit_progress)
            await self._finalize_report(session_id, final_state, start_time)

        except Exception as e:
            logger.exception(f"PR analysis failed: {e}")
            await self._record_failure(session_id, str(e))

    async def _run_manual_analysis(self, session_id: str, req: ManualDiffRequest):
        start_time = time.time()
        try:
            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="Diff Normalization",
                agent_name="system",
                status="running",
                message="Normalizing code changes and generating unified diff...",
                percent=10
            ))

            diff_text = DiffEngine.normalize_diff_input(
                original_code=req.original_code,
                updated_code=req.updated_code,
                raw_diff=req.raw_diff,
                filename=req.filename or "snippet.py"
            )
            changed_files = DiffEngine.parse_unified_diff(diff_text)
            if not changed_files:
                changed_files = [ChangedFile(
                    file_path=req.filename or "snippet.py",
                    status="modified",
                    additions=len([l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]),
                    deletions=len([l for l in diff_text.splitlines() if l.startswith("-") and not l.startswith("---")]),
                    diff_hunks=diff_text
                )]

            await self.emit_progress(ProgressEvent(
                session_id=session_id,
                step_id="init",
                step_name="Diff Normalization",
                agent_name="system",
                status="completed",
                message=f"Diff normalized: {len(changed_files)} file change(s) prepared.",
                percent=15
            ))

            state = MultiAgentState(
                session_id=session_id,
                mode=AnalysisMode.MANUAL_DIFF,
                diff_text=diff_text,
                changed_files=changed_files,
                languages=[req.language]
            )

            coordinator = CoordinatorAgent()
            final_state = await coordinator.orchestrate_analysis(state, progress_cb=self.emit_progress)
            await self._finalize_report(session_id, final_state, start_time)

        except Exception as e:
            logger.exception(f"Manual diff analysis failed: {e}")
            await self._record_failure(session_id, str(e))

    async def _finalize_report(self, session_id: str, state: MultiAgentState, start_time: float):
        duration = round(time.time() - start_time, 2)
        total_adds = sum(cf.additions for cf in state.changed_files)
        total_dels = sum(cf.deletions for cf in state.changed_files)

        report = AnalysisReport(
            session_id=session_id,
            mode=state.mode,
            repo_url=state.repo_url,
            pr_url=state.pr_url,
            pr_number=state.pr_number,
            pr_title=state.pr_title,
            base_ref=state.base_ref,
            head_ref=state.head_ref,
            duration_seconds=duration,
            executive_summary=state.executive_summary or "Analysis complete.",
            change_summary=state.change_summary or (state.code_understanding.change_summary if state.code_understanding else ""),
            risk_justification=state.risk_justification or (state.risk_assessment.score_explanation if state.risk_assessment else ""),
            affected_components=state.affected_components or [],
            languages_detected=state.languages,
            frameworks_detected=state.frameworks,
            total_files_changed=len(state.changed_files),
            total_additions=total_adds,
            total_deletions=total_dels,
            changed_files=state.changed_files,
            unified_findings=state.unified_findings,
            code_understanding=state.code_understanding,
            bug_findings=state.bug_findings,
            security_findings=state.security_findings,
            impact_items=state.impact_items,
            impact_graph=state.impact_graph or None,
            regression_risks=state.regression_risks,
            test_recommendations=state.test_recommendations,
            test_execution=state.test_execution,
            review_comments=state.review_comments,
            suggested_fixes=state.suggested_fixes,
            risk_assessment=state.risk_assessment,
            observability=state.observability
        )

        self.cached_reports[session_id] = report

        crit_count = len([f for f in state.unified_findings if f.severity.value == "CRITICAL"])
        sec_count = len([f for f in state.unified_findings if f.category.value == "SECURITY"])
        bug_count = len([f for f in state.unified_findings if f.category.value == "BUG_LOGIC"])

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisSessionModel)
                .where(AnalysisSessionModel.id == session_id)
                .values(
                    status=AnalysisStatus.COMPLETED.value,
                    duration_seconds=duration,
                    overall_score=state.risk_assessment.overall_score if state.risk_assessment else 10,
                    risk_category=state.risk_assessment.risk_category.value if state.risk_assessment else "LOW",
                    blast_radius=state.risk_assessment.blast_radius.value if state.risk_assessment else "LOCALIZED",
                    advisory_recommendation=state.risk_assessment.advisory_recommendation.value if state.risk_assessment else "APPROVE",
                    total_files_changed=len(state.changed_files),
                    total_additions=total_adds,
                    total_deletions=total_dels,
                    critical_findings_count=crit_count,
                    security_findings_count=sec_count,
                    bug_findings_count=bug_count,
                    progress_percent=100,
                    current_step="Completed",
                    raw_report_json=json.dumps(report.model_dump(mode="json"))
                )
            )
            await session.commit()

    async def _record_failure(self, session_id: str, error_msg: str):
        await self.emit_progress(ProgressEvent(
            session_id=session_id,
            step_id="error",
            step_name="Analysis Failed",
            agent_name="system",
            status="failed",
            message=error_msg,
            percent=100
        ))

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisSessionModel)
                .where(AnalysisSessionModel.id == session_id)
                .values(
                    status=AnalysisStatus.FAILED.value,
                    error_message=error_msg,
                    progress_percent=100,
                    current_step="Failed"
                )
            )
            await session.commit()

    async def get_report(self, session_id: str) -> Optional[AnalysisReport]:
        if session_id in self.cached_reports:
            return self.cached_reports[session_id]

        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(AnalysisSessionModel).where(AnalysisSessionModel.id == session_id)
            )
            record = res.scalar_one_or_none()
            if record and record.raw_report_json:
                data = json.loads(record.raw_report_json)
                report = AnalysisReport.model_validate(data)
                self.cached_reports[session_id] = report
                return report
        return None

analysis_service = AnalysisService()
