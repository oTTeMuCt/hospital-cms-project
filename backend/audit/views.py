from rest_framework import viewsets, filters, permissions

from accounts.permissions import IsAdminRole
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user", "target_content_type").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["action", "user__username", "ip_address"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]
