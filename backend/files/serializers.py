from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import File

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/dicom",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class FileSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "content_type",
            "object_id",
            "content_type_name",
            "name",
            "file",
            "mime_type",
            "size",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = ["id", "size", "uploaded_by", "created_at"]

    def validate_file(self, value):
        if hasattr(value, "content_type"):
            mime = value.content_type
        else:
            mime = None
        if mime and mime not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f"Недопустимый тип файла: {mime}. "
                f"Разрешённые: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )
        return value

    def create(self, validated_data):
        file_obj = validated_data.get("file")
        if file_obj and hasattr(file_obj, "content_type"):
            validated_data["mime_type"] = file_obj.content_type
        if file_obj:
            validated_data["size"] = file_obj.size
        return super().create(validated_data)

    def update(self, instance, validated_data):
        file_obj = validated_data.get("file")
        if file_obj and hasattr(file_obj, "content_type"):
            validated_data["mime_type"] = file_obj.content_type
        if file_obj:
            validated_data["size"] = file_obj.size
        return super().update(instance, validated_data)