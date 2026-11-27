from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "backend"})


def readiness(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        cache.get("hospital-cms-readiness")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


urlpatterns = [
    path("ready/", readiness, name="readiness"),
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    # Prometheus metrics
    path("", include("django_prometheus.urls")),
    # Auth & users
    path("api/", include("accounts.urls")),
    # Domain modules
    path("api/", include("hospitals.urls")),
    path("api/", include("patients.urls")),
    path("api/", include("medrecords.urls")),
    path("api/", include("appointments.urls")),
    path("api/", include("lab.urls")),
    path("api/", include("files.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("stats.urls")),
    path("api/", include("reports.urls")),
    # Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
