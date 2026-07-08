from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole, IsDoctor, IsLabTech
from .models import AnalysisOrder, AnalysisType
from .serializers import AnalysisOrderSerializer, AnalysisTypeSerializer


class AnalysisTypeViewSet(viewsets.ModelViewSet):
    queryset = AnalysisType.objects.all()
    serializer_class = AnalysisTypeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]


class AnalysisOrderViewSet(viewsets.ModelViewSet):
    queryset = AnalysisOrder.objects.select_related(
        "patient", "orderer", "assigned_to", "analysis_type", "verified_by"
    ).all()
    serializer_class = AnalysisOrderSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsLabTech()]
        if self.action == "create":
            return [IsDoctor()]
        if self.action in ("update", "partial_update"):
            return [IsLabTech()]
        if self.action == "destroy":
            return [IsAdminRole()]
        return [IsLabTech()]