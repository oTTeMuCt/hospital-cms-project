import logging

from django.db import transaction
from kombu.exceptions import OperationalError
from rest_framework import viewsets

from accounts.models import UserRole
from accounts.permissions import IsAdminRole, IsAuthenticatedAndRole, IsRegistrar
from .models import Notification, NotificationStatus
from .serializers import NotificationSerializer
from .tasks import send_notification


logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("recipient_content_type", "created_by").all()
    serializer_class = NotificationSerializer
    allowed_roles = {
        UserRole.ADMIN, UserRole.CHIEF_DOCTOR, UserRole.DOCTOR,
        UserRole.LAB_TECH, UserRole.REGISTRAR,
    }

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsRegistrar()]
        if self.action == "create":
            return [IsAuthenticatedAndRole()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminRole()]
        return [IsRegistrar()]

    def perform_create(self, serializer):
        notification = serializer.save(created_by=self.request.user)

        def enqueue():
            try:
                send_notification.delay(notification.pk)
            except OperationalError:
                logger.error("Could not enqueue notification %s", notification.pk)
                error_message = "Notification queue is unavailable."
                updated = Notification.objects.filter(
                    pk=notification.pk, status=NotificationStatus.PENDING,
                ).update(status=NotificationStatus.FAILED, error_message=error_message)
                if updated:
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = error_message

        transaction.on_commit(enqueue)
