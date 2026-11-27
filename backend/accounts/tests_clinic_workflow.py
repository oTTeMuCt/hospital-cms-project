from datetime import time, timedelta
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient


class ClinicWorkflowTests(TestCase):
    def test_working_day_across_six_roles(self):
        users = get_user_model().objects
        admin, chief, registrar, technician, patient = [
            users.create(username=role, role=role)
            for role in ("admin", "chief_doctor", "registrar", "lab_tech", "patient")
        ]
        client = APIClient()

        def call(user, method, path, data=None, expected=200, fmt="json"):
            client.force_authenticate(user)
            response = getattr(client, method)(path, data or {}, format=fmt)
            self.assertEqual(response.status_code, expected, getattr(response, "data", None))
            return response

        staff = call(admin, "post", "/api/staff/create-account/", {
            "username": "clinician", "password": "Fixture-Care-2026!", "role": "doctor",
            "first_name": "Демо", "last_name": "Врач", "position": "Терапевт",
        }, expected=201).data
        doctor = users.get(pk=staff["user"])
        day = timezone.localdate() + timedelta(days=1)
        call(chief, "post", "/api/doctor-work-hours/", {
            "doctor": doctor.pk, "weekday": day.weekday(),
            "starts_at": time(9).isoformat(), "ends_at": time(11).isoformat(),
        }, expected=201)

        type_payload = {"name": "Демонстрационный анализ", "code": "CLINIC-TEST", "fields": [
            {"field_name": "Показатель", "field_key": "marker", "field_type": "numeric", "is_required": True},
        ]}
        call(technician, "post", "/api/analysis-types/", type_payload, expected=403)
        kind = call(chief, "post", "/api/analysis-types/", type_payload, expected=201).data
        self.assertEqual(kind["fields"][0]["field_key"], "marker")

        schedule_query = {"doctor": doctor.pk, "date": day.isoformat()}
        slots = call(patient, "get", "/api/available-slots/", schedule_query).data
        self.assertEqual(len(slots), 4)
        first, second = slots[:2]
        booking = call(patient, "post", "/api/appointments/", {
            "patient": patient.patient_profile.pk, "doctor": doctor.pk,
            "scheduled_at": first["start"], "end_time": first["end"],
        }, expected=201).data
        self.assertEqual(len(call(patient, "get", "/api/available-slots/", schedule_query).data), 3)
        url = f"/api/appointments/{booking['id']}/"
        call(registrar, "patch", url, {"scheduled_at": second["start"], "end_time": second["end"]})
        call(registrar, "patch", url, {"status": "confirmed"})
        call(doctor, "patch", url, {"status": "completed"})

        record_data = {"patient": patient.patient_profile.pk, "appointment": booking["id"],
                       "diagnoses": [{"name": "Синтетический диагноз"}], "medications": "Тестовое назначение"}
        call(registrar, "post", "/api/medical-records/", record_data, expected=403)
        record = call(doctor, "post", "/api/medical-records/", record_data, expected=201).data
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            attachment = call(doctor, "post", "/api/files/", {
                "content_type": record["attachment_content_type"], "object_id": record["id"],
                "name": "Тестовый файл", "file": SimpleUploadedFile("sample.pdf", b"sample", "application/pdf"),
            }, expected=201, fmt="multipart").data
            path = urlsplit(attachment["file"]).path
            response = call(doctor, "get", path)
            self.assertEqual(b"".join(response.streaming_content), b"sample")

        order = call(doctor, "post", "/api/analysis-orders/", {
            "patient": patient.patient_profile.pk, "analysis_type": kind["id"],
        }, expected=201).data
        analysis_url = f"/api/analysis-orders/{order['id']}/"
        call(doctor, "patch", analysis_url, {"status": "ordered"})
        call(technician, "patch", analysis_url, {"status": "in_progress"})
        completed = call(technician, "patch", analysis_url, {"result_values": [{"field_key": "marker", "value": "12"}]}).data
        self.assertEqual(completed["status"], "completed")
        call(doctor, "patch", analysis_url, {"status": "verified"})
        self.assertEqual(call(patient, "get", analysis_url).data["result_values"], [])
        call(doctor, "patch", analysis_url, {"status": "sent"})
        self.assertEqual(call(patient, "get", analysis_url).data["result_values"][0]["value"], "12")
        self.assertEqual(call(chief, "get", "/api/stats/daily/", {"start": day.isoformat()}).data[0]["count"], 1)
