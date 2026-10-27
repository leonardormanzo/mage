from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_report_pdf(*, company_name: str, project_name: str, report, records: list) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ARC COPILOT · RELATÓRIO DIÁRIO DE OBRA", styles["Title"]),
        Spacer(1, 5 * mm),
        Paragraph(f"Empresa: {company_name}", styles["BodyText"]),
        Paragraph(f"Obra: {project_name}", styles["BodyText"]),
        Paragraph(f"Data: {report.report_date.strftime('%d/%m/%Y')}", styles["BodyText"]),
        Paragraph(f"Status: {report.status.upper()}", styles["BodyText"]),
        Spacer(1, 6 * mm),
    ]
    data = [["Tipo", "Descrição", "Quantidade", "Situação"]]
    for record in records:
        description = record.service or record.evidence_text
        quantity = (
            f"{record.quantity:g} {record.unit or ''}"
            if record.quantity is not None
            else "Não informado"
        )
        data.append([record.record_type, description, quantity, "Confirmado"])
    if len(data) == 1:
        data.append(["—", "Não informado", "Não informado", "—"])
    table = Table(data, colWidths=[34 * mm, 82 * mm, 30 * mm, 28 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15372f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b7c7c2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f7f5")]),
            ]
        )
    )
    story.extend([table, Spacer(1, 8 * mm)])
    if not report.weather:
        story.append(Paragraph("Clima: Não informado", styles["BodyText"]))
    if report.workforce is None:
        story.append(Paragraph("Efetivo: Não informado", styles["BodyText"]))
    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("Responsável: ____________________________________", styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()
