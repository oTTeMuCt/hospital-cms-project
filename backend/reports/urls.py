from django.urls import path

from .views import (
    PatientsPDFView,
    PatientsExcelView,
    AnalysesPDFView,
    SchedulePDFView,
)

urlpatterns = [
    path("reports/patients/pdf/", PatientsPDFView.as_view(), name="reports-patients-pdf"),
    path("reports/patients/excel/", PatientsExcelView.as_view(), name="reports-patients-excel"),
    path("reports/analyses/pdf/", AnalysesPDFView.as_view(), name="reports-analyses-pdf"),
    path("reports/schedule/<int:doctor_id>/pdf/", SchedulePDFView.as_view(), name="reports-schedule-pdf"),
]