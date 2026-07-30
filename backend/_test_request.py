"""
Test script to reproduce the 403 issue.
Creates test data and makes a POST request to /api/analysis-orders/
"""
import os
import sys
import json
import urllib.request
import urllib.error

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_DEBUG', 'true')
os.environ.setdefault('USE_SQLITE', 'true')
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-key')

import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserRole
from patients.models import Patient
from lab.models import AnalysisType, AnalysisOrder
from lab.serializers import AnalysisOrderSerializer

User = get_user_model()

# Create a doctor user if not exists
doctor, created = User.objects.get_or_create(
    username='testdoctor',
    defaults={
        'first_name': 'Test',
        'last_name': 'Doctor',
        'role': UserRole.DOCTOR,
        'is_staff': True,
    }
)
if created:
    doctor.set_password('testpass123')
    doctor.save()
    print(f"Created doctor user: {doctor.username} (id={doctor.id})")
else:
    print(f"Using existing doctor: {doctor.username} (id={doctor.id}, role={doctor.role})")

# Create a patient if not exists
patient, created = Patient.objects.get_or_create(
    full_name='Test Patient',
    defaults={
        'birth_date': '1990-01-01',
        'gender': 'male',
        'phone': '+998901234567',
    }
)
print(f"Patient: {patient.full_name} (id={patient.id})")

# Create an analysis type if not exists
analysis_type, created = AnalysisType.objects.get_or_create(
    code='BLOOD_TEST',
    defaults={
        'name': 'General Blood Test',
        'price': 50000,
        'currency': 'UZS',
        'turnaround_days': 1,
    }
)
print(f"AnalysisType: {analysis_type.name} (id={analysis_type.id})")

# Get a JWT token
print("\n--- Getting JWT token ---")
token_url = 'http://localhost:8000/api/auth/token/'
token_data = json.dumps({
    'username': 'testdoctor',
    'password': 'testpass123'
}).encode('utf-8')

token_req = urllib.request.Request(
    token_url,
    data=token_data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    token_resp = urllib.request.urlopen(token_req)
    token_body = json.loads(token_resp.read().decode('utf-8'))
    access_token = token_body['access']
    print(f"Got token: {access_token[:50]}...")
except urllib.error.HTTPError as e:
    print(f"Token error: {e.code} - {e.read().decode('utf-8')}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# Make a POST request to /api/analysis-orders/
print("\n--- Testing POST /api/analysis-orders/ ---")
order_url = 'http://localhost:8000/api/analysis-orders/'
order_data = json.dumps({
    'patient': patient.id,
    'analysis_type': analysis_type.id,
    'notes': 'Test analysis order'
}).encode('utf-8')

order_req = urllib.request.Request(
    order_url,
    data=order_data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    },
    method='POST'
)

try:
    order_resp = urllib.request.urlopen(order_req)
    order_body = json.loads(order_resp.read().decode('utf-8'))
    print(f"SUCCESS! Status: {order_resp.status}")
    print(f"Response: {json.dumps(order_body, indent=2, ensure_ascii=False)}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"ERROR! Status: {e.code}")
    print(f"Response: {error_body}")
    print(f"\nHeaders: {dict(e.headers)}")
except Exception as e:
    print(f"Error: {e}")

# Check the doctor's role
print("\n--- Doctor's role check ---")
doctor = User.objects.get(username='testdoctor')
print(f"Doctor role: {repr(doctor.role)}")
print(f"Doctor role == 'doctor': {doctor.role == 'doctor'}")
print(f"Doctor role == UserRole.DOCTOR: {doctor.role == UserRole.DOCTOR}")
print(f"Doctor role in ['doctor', 'chief_doctor', 'admin']: {doctor.role in ['doctor', 'chief_doctor', 'admin']}")

# Check if there are any analysis orders
print("\n--- Analysis Orders ---")
orders = AnalysisOrder.objects.all()
print(f"Total orders: {orders.count()}")
for o in orders:
    print(f"  Order {o.id}: patient={o.patient.id}, type={o.analysis_type.name}, status={o.status}, orderer={o.orderer}")