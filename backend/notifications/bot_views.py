from django.core import signing
from django.db import IntegrityError, transaction
from django.utils.crypto import constant_time_compare
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from patients.models import Patient
from patients.telegram import TELEGRAM_LINK_SALT, TELEGRAM_LINK_TTL, is_bot_request

from .subscription_models import Subscription


class SubscriptionRequest(serializers.Serializer):
    chat_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    code = serializers.CharField(max_length=512)


class BotSubscriptionListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not is_bot_request(request):
            raise PermissionDenied()
        subscriptions = Subscription.objects.filter(is_active=True, is_verified=True).values(
            "chat_id", "patient_id", "patient_id_str"
        )
        return Response(list(subscriptions))

    def post(self, request):
        if not is_bot_request(request):
            raise PermissionDenied()
        serializer = SubscriptionRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_id = serializer.validated_data["chat_id"]
        try:
            code = signing.loads(
                serializer.validated_data["code"], salt=TELEGRAM_LINK_SALT, max_age=TELEGRAM_LINK_TTL,
            )
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"code": "Код недействителен или истёк."}) from exc

        try:
            with transaction.atomic():
                patient = Patient.objects.select_for_update().filter(pk=code["patient"]).first()
                if not patient or not patient.telegram_link_nonce or not constant_time_compare(
                    patient.telegram_link_nonce, code["nonce"],
                ):
                    raise serializers.ValidationError({"code": "Код уже использован или недействителен."})

                active = Subscription.objects.filter(is_active=True, is_verified=True)
                if active.filter(patient=patient).exclude(chat_id=chat_id).exists() or active.filter(
                    chat_id=chat_id,
                ).exclude(patient=patient).exists():
                    return Response(
                        {"detail": "Сначала отмените предыдущую подписку."},
                        status=status.HTTP_409_CONFLICT,
                    )

                subscription, created = Subscription.objects.select_for_update().get_or_create(
                    chat_id=chat_id,
                    defaults={
                        "patient": patient, "patient_id_str": str(patient.pk),
                        "is_active": True, "is_verified": True,
                    },
                )
                if not created:
                    if subscription.is_verified and subscription.is_active and subscription.patient_id != patient.pk:
                        return Response(
                            {"detail": "Сначала отмените предыдущую подписку."},
                            status=status.HTTP_409_CONFLICT,
                        )
                    subscription.patient = patient
                    subscription.patient_id_str = str(patient.pk)
                    subscription.is_active = True
                    subscription.is_verified = True
                    subscription.save()
                patient.telegram_id = str(chat_id)
                patient.telegram_link_nonce = ""
                patient.save(update_fields=["telegram_id", "telegram_link_nonce"])
        except IntegrityError:
            return Response(
                {"detail": "Аккаунт или чат уже привязан."}, status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"status": "ok", "patient_id": patient.pk},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class BotSubscriptionDeleteView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def delete(self, request, chat_id):
        if not is_bot_request(request):
            raise PermissionDenied()

        existing = Subscription.objects.filter(chat_id=chat_id).first()
        if existing is not None:
            if existing.patient_id is not None:
                Patient.objects.select_for_update().filter(pk=existing.patient_id).first()
            deleted, _ = Subscription.objects.filter(
                pk=existing.pk, chat_id=chat_id, patient_id=existing.patient_id, is_verified=existing.is_verified,
            ).delete()
            if deleted and existing.patient_id is not None:
                Patient.objects.filter(pk=existing.patient_id, telegram_id=str(chat_id)).update(telegram_id="")
        return Response({"status": "ok"})
