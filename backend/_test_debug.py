"""
Debug script to trace the 403 issue for POST /api/analysis-orders/
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('DJANGO_DEBUG', 'true')
os.environ.setdefault('USE_SQLITE', 'true')
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-key')

import django
django.setup()

from accounts.permissions import IsDoctor, IsAuthenticatedAndRole, IsDoctorOrLabTech, IsAdminRole, IsLabTech
from accounts.models import UserRole

# Create a mock request object with a doctor user
class MockUser:
    is_authenticated = True
    role = 'doctor'
    id = 1
    
class MockRequest:
    user = MockUser()
    method = 'POST'
    
class MockView:
    action = 'create'
    allowed_roles = {'admin', 'doctor', 'chief_doctor', 'lab_tech', 'registrar', 'patient'}

print("=" * 60)
print("DEBUG: Tracing permission check for Doctor creating AnalysisOrder")
print("=" * 60)
print(f"UserRole.DOCTOR = {repr(UserRole.DOCTOR)}")
print(f"UserRole.CHIEF_DOCTOR = {repr(UserRole.CHIEF_DOCTOR)}")
print(f"UserRole.ADMIN = {repr(UserRole.ADMIN)}")
print(f"Doctor role value: {repr('doctor')}")
print()

# Test IsDoctor
perm = IsDoctor()
result = perm.has_permission(MockRequest(), MockView())
print(f"IsDoctor().has_permission(doctor) = {result}")

# Test IsAuthenticatedAndRole
perm2 = IsAuthenticatedAndRole()
result2 = perm2.has_permission(MockRequest(), MockView())
print(f"IsAuthenticatedAndRole().has_permission(doctor) = {result2}")

# Test IsDoctorOrLabTech
perm3 = IsDoctorOrLabTech()
result3 = perm3.has_permission(MockRequest(), MockView())
print(f"IsDoctorOrLabTech().has_permission(doctor) = {result3}")

# Test with patient role
class PatientUser:
    is_authenticated = True
    role = 'patient'
    
class PatientRequest:
    user = PatientUser()
    method = 'POST'

print()
print(f"IsDoctor().has_permission(patient) = {IsDoctor().has_permission(PatientRequest(), MockView())}")

# Test with anonymous user
class AnonUser:
    is_authenticated = False
    role = None
    
class AnonRequest:
    user = AnonUser()
    method = 'POST'

print(f"IsDoctor().has_permission(anonymous) = {IsDoctor().has_permission(AnonRequest(), MockView())}")

# Check what the get_permissions method returns for create action
print()
print("=" * 60)
print("Simulating get_permissions() for create action:")
print(f"  action = 'create'")
print(f"  Would return: [IsDoctor()]")
print(f"  IsDoctor result: {IsDoctor().has_permission(MockRequest(), MockView())}")
print("=" * 60)

# Check if there's a fallback issue
print()
print("Checking if action could be wrong:")
print(f"  For POST /api/analysis-orders/ the action should be 'create'")
print(f"  If action is not matched, fallback is [IsLabTech()]")
print(f"  IsLabTech().has_permission(doctor) = {IsLabTech().has_permission(MockRequest(), MockView())}")