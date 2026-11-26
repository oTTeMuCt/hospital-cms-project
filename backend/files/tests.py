from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from patients.models import Patient


class AttachmentDownloadTests(TestCase):
    def test_upload_returns_protected_download_for_existing_file(self):
        users = get_user_model().objects
        owner = users.create(username="owner", role="patient")
        other = users.create(username="other", role="patient")
        client = APIClient()
        client.force_authenticate(owner)
        content = b"%PDF-1.4 synthetic sample"

        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            upload = client.post("/api/files/", {
                "content_type": ContentType.objects.get_for_model(Patient).pk,
                "object_id": owner.patient_profile.pk,
                "name": "Synthetic attachment",
                "file": SimpleUploadedFile("sample.pdf", content, content_type="application/pdf"),
            })
            self.assertEqual(upload.status_code, 201, upload.data)
            url = urlsplit(upload.data["file"]).path
            self.assertEqual(url, f"/api/files/{upload.data['id']}/download/")
            response = client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), content)
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertEqual(response["Cache-Control"], "private, no-store")

            client.force_authenticate(other)
            self.assertEqual(client.get(url).status_code, 404)
            self.assertEqual(client.get("/api/files/").data["count"], 0)
            client.force_authenticate(None)
            self.assertEqual(client.get(url).status_code, 401)
