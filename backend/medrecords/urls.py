from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import MedicalRecordViewSet

router = SimpleRouter()
router.register(r"medical-records", MedicalRecordViewSet, basename="medicalrecord")

urlpatterns = [
    path("", include(router.urls)),
]
