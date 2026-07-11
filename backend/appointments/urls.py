from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AppointmentViewSet

router = SimpleRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]
