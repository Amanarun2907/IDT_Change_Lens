import json
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

Base = declarative_base()

class AnalysisSessionModel(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    mode = Column(String, index=True)
    repo_url = Column(String, nullable=True)
    pr_url = Column(String, nullable=True)
    pr_title = Column(String, nullable=True)
    base_ref = Column(String, nullable=True)
    head_ref = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0)

    overall_score = Column(Integer, nullable=True)
    risk_category = Column(String, nullable=True)
    blast_radius = Column(String, nullable=True)
    advisory_recommendation = Column(String, nullable=True)

    total_files_changed = Column(Integer, default=0)
    total_additions = Column(Integer, default=0)
    total_deletions = Column(Integer, default=0)
    critical_findings_count = Column(Integer, default=0)
    security_findings_count = Column(Integer, default=0)
    bug_findings_count = Column(Integer, default=0)

    progress_percent = Column(Integer, default=0)
    current_step = Column(String, default="Initialized")
    raw_report_json = Column(Text, nullable=True)

    def to_summary_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "mode": self.mode,
            "repo_url": self.repo_url,
            "pr_url": self.pr_url,
            "pr_title": self.pr_title,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "status": self.status,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "overall_score": self.overall_score,
            "risk_category": self.risk_category,
            "blast_radius": self.blast_radius,
            "advisory_recommendation": self.advisory_recommendation,
            "total_files_changed": self.total_files_changed,
            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "critical_findings_count": self.critical_findings_count,
            "security_findings_count": self.security_findings_count,
            "bug_findings_count": self.bug_findings_count,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step
        }

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
