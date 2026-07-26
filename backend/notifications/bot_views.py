"""
API endpoints for the Telegram Bot to manage subscriptions via database.
Replaces JSON file-based subscription storage.
"""
import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .subscription_models import Subscription

logger = logging.getLogger("notifications.bot_views")


class BotSubscriptionListCreateView(APIView):
    """
    GET /api/bot/subscriptions/ — list all subscriptions (for bot cache warmup)
    POST /api/bot/subscriptions/ — create a subscription

    Protected by X-Bot-Key header.
    """
    permission_classes = [AllowAny]

    def _verify_bot_key(self, request) -> bool:
        import os
        expected_key = os.getenv("BOT_API_KEY")
        if not expected_key:
            return False
        bot_key = request.headers.get("X-Bot-Key", "")
        return bot_key == expected_key

    def get(self, request):
        if not self._verify_bot_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        subscriptions = Subscription.objects.filter(is_active=True).values(
            "chat_id", "patient_id", "patient_id_str"
        )
        return Response(list(subscriptions), status=status.HTTP_200_OK)

    def post(self, request):
        if not self._verify_bot_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        chat_id = request.data.get("chat_id")
        patient_id_str = request.data.get("patient_id_str", "")

        if not chat_id or not patient_id_str:
            return Response(
                {"error": "chat_id and patient_id_str are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sub, created = Subscription.objects.update_or_create(
                chat_id=int(chat_id),
                defaults={
                    "patient_id_str": patient_id_str,
                    "is_active": True,
                },
            )
            logger.info(
                "Bot subscription %s: chat_id=%s, patient_id_str=%s",
                "created" if created else "updated",
                chat_id,
                patient_id_str,
            )
            return Response(
                {
                    "status": "ok",
                    "chat_id": sub.chat_id,
                    "patient_id_str": sub.patient_id_str,
                    "created": created,
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except (IntegrityError, ValueError) as exc:
            logger.error("Failed to create subscription: %s", exc)
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BotSubscriptionDeleteView(APIView):
    """
    DELETE /api/bot/subscriptions/<chat_id>/
    Delete a subscription by chat_id.
    """
    permission_classes = [AllowAny]

    def _verify_bot_key(self, request) -> bool:
        import os
        expected_key = os.getenv("BOT_API_KEY")
        if not expected_key:
            return False
        bot_key = request.headers.get("X-Bot-Key", "")
        return bot_key == expected_key

    def delete(self, request, chat_id):
        if not self._verify_bot_key(request):
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            sub = Subscription.objects.get(chat_id=chat_id)
            sub.delete()
            logger.info("Bot subscription deleted: chat_id=%s", chat_id)
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response(
                {"error": "Subscription not found"},
                status=status.HTTP_404_NOT_FOUND,
            )