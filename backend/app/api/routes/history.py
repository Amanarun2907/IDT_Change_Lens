from fastapi import APIRouter, Query
from typing import Optional, List
from sqlalchemy import select, desc, func
from app.models.database import AsyncSessionLocal, AnalysisSessionModel

router = APIRouter(prefix="/history", tags=["History"])

@router.get("")
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None)
):
    async with AsyncSessionLocal() as session:
        query = select(AnalysisSessionModel).order_by(desc(AnalysisSessionModel.created_at))

        if status:
            query = query.where(AnalysisSessionModel.status == status)
        if risk_category:
            query = query.where(AnalysisSessionModel.risk_category == risk_category)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        sessions = result.scalars().all()

        count_query = select(func.count(AnalysisSessionModel.id))
        total_count = (await session.execute(count_query)).scalar() or 0

        return {
            "total": total_count,
            "items": [s.to_summary_dict() for s in sessions]
        }

@router.get("/stats")
async def get_dashboard_stats():
    """
    Computes real metrics from persisted SQLite analysis sessions.
    """
    async with AsyncSessionLocal() as session:
        # Total analyses
        total_res = await session.execute(select(func.count(AnalysisSessionModel.id)))
        total_analyses = total_res.scalar() or 0

        # Critical findings sum
        crit_res = await session.execute(select(func.sum(AnalysisSessionModel.critical_findings_count)))
        total_critical = crit_res.scalar() or 0

        # High risk changes
        high_risk_res = await session.execute(
            select(func.count(AnalysisSessionModel.id)).where(
                AnalysisSessionModel.risk_category.in_(["HIGH", "CRITICAL"])
            )
        )
        high_risk_changes = high_risk_res.scalar() or 0

        # Security vulnerabilities sum
        sec_res = await session.execute(select(func.sum(AnalysisSessionModel.security_findings_count)))
        total_security_vulns = sec_res.scalar() or 0

        # Average risk score
        avg_score_res = await session.execute(
            select(func.avg(AnalysisSessionModel.overall_score)).where(
                AnalysisSessionModel.overall_score.isnot(None)
            )
        )
        avg_score = round(avg_score_res.scalar() or 0, 1)

        # Recent 6 analyses
        recent_res = await session.execute(
            select(AnalysisSessionModel).order_by(desc(AnalysisSessionModel.created_at)).limit(6)
        )
        recent_items = [s.to_summary_dict() for s in recent_res.scalars().all()]

        # Trend data from recent sessions
        trend_res = await session.execute(
            select(
                AnalysisSessionModel.id,
                AnalysisSessionModel.created_at,
                AnalysisSessionModel.overall_score,
                AnalysisSessionModel.risk_category
            ).where(AnalysisSessionModel.overall_score.isnot(None))
            .order_by(AnalysisSessionModel.created_at)
            .limit(15)
        )
        trends = [
            {
                "session_id": row.id[:8],
                "date": row.created_at.strftime("%b %d, %H:%M") if row.created_at else "",
                "score": row.overall_score or 0,
                "category": row.risk_category or "LOW"
            }
            for row in trend_res.all()
        ]

        return {
            "total_analyses": total_analyses,
            "critical_findings": total_critical,
            "high_risk_changes": high_risk_changes,
            "security_vulnerabilities": total_security_vulns,
            "average_risk_score": avg_score,
            "recent_analyses": recent_items,
            "trends": trends
        }
