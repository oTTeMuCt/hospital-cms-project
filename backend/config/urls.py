from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "backend"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
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
