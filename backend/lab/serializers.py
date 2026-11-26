from collections.abc import Mapping
from math import isfinite

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from .models import (
    ALLOWED_TRANSITIONS,
    AnalysisField,
    AnalysisOrder,
    AnalysisResultValue,
    AnalysisStatus,
    AnalysisType,
    Interpretations,
    PUBLISHED_STATUSES,
)


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


class AnalysisFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisField
        fields = [
            "id",
            "analysis_type",
            "field_type",
            "field_name",
            "field_key",
            "options",
            "unit",
            "reference_range_min",
            "reference_range_max",
            "reference_range_text",
            "is_required",
            "sort_order",
        ]
        read_only_fields = ["id"]


class AnalysisTypeDetailSerializer(serializers.ModelSerializer):
    """AnalysisType with its predefined fields."""
    fields = AnalysisFieldSerializer(many=True, read_only=True)

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
            "fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AnalysisResultValueSerializer(serializers.ModelSerializer):
    """Serializer for AnalysisResultValue - used for READ (output) only.

    For WRITE operations, the parent AnalysisOrderSerializer handles
    result_values validation and creation directly via update() method,
    bypassing this nested serializer.
    """
    field_name = serializers.CharField(source="field.field_name", read_only=True)
    field_key = serializers.CharField(source="field.field_key", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)
    unit = serializers.CharField(source="field.unit", read_only=True)
    reference_range_min = serializers.FloatField(source="field.reference_range_min", read_only=True)
    reference_range_max = serializers.FloatField(source="field.reference_range_max", read_only=True)
    reference_range_text = serializers.CharField(source="field.reference_range_text", read_only=True)
    options = serializers.JSONField(source="field.options", read_only=True)

    class Meta:
        model = AnalysisResultValue
        fields = [
            "id",
            "field",
            "field_name",
            "field_key",
            "field_type",
            "unit",
            "reference_range_min",
            "reference_range_max",
            "reference_range_text",
            "options",
            "value",
            "interpretation",
        ]
        read_only_fields = ["id"]


