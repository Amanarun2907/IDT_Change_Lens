import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.schemas import AnalysisReport

class ReportExportService:
    """
    Generates professional PDF and JSON reports from AnalysisReport data.
    """

    @staticmethod
    def export_json(report: AnalysisReport) -> str:
        return json.dumps(report.model_dump(mode="json"), indent=2)

    @staticmethod
    def export_pdf(report: AnalysisReport) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            "ReportSub",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b")
        )
        h2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=14,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        badge_style = ParagraphStyle(
            "BadgeStyle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.white,
            alignment=1
        )

        elements = []

        # Header Title
        elements.append(Paragraph("CHANGELENS — CHANGE INTELLIGENCE REPORT", title_style))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Session: {report.session_id}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceBefore=8, spaceAfter=14))

        # Overview Table
        score = report.risk_assessment.overall_score
        cat = report.risk_assessment.risk_category.value
        cat_color = colors.HexColor("#dc2626") if cat == "CRITICAL" else (colors.HexColor("#ea580c") if cat == "HIGH" else (colors.HexColor("#eab308") if cat == "MEDIUM" else colors.HexColor("#16a34a")))

        meta_data = [
            [
                Paragraph("<b>Analysis Mode:</b>", body_style),
                Paragraph(report.mode.value.upper(), body_style),
                Paragraph("<b>Risk Score:</b>", body_style),
                Paragraph(f"<b>{score} / 100</b> ({cat})", body_style)
            ],
            [
                Paragraph("<b>Target:</b>", body_style),
                Paragraph(report.pr_url or report.repo_url or "Manual Snippet Diff", body_style),
                Paragraph("<b>Blast Radius:</b>", body_style),
                Paragraph(report.risk_assessment.blast_radius.value, body_style)
            ],
            [
                Paragraph("<b>Recommendation:</b>", body_style),
                Paragraph(f"<b>{report.risk_assessment.advisory_recommendation.value}</b>", body_style),
                Paragraph("<b>Files Changed:</b>", body_style),
                Paragraph(f"{report.total_files_changed} (+{report.total_additions} / -{report.total_deletions})", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[100, 180, 100, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Executive Summary
        elements.append(Paragraph("Executive Summary", h2_style))
        elements.append(Paragraph(report.executive_summary, body_style))
        elements.append(Spacer(1, 10))

        # Security Findings
        elements.append(Paragraph(f"Security Findings ({len(report.security_findings)})", h2_style))
        if report.security_findings:
            sec_rows = [["Severity", "Finding Title", "File & Line", "CWE"]]
            for sf in report.security_findings[:8]:
                sec_rows.append([
                    sf.severity.value,
                    sf.vulnerability_title,
                    f"{sf.file_path}:{sf.exact_line}",
                    sf.cwe or "N/A"
                ])
            sec_table = Table(sec_rows, colWidths=[70, 230, 160, 80])
            sec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(sec_table)
        else:
            elements.append(Paragraph("No security vulnerabilities detected by completed checks.", body_style))
        elements.append(Spacer(1, 10))

        # Bug and Logic Findings
        elements.append(Paragraph(f"Bug & Logic Findings ({len(report.bug_findings)})", h2_style))
        if report.bug_findings:
            bug_rows = [["Severity", "Issue Title", "File", "Line Range"]]
            for bf in report.bug_findings[:8]:
                bug_rows.append([
                    bf.severity.value,
                    bf.title,
                    bf.file_path,
                    f"L{bf.line_start}-{bf.line_end}"
                ])
            bug_table = Table(bug_rows, colWidths=[70, 230, 160, 80])
            bug_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('PADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(bug_table)
        else:
            elements.append(Paragraph("No logical defects or boundary condition flaws detected.", body_style))
        elements.append(Spacer(1, 10))

        # Testing Recommendations
        elements.append(Paragraph(f"Test Recommendations ({len(report.test_recommendations)})", h2_style))
        for idx, tr in enumerate(report.test_recommendations[:4], 1):
            t_text = f"<b>{idx}. {tr.test_name}</b> [{tr.priority.value}]<br/>Objective: {tr.objective}<br/>Input: <code>{tr.input_data}</code> &rarr; Expected: <code>{tr.expected_output}</code>"
            elements.append(Paragraph(t_text, body_style))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 10))
        # Checklist
        elements.append(Paragraph("Pre-Merge Review Checklist", h2_style))
        for item in report.risk_assessment.human_review_checklist:
            elements.append(Paragraph(f"[  ] {item}", body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
