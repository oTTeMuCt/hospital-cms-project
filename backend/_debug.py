"""Debug: check what happens when saving result values."""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["USE_SQLITE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from lab.models import AnalysisOrder, AnalysisField, AnalysisResultValue
from lab.serializers import AnalysisOrderSerializer

o = AnalysisOrder.objects.get(pk=5)
print(f"Order #{o.id}: {o.analysis_type.name} (type_id={o.analysis_type_id})")
print(f"Status: {o.status}")

fields = list(o.analysis_type.fields.all())
print(f"Fields ({len(fields)}):")
for f in fields:
    print(f"  - {f.field_key}: {f.field_name} ({f.field_type})")

# Simulate what the frontend sends
test_payload = {
    "result_values": [
        {"field_key": "blood_group", "value": "A (II) Rh+"},
    ],
    "status": "completed",
}
print(f"\nTest payload: {test_payload}")

# Try to validate and save
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from django.test.client import RequestFactory

# Create a mock request
rf = RequestFactory()
request = rf.patch("/api/analysis-orders/5/")

# Create serializer with instance
serializer = AnalysisOrderSerializer(
    instance=o,
    data=test_payload,
    partial=True,
    context={"request": request},
)

print(f"\nIs valid: {serializer.is_valid()}")
if not serializer.is_valid():
    print(f"Errors: {serializer.errors}")
else:
    serializer.save()
    print("Saved successfully!")
    o.refresh_from_db()
    print(f"New status: {o.status}")
    print(f"Result values: {list(o.result_values.all().values('field__field_key', 'value'))}")