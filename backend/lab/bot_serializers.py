from rest_framework import serializers

from .models import AnalysisOrder, Interpretations


class BotResultValueSerializer(serializers.Serializer):
    """Simplified result value for Telegram bot display."""
    field_name = serializers.CharField()
    value = serializers.CharField()
    unit = serializers.CharField()
    interpretation = serializers.CharField()
    reference_range_text = serializers.CharField()


class BotAnalysisResultSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор для отображения результатов в Telegram-боте."""

    analysis_name = serializers.CharField(source="analysis_type.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result_fields = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "analysis_name",
            "status",
            "status_display",
            "requested_at",
            "completed_at",
            "result",
            "result_fields",
            "notes",
        ]

    def get_result_fields(self, obj):
        values = obj.result_values.select_related("field").all().order_by("field__sort_order")
        data = []
        for rv in values:
            interp_label = ""
            if rv.interpretation:
                interp_label = dict(Interpretations.choices).get(rv.interpretation, "")
            ref_text = rv.field.reference_range_text or ""
            if not ref_text and rv.field.reference_range_min is not None and rv.field.reference_range_max is not None:
                ref_text = f"{rv.field.reference_range_min}–{rv.field.reference_range_max}"
            data.append({
                "field_name": rv.field.field_name,
                "value": rv.value,
                "unit": rv.field.unit or "",
                "interpretation": interp_label,
                "reference_range_text": ref_text,
            })
        return data