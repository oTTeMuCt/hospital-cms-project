from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import DepartmentViewSet, HospitalViewSet, StaffViewSet

router = SimpleRouter()
router.register(r"hospitals", HospitalViewSet, basename="hospital")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"staff", StaffViewSet, basename="staff")

urlpatterns = [
    path("", include(router.urls)),
]
