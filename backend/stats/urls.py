from django.urls import path

from .views import (
    PatientStatsView,
    AnalysisStatsView,
    DoctorStatsView,
    HospitalStatsView,
    DailyStatsView,
)

urlpatterns = [
    path("stats/patients/", PatientStatsView.as_view(), name="stats-patients"),
    path("stats/analyses/", AnalysisStatsView.as_view(), name="stats-analyses"),
    path("stats/doctors/", DoctorStatsView.as_view(), name="stats-doctors"),
    path("stats/hospitals/", HospitalStatsView.as_view(), name="stats-hospitals"),
    path("stats/daily/", DailyStatsView.as_view(), name="stats-daily"),
]