class AnalysisOrderSerializer(serializers.ModelSerializer):
    analysis_type_name = serializers.CharField(source="analysis_type.name", read_only=True)
    analysis_type_fields = AnalysisFieldSerializer(source="analysis_type.fields", many=True, read_only=True)
    result_values = AnalysisResultValueSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "patient",
            "orderer",
            "assigned_to",
            "analysis_type",
            "analysis_type_name",
            "analysis_type_fields",
            "status",
            "requested_at",
            "completed_at",
            "result",
            "result_data",
            "result_values",
            "verified_by",
            "notes",
        ]
        read_only_fields = ["id", "requested_at", "orderer", "completed_at", "verified_by"]

    def to_internal_value(self, data):
        if "result_values" in data:
            data = data.copy()
            self._raw_result_values = data["result_values"]
            del data["result_values"]
            if not isinstance(self._raw_result_values, list):
                raise serializers.ValidationError({"result_values": "Ожидается список результатов."})
        return super().to_internal_value(data)

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = get_object_or_404(AnalysisOrder.objects.select_for_update(), pk=instance.pk)
        user = getattr(self.context.get("request"), "user", None)
        role = getattr(user, "role", None)
        old_status = instance.status
        new_status = validated_data.get("status", old_status)
        raw_results = getattr(self, "_raw_result_values", None)

        if new_status != old_status and new_status not in ALLOWED_TRANSITIONS.get(old_status, ()):
            raise serializers.ValidationError({"status": "Недопустимый переход статуса анализа."})
        if role == "lab_tech":
            if instance.assigned_to_id not in (None, user.pk):
                raise serializers.ValidationError({"assigned_to": "Анализ назначен другому лаборанту."})
            if set(validated_data) - {"status", "notes", "result"}:
                raise serializers.ValidationError("Лаборанту доступны только статус, результат и примечания.")
            if new_status != old_status and new_status not in {AnalysisStatus.IN_PROGRESS, AnalysisStatus.COMPLETED}:
                raise serializers.ValidationError({"status": "Этот переход выполняет врач."})
            if new_status == AnalysisStatus.IN_PROGRESS and instance.assigned_to_id is None:
                validated_data["assigned_to"] = user
        if old_status != AnalysisStatus.CREATED and {"patient", "analysis_type"}.intersection(validated_data):
            raise serializers.ValidationError("Пациента и вид анализа можно изменить только до назначения.")
        if raw_results is not None and old_status != AnalysisStatus.IN_PROGRESS:
            raise serializers.ValidationError({"result_values": "Ввод результатов доступен для анализа в работе."})

        for field, value in validated_data.items():
            setattr(instance, field, value)
        if raw_results is not None:
            self._save_result_values(instance, raw_results)

        completed = new_status in (AnalysisStatus.COMPLETED, AnalysisStatus.VERIFIED, AnalysisStatus.SENT)
        auto_complete = role == "lab_tech" and old_status == AnalysisStatus.IN_PROGRESS and (
            bool(raw_results) or bool(validated_data.get("result"))
        )
        if completed or auto_complete:
            filled = instance.result_values.exclude(value="").values("field_id")
            missing = instance.analysis_type.fields.filter(is_required=True).exclude(pk__in=filled)
            if completed and missing.exists():
                raise serializers.ValidationError({"result_values": "Заполните все обязательные поля анализа."})
            if auto_complete and not missing.exists():
                instance.status = AnalysisStatus.COMPLETED
            if old_status == AnalysisStatus.IN_PROGRESS and instance.status == AnalysisStatus.COMPLETED:
                instance.completed_at = timezone.now()
        if old_status != AnalysisStatus.VERIFIED and instance.status == AnalysisStatus.VERIFIED:
            instance.verified_by = user
        instance.save()
        return instance

    def _save_result_values(self, instance, result_values_data):
        """Validate and save result values from raw input data."""
        analysis_type = instance.analysis_type
        fields_map = {f.field_key: f for f in analysis_type.fields.all()}

        prev_values = {rv.field.field_key: rv for rv in instance.result_values.all()}

        seen = set()
        for item in result_values_data:
            if not isinstance(item, Mapping) or not isinstance(item.get("field_key"), str) or not isinstance(item.get("value"), str):
                raise serializers.ValidationError({"result_values": "Ожидаются ключ поля и строковое значение."})
            field_key = item["field_key"]
            value = item["value"].strip()
            if field_key in seen:
                raise serializers.ValidationError({"result_values": "Поле результата указано дважды."})
            seen.add(field_key)

            if not field_key:
                raise serializers.ValidationError({
                    "result_values": "Каждое поле результата должно содержать 'field_key'."
                })

            field_obj = fields_map.get(field_key)
            if not field_obj:
                raise serializers.ValidationError(
                    f"Поле '{field_key}' не найдено для анализа '{analysis_type.name}'."
                )

            # Validate required fields
            if field_obj.is_required and not value:
                raise serializers.ValidationError(
                    f"Поле '{field_obj.field_name}' обязательно для заполнения."
                )

            if value:
                # Validate choice fields
                if field_obj.field_type == "choice":
                    valid_options = field_obj.options or []
                    if value not in valid_options:
                        raise serializers.ValidationError(
                            f"Недопустимое значение для '{field_obj.field_name}': '{value}'. "
                            f"Допустимые: {', '.join(valid_options)}"
                        )

                # Validate numeric fields
                if field_obj.field_type == "numeric":
                    try:
                        if not isfinite(float(value.replace(",", "."))):
                            raise ValueError
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(
                            f"Поле '{field_obj.field_name}' должно содержать числовое значение."
                        )

            # Compute interpretation for numeric fields
            interpretation = item.get("interpretation", "")
            if field_obj.field_type == "numeric" and value:
                try:
                    numeric_value = float(value.replace(",", "."))
                    if (
                        field_obj.reference_range_min is not None
                        and field_obj.reference_range_max is not None
                    ):
                        if numeric_value < field_obj.reference_range_min:
                            interpretation = Interpretations.LOW
                        elif numeric_value > field_obj.reference_range_max:
                            interpretation = Interpretations.HIGH
                        else:
                            interpretation = Interpretations.NORMAL
                except (ValueError, TypeError):
                    pass

            # Update or create result value
            if field_key in prev_values:
                rv = prev_values[field_key]
                rv.value = value
                rv.interpretation = interpretation
                rv.save()
            else:
                AnalysisResultValue.objects.create(
                    analysis_order=instance,
                    field=field_obj,
                    value=value,
                    interpretation=interpretation,
                )

        # Also set the legacy `result` field from structured values
        result_texts = []
        for rv in instance.result_values.select_related("field").order_by("field__sort_order"):
            display = f"{rv.field.field_name}: {rv.value}"
            if rv.field.unit:
                display += f" {rv.field.unit}"
            if rv.interpretation:
                interp_label = dict(Interpretations.choices).get(rv.interpretation, "")
                display += f" ({interp_label})"
            if rv.field.reference_range_min is not None and rv.field.reference_range_max is not None:
                display += f" [норма: {rv.field.reference_range_min}-{rv.field.reference_range_max}]"
            result_texts.append(display)
        if result_texts:
            instance.result = "\n".join(result_texts)

    def create(self, validated_data):
        validated_data.pop("result_values", None)
        validated_data["status"] = AnalysisStatus.CREATED
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = getattr(self.context.get("request"), "user", None)
        if getattr(user, "role", None) == "patient":
            data["notes"] = ""
            if instance.status not in PUBLISHED_STATUSES:
                data.update(result="", result_data=None, result_values=[])
        return data
