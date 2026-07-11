from rest_framework import viewsets  # noqa: I001
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole
from .models import File
from .serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related("content_type", "uploaded_by").all()
    serializer_class = FileSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "create"):
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)