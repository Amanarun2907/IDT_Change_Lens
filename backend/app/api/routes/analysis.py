from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import RepoAnalysisRequest, PRAnalysisRequest, ManualDiffRequest, AnalysisReport
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/repo")
async def analyze_repository(req: RepoAnalysisRequest):
    try:
        session_id = await analysis_service.start_repo_analysis(req)
        return {"session_id": session_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate repo analysis: {str(e)}")

@router.post("/pr")
async def analyze_pull_request(req: PRAnalysisRequest):
    try:
        session_id = await analysis_service.start_pr_analysis(req)
        return {"session_id": session_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate PR analysis: {str(e)}")

@router.post("/manual")
async def analyze_manual_diff(req: ManualDiffRequest):
    try:
        session_id = await analysis_service.start_manual_analysis(req)
        return {"session_id": session_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate manual analysis: {str(e)}")

@router.get("/{session_id}/stream")
async def stream_analysis_progress(session_id: str):
    return StreamingResponse(
        analysis_service.stream_progress(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{session_id}/report", response_model=AnalysisReport)
async def get_analysis_report(session_id: str):
    report = await analysis_service.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found or still processing.")
    return report
