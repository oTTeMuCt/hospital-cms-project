from rest_framework import serializers

from .models import AnalysisOrder, AnalysisType


class AnalysisTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisType
        fields = [
            "id",
            "name",
            "code",
            "price",
            "currency",
            "turnaround_days",
            "normal_range",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AnalysisOrderSerializer(serializers.ModelSerializer):
    analysis_type_name = serializers.CharField(source="analysis_type.name", read_only=True)

    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "patient",
            "orderer",
            "assigned_to",
            "analysis_type",
            "analysis_type_name",
            "status",
            "requested_at",
            "completed_at",
            "result",
            "result_data",
            "verified_by",
            "notes",
        ]
        read_only_fields = ["id", "requested_at"]