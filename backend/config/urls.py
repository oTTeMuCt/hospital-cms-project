from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "backend"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path("api/", include("accounts.urls")),
]
