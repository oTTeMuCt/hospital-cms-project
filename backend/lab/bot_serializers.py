from rest_framework import serializers

from .models import AnalysisOrder


class BotAnalysisResultSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор для отображения результатов в Telegram-боте."""

    analysis_name = serializers.CharField(source="analysis_type.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

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
            "notes",
        ]
