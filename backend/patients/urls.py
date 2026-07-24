from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import BotLinkTelegramView, PatientViewSet

router = SimpleRouter()
router.register(r"patients", PatientViewSet, basename="patient")

urlpatterns = [
    path("", include(router.urls)),
    path("bot/link-telegram/", BotLinkTelegramView.as_view(), name="bot-link-telegram"),
]
