"""
Tests for the Doctor → Laboratory workflow.
Verifies that Lab Technicians can see newly created (unassigned) analyses.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserRole
from accounts.permissions import IsDoctor, IsDoctorOrLabTech
from patients.models import Patient
from lab.models import AnalysisType, AnalysisOrder, AnalysisStatus
from lab.views import AnalysisOrderViewSet
from lab.serializers import AnalysisOrderSerializer

User = get_user_model()


class LabWorkflowTests(TestCase):
    """Test the Doctor → Laboratory analysis workflow."""

    def setUp(self):
        # Create users
        self.doctor = User.objects.create_user(
            username='test_doctor',
            password='testpass123',
            role=UserRole.DOCTOR,
            first_name='Test',
            last_name='Doctor',
        )
        self.lab_tech = User.objects.create_user(
            username='test_labtech',
            password='testpass123',
            role=UserRole.LAB_TECH,
            first_name='Test',
            last_name='LabTech',
        )
        self.admin = User.objects.create_user(
            username='test_admin',
            password='testpass123',
            role=UserRole.ADMIN,
            first_name='Test',
            last_name='Admin',
            is_staff=True,
            is_superuser=True,
        )
        self.other_lab_tech = User.objects.create_user(
            username='test_labtech2',
            password='testpass123',
            role=UserRole.LAB_TECH,
            first_name='Other',
            last_name='LabTech',
        )
        self.registrar = User.objects.create_user(
            username='test_registrar',
            password='testpass123',
            role=UserRole.REGISTRAR,
            first_name='Test',
            last_name='Registrar',
        )

        # Create patient
        self.patient = Patient.objects.create(
            full_name='Test Patient',
            birth_date='1990-01-01',
            gender='male',
            phone='+998901234567',
        )

        # Create analysis type
        self.analysis_type = AnalysisType.objects.create(
            name='Blood Test',
            code='BLOOD_TEST',
            price=50000,
            currency='UZS',
            turnaround_days=1,
        )

        self.factory = RequestFactory()
        self.api_factory = APIRequestFactory()

    def _get_queryset_for_user(self, user):
        """Helper to get the queryset as seen by a specific user role."""
        request = self.factory.get('/api/analysis-orders/')
        request.user = user
        view = AnalysisOrderViewSet()
        view.request = request
        view.action = 'list'
        return view.get_queryset()

    # ── TEST 1: Doctor creates analysis → Lab Tech can see it ──
    def test_lab_tech_sees_newly_created_analysis(self):
        """Lab Tech must see unassigned analyses (newly created by Doctor)."""
        # Doctor creates an analysis (assigned_to is NULL)
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
            assigned_to=None,  # NOT assigned to anyone
        )

        # Lab Tech queries
        qs = self._get_queryset_for_user(self.lab_tech)
        self.assertIn(order, qs, 
            "Lab Tech MUST see unassigned analyses in the queue")

    # ── TEST 2: Lab Tech sees assigned analyses ──
    def test_lab_tech_sees_own_assigned_analyses(self):
        """Lab Tech must see analyses assigned to them."""
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.ORDERED,
            assigned_to=self.lab_tech,  # assigned to this Lab Tech
        )

        qs = self._get_queryset_for_user(self.lab_tech)
        self.assertIn(order, qs,
            "Lab Tech MUST see analyses assigned to them")

    # ── TEST 3: Lab Tech does NOT see other lab tech's assigned analyses ──
    def test_lab_tech_does_not_see_other_assignments(self):
        """Lab Tech must NOT see analyses assigned to a different Lab Tech."""
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.ORDERED,
            assigned_to=self.other_lab_tech,  # assigned to OTHER lab tech
        )

        qs = self._get_queryset_for_user(self.lab_tech)
        self.assertNotIn(order, qs,
            "Lab Tech MUST NOT see analyses assigned to other Lab Techs")

    # ── TEST 4: Doctor sees own ordered analyses ──
    def test_doctor_sees_own_ordered_analyses(self):
        """Doctor must see analyses they ordered."""
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
        )

        qs = self._get_queryset_for_user(self.doctor)
        self.assertIn(order, qs,
            "Doctor MUST see their own ordered analyses")

    # ── TEST 5: Doctor does NOT see other doctor's analyses ──
    def test_doctor_does_not_see_other_doctors_analyses(self):
        """Doctor must NOT see analyses ordered by other doctors."""
        other_doctor = User.objects.create_user(
            username='other_doctor',
            password='testpass123',
            role=UserRole.DOCTOR,
        )
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=other_doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
        )

        qs = self._get_queryset_for_user(self.doctor)
        self.assertNotIn(order, qs,
            "Doctor MUST NOT see other doctors' ordered analyses")

    # ── TEST 6: Admin sees all analyses ──
    def test_admin_sees_all_analyses(self):
        """Admin must see all analyses regardless of assignment."""
        order1 = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
            assigned_to=None,
        )
        order2 = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.IN_PROGRESS,
            assigned_to=self.lab_tech,
        )

        qs = self._get_queryset_for_user(self.admin)
        self.assertIn(order1, qs, "Admin must see unassigned analyses")
        self.assertIn(order2, qs, "Admin must see assigned analyses")

    # ── TEST 7: Verify queryset SQL is correct ──
    def test_lab_tech_queryset_uses_or_condition(self):
        """Verify the Lab Tech queryset uses OR logic (unassigned OR assigned)."""
        # Create unassigned analysis
        AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
            assigned_to=None,
        )
        # Create assigned analysis
        AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.IN_PROGRESS,
            assigned_to=self.lab_tech,
        )

        qs = self._get_queryset_for_user(self.lab_tech)
        # Should return 2 orders
        self.assertEqual(qs.count(), 2,
            "Lab Tech should see both unassigned AND assigned analyses")

    # ── TEST 8: Status transition model works ──
    def test_status_transitions(self):
        """Verify that status transitions follow the allowed transitions."""
        from lab.models import ALLOWED_TRANSITIONS, AnalysisStatus

        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
        )

        # Can transition from CREATED → ORDERED
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        self.assertIn(AnalysisStatus.ORDERED, allowed)

        # Can transition from ORDERED → IN_PROGRESS
        order.status = AnalysisStatus.ORDERED
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        self.assertIn(AnalysisStatus.IN_PROGRESS, allowed)

        # Can transition from IN_PROGRESS → COMPLETED
        order.status = AnalysisStatus.IN_PROGRESS
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        self.assertIn(AnalysisStatus.COMPLETED, allowed)

        # Can transition from COMPLETED → VERIFIED
        order.status = AnalysisStatus.COMPLETED
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        self.assertIn(AnalysisStatus.VERIFIED, allowed)

    # ═══════════════════════════════════════════════════════════════
    # RBAC TESTS
    # ═══════════════════════════════════════════════════════════════

    # ── TEST 9: Only Doctor/Admin can create analyses ──
    def test_lab_tech_cannot_create_analysis(self):
        """Lab Tech must NOT be able to create analysis orders."""
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status

        factory = APIRequestFactory()
        data = {
            'patient': self.patient.id,
            'analysis_type': self.analysis_type.id,
            'notes': 'Test',
        }
        request = factory.post('/api/analysis-orders/', data, format='json')
        request.user = self.lab_tech
        force_authenticate(request, user=self.lab_tech)

        view = AnalysisOrderViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            "Lab Tech must get 403 when trying to create an analysis order"
        )

    def test_doctor_can_create_analysis(self):
        """Doctor must be able to create analysis orders."""
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status

        factory = APIRequestFactory()
        data = {
            'patient': self.patient.id,
            'analysis_type': self.analysis_type.id,
            'notes': 'Test',
        }
        request = factory.post('/api/analysis-orders/', data, format='json')
        request.user = self.doctor
        force_authenticate(request, user=self.doctor)

        view = AnalysisOrderViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            "Doctor must be able to create an analysis order"
        )

    def test_admin_can_create_analysis(self):
        """Admin must be able to create analysis orders."""
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status

        factory = APIRequestFactory()
        data = {
            'patient': self.patient.id,
            'analysis_type': self.analysis_type.id,
            'notes': 'Test',
        }
        request = factory.post('/api/analysis-orders/', data, format='json')
        request.user = self.admin
        force_authenticate(request, user=self.admin)

        view = AnalysisOrderViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            "Admin must be able to create an analysis order"
        )

    # ── TEST 10: Registrar cannot create analyses ──
    def test_registrar_cannot_create_analysis(self):
        """Registrar must NOT be able to create analysis orders."""
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status

        factory = APIRequestFactory()
        data = {
            'patient': self.patient.id,
            'analysis_type': self.analysis_type.id,
            'notes': 'Test',
        }
        request = factory.post('/api/analysis-orders/', data, format='json')
        request.user = self.registrar
        force_authenticate(request, user=self.registrar)

        view = AnalysisOrderViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN,
            "Registrar must get 403 when trying to create an analysis order"
        )

    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW TESTS
    # ═══════════════════════════════════════════════════════════════

    # ── TEST 11: Lab Tech accepts analysis → auto-assigned ──
    def test_lab_tech_accept_auto_assigns(self):
        """When Lab Tech sets status to in_progress, they are auto-assigned."""
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.ORDERED,
            assigned_to=None,  # unassigned
        )

        from rest_framework.test import APIRequestFactory, force_authenticate

        factory = APIRequestFactory()
        data = {'status': 'in_progress'}
        request = factory.patch(f'/api/analysis-orders/{order.id}/', data, format='json')
        request.user = self.lab_tech
        force_authenticate(request, user=self.lab_tech)

        view = AnalysisOrderViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=order.id)

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.assigned_to, self.lab_tech,
            "Lab Tech must be auto-assigned when they accept an analysis")
        self.assertEqual(order.status, AnalysisStatus.IN_PROGRESS,
            "Status must change to in_progress")

    # ── TEST 12: Lab Tech saves results → auto-completed ──
    def test_lab_tech_saves_results_auto_completes(self):
        """When Lab Tech saves results, status auto-changes to completed."""
        from lab.models import AnalysisField

        # Create a field for the analysis type
        field = AnalysisField.objects.create(
            analysis_type=self.analysis_type,
            field_type='text',
            field_name='Result',
            field_key='result',
            is_required=True,
        )

        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.IN_PROGRESS,
            assigned_to=self.lab_tech,
        )

        from rest_framework.test import APIRequestFactory, force_authenticate

        factory = APIRequestFactory()
        data = {
            'result_values': [{'field_key': 'result', 'value': 'Normal'}],
            'notes': 'All tests normal',
        }
        request = factory.patch(f'/api/analysis-orders/{order.id}/', data, format='json')
        request.user = self.lab_tech
        force_authenticate(request, user=self.lab_tech)

        view = AnalysisOrderViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=order.id)

        self.assertEqual(response.status_code, 200,
            "Lab Tech must be able to save results")
        order.refresh_from_db()
        self.assertEqual(order.status, AnalysisStatus.COMPLETED,
            "Status must auto-change to completed when results are saved")

    # ── TEST 13: Doctor verifies completed analysis ──
    def test_doctor_verifies_completed_analysis(self):
        """Doctor must be able to verify a completed analysis."""
        order = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.COMPLETED,
            assigned_to=self.lab_tech,
        )

        from rest_framework.test import APIRequestFactory, force_authenticate

        factory = APIRequestFactory()
        data = {'status': 'verified'}
        request = factory.patch(f'/api/analysis-orders/{order.id}/', data, format='json')
        request.user = self.doctor
        force_authenticate(request, user=self.doctor)

        view = AnalysisOrderViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=order.id)

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, AnalysisStatus.VERIFIED,
            "Doctor must be able to verify a completed analysis")

    # ── TEST 14: Patient sees only their own analyses ──
    def test_patient_sees_only_own_analyses(self):
        """Patient must only see analyses linked to their user account."""
        # Create a patient user
        patient_user = User.objects.create_user(
            username='test_patient',
            password='testpass123',
            role=UserRole.PATIENT,
        )
        # Check if a Patient was auto-created for this user (e.g., via signal)
        try:
            patient_for_user = Patient.objects.get(user=patient_user)
        except Patient.DoesNotExist:
            # Create one manually
            patient_for_user = Patient.objects.create(
                full_name='Test Patient (linked)',
                birth_date='1990-01-01',
                gender='male',
                phone='+998901234570',
                user=patient_user,
            )

        # Create analysis for this patient
        order1 = AnalysisOrder.objects.create(
            patient=patient_for_user,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
        )
        # Create analysis for a different patient (the one from setUp)
        order2 = AnalysisOrder.objects.create(
            patient=self.patient,
            orderer=self.doctor,
            analysis_type=self.analysis_type,
            status=AnalysisStatus.CREATED,
        )

        qs = self._get_queryset_for_user(patient_user)
        self.assertIn(order1, qs,
            "Patient must see their own analyses")
        self.assertNotIn(order2, qs,
            "Patient must NOT see other patients' analyses")
