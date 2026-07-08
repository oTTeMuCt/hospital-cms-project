from rest_framework import viewsets, permissions

from accounts.permissions import IsAdminRole, IsRegistrar
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related("recipient_content_type", "created_by").all()
    serializer_class = NotificationSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsRegistrar()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminRole()]
        return [IsRegistrar()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
