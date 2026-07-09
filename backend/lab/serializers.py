from rest_framework import serializers

from .models import ALLOWED_TRANSITIONS, AnalysisOrder, AnalysisType


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

    def validate_status(self, value):
        instance = getattr(self, "instance", None)
        if instance is None:
            # создание — допустим любой статус
            return value
        old_status = instance.status
        if old_status == value:
            return value
        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if value not in allowed:
            raise serializers.ValidationError(
                f"Недопустимый переход: из «{instance.get_status_display()}» "
                f"в «{dict(self.Meta.model.Status.choices).get(value, value)}»."
            )
        return value
