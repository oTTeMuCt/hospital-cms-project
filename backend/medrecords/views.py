from rest_framework import viewsets

from accounts.permissions import IsDoctor
from .models import MedicalRecord
from .serializers import MedicalRecordSerializer


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.select_related("patient", "created_by").all()
    serializer_class = MedicalRecordSerializer

    def get_permissions(self):
        return [IsDoctor()]