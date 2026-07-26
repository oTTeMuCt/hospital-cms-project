from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .bot_views import BotSubscriptionDeleteView, BotSubscriptionListCreateView
from .views import NotificationViewSet

router = SimpleRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    # Bot subscription endpoints (database-backed, replaces JSON file)
    path("bot/subscriptions/", BotSubscriptionListCreateView.as_view(), name="bot-subscriptions"),
    path("bot/subscriptions/<int:chat_id>/", BotSubscriptionDeleteView.as_view(), name="bot-subscription-delete"),
]
