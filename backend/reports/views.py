import io
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsChiefDoctor
from appointments.models import Appointment
from lab.models import AnalysisOrder
from patients.models import Patient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_pdf_response(filename):
    """Возвращает HTTP-ответ с заголовками для PDF."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _create_excel_response(filename):
    """Возвращает HTTP-ответ с заголовками для Excel."""
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Patients PDF
# ---------------------------------------------------------------------------

class PatientsPDFView(APIView):
    """GET /api/reports/patients/pdf/"""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements = []

        # Заголовок
        title_style = styles["Title"]
        elements.append(Paragraph("Отчёт по пациентам", title_style))
        elements.append(Spacer(1, 10 * mm))

        # Таблица
        style_normal = styles["Normal"]
        header = [
            Paragraph("<b>№</b>", style_normal),
            Paragraph("<b>ФИО</b>", style_normal),
            Paragraph("<b>Дата рождения</b>", style_normal),
            Paragraph("<b>Пол</b>", style_normal),
            Paragraph("<b>Группа крови</b>", style_normal),
            Paragraph("<b>Телефон</b>", style_normal),
        ]

        data = [header]
        patients = Patient.objects.all().order_by("full_name")
        for idx, p in enumerate(patients, start=1):
            row = [
                str(idx),
                p.full_name,
                p.birth_date.strftime("%d.%m.%Y") if p.birth_date else "",
                p.get_gender_display() if p.gender else "",
                p.blood_group or "",
                p.phone or "",
            ]
            data.append(row)

        col_widths = [15 * mm, 55 * mm, 30 * mm, 25 * mm, 25 * mm, 40 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b5797")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        # Подвал
        elements.append(Spacer(1, 10 * mm))
        footer_style = styles["Italic"]
        elements.append(Paragraph(
            f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            footer_style,
        ))

        doc.build(elements)
        buf.seek(0)

        response = _create_pdf_response("patients_report.pdf")
        response.write(buf.getvalue())
        return response


# ---------------------------------------------------------------------------
# Patients Excel
# ---------------------------------------------------------------------------

class PatientsExcelView(APIView):
    """GET /api/reports/patients/excel/"""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        wb = Workbook()
        ws = wb.active
        ws.title = "Пациенты"

        # Заголовки
        headers = ["№", "ФИО", "Дата рождения", "Пол", "Группа крови", "Телефон", "Email", "Адрес"]
        ws.append(headers)

        # Данные
        patients = Patient.objects.all().order_by("full_name")
        for idx, p in enumerate(patients, start=1):
            ws.append([
                idx,
                p.full_name,
                p.birth_date.strftime("%d.%m.%Y") if p.birth_date else "",
                p.get_gender_display() if p.gender else "",
                p.blood_group or "",
                p.phone or "",
                p.email or "",
                p.address or "",
            ])

        # Автоширина колонок
        for col_cells in ws.columns:
            max_len = 0
            col_letter = col_cells[0].column_letter
            for cell in col_cells:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        response = _create_excel_response("patients_report.xlsx")
        response.write(buf.getvalue())
        return response


# ---------------------------------------------------------------------------
# Analyses PDF
# ---------------------------------------------------------------------------

class AnalysesPDFView(APIView):
    """GET /api/reports/analyses/pdf/"""
    permission_classes = [IsChiefDoctor]

    def get(self, request):
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements = []

        title_style = styles["Title"]
        elements.append(Paragraph("Отчёт по анализам", title_style))
        elements.append(Spacer(1, 10 * mm))

        style_normal = styles["Normal"]
        header = [
            Paragraph("<b>№</b>", style_normal),
            Paragraph("<b>Пациент</b>", style_normal),
            Paragraph("<b>Тип анализа</b>", style_normal),
            Paragraph("<b>Статус</b>", style_normal),
            Paragraph("<b>Назначен</b>", style_normal),
            Paragraph("<b>Завершён</b>", style_normal),
        ]

        data = [header]
        orders = AnalysisOrder.objects.select_related("patient", "analysis_type").all().order_by("-requested_at")
        for idx, o in enumerate(orders, start=1):
            row = [
                str(idx),
                o.patient.full_name,
                o.analysis_type.name,
                o.get_status_display(),
                o.requested_at.strftime("%d.%m.%Y") if o.requested_at else "",
                o.completed_at.strftime("%d.%m.%Y") if o.completed_at else "",
            ]
            data.append(row)

        col_widths = [12 * mm, 55 * mm, 45 * mm, 30 * mm, 25 * mm, 25 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b5797")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 10 * mm))
        footer_style = styles["Italic"]
        elements.append(Paragraph(
            f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            footer_style,
        ))

        doc.build(elements)
        buf.seek(0)

        response = _create_pdf_response("analyses_report.pdf")
        response.write(buf.getvalue())
        return response


# ---------------------------------------------------------------------------
# Doctor Schedule PDF
# ---------------------------------------------------------------------------

class SchedulePDFView(APIView):
    """GET /api/reports/schedule/{doctor_id}/pdf/"""
    permission_classes = [IsChiefDoctor]

    def get(self, request, doctor_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        appointments = (
            Appointment.objects.filter(doctor_id=doctor_id)
            .select_related("patient", "department")
            .order_by("scheduled_at")
        )
        if not appointments.exists():
            raise NotFound("Приёмы для указанного врача не найдены.")

        doctor = appointments[0].doctor if appointments and appointments[0].doctor else None
        doctor_name = doctor.full_name_display if doctor else f"Врач #{doctor_id}"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements = []

        title_style = styles["Title"]
        elements.append(Paragraph(f"Расписание приёмов врача", title_style))
        elements.append(Paragraph(doctor_name, styles["Heading2"]))
        elements.append(Spacer(1, 8 * mm))

        style_normal = styles["Normal"]
        header = [
            Paragraph("<b>№</b>", style_normal),
            Paragraph("<b>Дата и время</b>", style_normal),
            Paragraph("<b>Пациент</b>", style_normal),
            Paragraph("<b>Отделение</b>", style_normal),
            Paragraph("<b>Статус</b>", style_normal),
        ]

        data = [header]
        for idx, a in enumerate(appointments, start=1):
            row = [
                str(idx),
                a.scheduled_at.strftime("%d.%m.%Y %H:%M") if a.scheduled_at else "",
                a.patient.full_name if a.patient else "",
                a.department.name if a.department else "",
                a.get_status_display(),
            ]
            data.append(row)

        col_widths = [12 * mm, 45 * mm, 55 * mm, 45 * mm, 35 * mm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b5797")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 10 * mm))
        footer_style = styles["Italic"]
        elements.append(Paragraph(
            f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            footer_style,
        ))

        doc.build(elements)
        buf.seek(0)

        response = _create_pdf_response(f"schedule_{doctor_id}.pdf")
        response.write(buf.getvalue())
        return response