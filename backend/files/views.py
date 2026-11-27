from pathlib import PurePosixPath

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserRole
from accounts.permissions import IsAdminRole
from appointments.views import AppointmentViewSet
from lab.models import PUBLISHED_STATUSES
from lab.views import AnalysisOrderViewSet
from medrecords.views import MedicalRecordViewSet
from patients.models import Patient
from patients.views import PatientViewSet

from .models import File
from .serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.select_related("content_type", "uploaded_by")
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["content_type", "object_id"]

    def get_permissions(self):
        return [IsAdminRole()] if self.action == "destroy" else [IsAuthenticated()]

    def _accessible_targets(self):
        targets = {}
        for view_class, model in (
            (PatientViewSet, Patient),
            (AppointmentViewSet, AppointmentViewSet.queryset.model),
            (MedicalRecordViewSet, MedicalRecordViewSet.queryset.model),
            (AnalysisOrderViewSet, AnalysisOrderViewSet.queryset.model),
        ):
            view = view_class(request=self.request, action="retrieve")
            if all(permission.has_permission(self.request, view) for permission in view.get_permissions()):
                queryset = view.get_queryset()
                if view_class is AnalysisOrderViewSet and self.request.user.role == UserRole.PATIENT:
                    queryset = queryset.filter(status__in=PUBLISHED_STATUSES)
                targets[model] = queryset

        content_types = ContentType.objects.get_for_models(*targets)
        return {content_types[model].pk: queryset for model, queryset in targets.items()}

    def get_queryset(self):
        files = super().get_queryset()
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return files

        visible = Q(pk__in=[])
        for content_type_id, targets in self._accessible_targets().items():
            visible |= Q(content_type_id=content_type_id, object_id__in=targets.order_by().values("pk"))
        return files.filter(visible)

    def _check_target(self, serializer):
        instance = serializer.instance
        content_type = serializer.validated_data.get("content_type", getattr(instance, "content_type", None))
        object_id = serializer.validated_data.get("object_id", getattr(instance, "object_id", None))
        if self.request.user.role == UserRole.ADMIN:
            return
        targets = self._accessible_targets().get(content_type.pk)
        if content_type.model_class() is MedicalRecordViewSet.queryset.model and self.request.user.role == UserRole.DOCTOR:
            targets = targets.filter(created_by=self.request.user) if targets is not None else None
        if targets is None or not targets.filter(pk=object_id).exists():
            raise PermissionDenied("Нет доступа к объекту вложения.")

    def perform_create(self, serializer):
        self._check_target(serializer)
        serializer.save(uploaded_by=self.request.user)

    def perform_update(self, serializer):
        user = self.request.user
        if user.role != UserRole.ADMIN and serializer.instance.uploaded_by_id != user.pk:
            raise PermissionDenied("Редактировать вложение может его автор или администратор.")
        self._check_target(serializer)
        serializer.save()

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        attachment = self.get_object()
        if not attachment.file:
            raise Http404
        try:
            stream = attachment.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404 from exc
        response = FileResponse(
            stream, as_attachment=True, filename=PurePosixPath(attachment.file.name).name,
            content_type="application/octet-stream",
        )
        response["Cache-Control"] = "private, no-store"
        return response
