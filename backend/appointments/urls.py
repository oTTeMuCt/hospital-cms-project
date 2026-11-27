from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AppointmentViewSet, AvailableSlotsView, BookingDoctorsView, DoctorWorkHoursViewSet

router = SimpleRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")

router.register(r"doctor-work-hours", DoctorWorkHoursViewSet, basename="doctor-work-hours")

urlpatterns = [
    path("booking-doctors/", BookingDoctorsView.as_view()),
    path("available-slots/", AvailableSlotsView.as_view()),
    path("", include(router.urls)),
]
