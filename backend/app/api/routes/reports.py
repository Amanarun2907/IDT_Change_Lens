from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.services.analysis_service import analysis_service
from app.services.report_service import ReportExportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{session_id}/pdf")
async def download_pdf_report(session_id: str):
    report = await analysis_service.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    pdf_bytes = ReportExportService.export_pdf(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="changelens_{session_id[:8]}.pdf"'}
    )

@router.get("/{session_id}/json")
async def download_json_report(session_id: str):
    report = await analysis_service.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    json_str = ReportExportService.export_json(report)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="changelens_{session_id[:8]}.json"'}
    )
