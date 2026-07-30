import logging
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
)

logger = logging.getLogger("lab.serializer")


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
        read_only_fields = ["id", "requested_at"]

    def validate_status(self, value):
        instance = getattr(self, "instance", None)
        if instance is None:
            return value
        old_status = instance.status
        if old_status == value:
            return value
        allowed = ALLOWED_TRANSITIONS.get(old_status, set())
        if value not in allowed:
            raise serializers.ValidationError(
                f"Недопустимый переход: из «{instance.get_status_display()}» "
                f"в «{dict(AnalysisStatus.choices).get(value, value)}»."
            )
        return value

    def to_internal_value(self, data):
        """Intercept to extract result_values before DRF processes nested fields."""
        if "result_values" in data:
            self._raw_result_values = data.pop("result_values")
        ret = super().to_internal_value(data)
        return ret

    def update(self, instance, validated_data):
        """
        Central workflow state machine for AnalysisOrder updates.

        Workflow decisions are based on:
        - Current database status (instance.status)
        - Authenticated user role (from serializer context)
        - Presence of result_values in raw request data

        State Machine:
            created → ordered (Doctor assigns to lab)
            ordered → in_progress (Lab Tech accepts → auto-assigned)
            in_progress → completed (Lab Tech saves results → auto-completed)
            completed → verified (Doctor verifies)
            verified → sent (Doctor sends to patient)
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        user_role = getattr(user, "role", None) if user else None

        # Extract raw result_values (intercepted by to_internal_value)
        raw_result_values = getattr(self, "_raw_result_values", None)
        has_result_values = raw_result_values is not None

        # Extract status from validated_data (if frontend sent it)
        new_status = validated_data.get("status")

        # Log BEFORE processing
        logger.info(
            "=== WORKFLOW UPDATE START ===\n"
            "  order_id=%s\n"
            "  current_status=%s\n"
            "  new_status_from_frontend=%s\n"
            "  assigned_to_id=%s\n"
            "  assigned_to_username=%s\n"
            "  user_role=%s\n"
            "  user_id=%s\n"
            "  has_result_values=%s\n"
            "  validated_data_keys=%s\n"
            "  raw_result_values_count=%s",
            instance.id,
            instance.status,
            new_status,
            instance.assigned_to_id,
            getattr(instance.assigned_to, "username", None) if instance.assigned_to else None,
            user_role,
            getattr(user, "id", None),
            has_result_values,
            list(validated_data.keys()),
            len(raw_result_values) if raw_result_values else 0,
        )

        # ─── WORKFLOW STATE MACHINE ───
        # Decisions are based on current DB state, user role, and data presence
        # NOT on what the frontend sends for status

        if user_role == "lab_tech":
            # ─── LAB TECH WORKFLOW ───

            # 1. ACCEPT: Lab Tech accepting an analysis (status → in_progress)
            if new_status == AnalysisStatus.IN_PROGRESS and instance.assigned_to is None:
                validated_data["assigned_to"] = user
                logger.info("  ACTION: Auto-assign lab tech %s to order %s", user.id, instance.id)

            # 2. COMPLETE: Lab Tech saves results → auto-complete
            if has_result_values and instance.status == AnalysisStatus.IN_PROGRESS:
                validated_data["status"] = AnalysisStatus.COMPLETED
                validated_data["completed_at"] = timezone.now()
                logger.info(
                    "  ACTION: Auto-complete order %s (results saved by lab tech %s)",
                    instance.id, user.id,
                )

        # ─── DOCTOR / ADMIN WORKFLOW ───
        # Doctors and admins can explicitly set status transitions
        # (e.g., created → ordered, completed → verified, verified → sent)

        # ─── APPLY VALIDATED DATA ───
        # Set all fields from validated_data on the instance
        for attr, value in validated_data.items():
            if attr != "result_values":
                setattr(instance, attr, value)

        # ─── SAVE RESULT VALUES ───
        if has_result_values:
            self._save_result_values(instance, raw_result_values)

        # ─── PERSIST TO DATABASE ───
        instance.save()

        # Log AFTER processing
        logger.info(
            "=== WORKFLOW UPDATE END ===\n"
            "  order_id=%s\n"
            "  final_status=%s\n"
            "  final_assigned_to_id=%s\n"
            "  final_assigned_to_username=%s\n"
            "  completed_at=%s\n"
            "  result_values_saved=%s",
            instance.id,
            instance.status,
            instance.assigned_to_id,
            getattr(instance.assigned_to, "username", None) if instance.assigned_to else None,
            instance.completed_at,
            has_result_values,
        )

        return instance

    def _save_result_values(self, instance, result_values_data):
        """Validate and save result values from raw input data."""
        analysis_type = instance.analysis_type
        fields_map = {f.field_key: f for f in analysis_type.fields.all()}

        prev_values = {rv.field.field_key: rv for rv in instance.result_values.all()}

        for item in result_values_data:
            field_key = item.get("field_key", "")
            value = item.get("value", "").strip()

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
                        float(value.replace(",", "."))
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
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure structured result_values are included in the response
        if not data.get("result_values"):
            values = AnalysisResultValueSerializer(
                instance.result_values.select_related("field").all(),
                many=True,
            ).data
            data["result_values"] = values
        return data
