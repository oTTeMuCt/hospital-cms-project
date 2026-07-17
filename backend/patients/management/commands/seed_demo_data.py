"""
Management command to populate the system with demo data:
- 5 Departments
- 5 Doctors (with User accounts) assigned to departments
- 5 Patients (with User accounts and Patient profiles)
- 5 Laboratory test types

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --force   # Drop existing demo data first
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import UserRole
from hospitals.models import Department, DepartmentType, Hospital, Staff
from lab.models import AnalysisType
from patients.models import Gender, Patient

User = get_user_model()


DEPARTMENTS = [
    {"name": "Кардиология", "dept_type": DepartmentType.CARDIOLOGY, "description": "Диагностика и лечение заболеваний сердечно-сосудистой системы"},
    {"name": "Неврология", "dept_type": DepartmentType.NEUROLOGY, "description": "Диагностика и лечение заболеваний нервной системы"},
    {"name": "Хирургия", "dept_type": DepartmentType.SURGERY, "description": "Хирургическое лечение различных заболеваний"},
    {"name": "Педиатрия", "dept_type": DepartmentType.THERAPY, "description": "Медицинская помощь детям с рождения до 18 лет"},
    {"name": "Лаборатория", "dept_type": DepartmentType.LABORATORY, "description": "Клинико-диагностические лабораторные исследования"},
]

DOCTORS_DATA = [
    {
        "username": "doctor_karimov",
        "first_name": "Бахтияр",
        "last_name": "Каримов",
        "middle_name": "Алишерович",
        "position": "Врач-кардиолог",
        "department_idx": 0,  # Кардиология
    },
    {
        "username": "doctor_rasulova",
        "first_name": "Дильноза",
        "last_name": "Расулова",
        "middle_name": "Тимуровна",
        "position": "Врач-невролог",
        "department_idx": 1,  # Неврология
    },
    {
        "username": "doctor_yusupov",
        "first_name": "Рустам",
        "last_name": "Юсупов",
        "middle_name": "Шерзодович",
        "position": "Врач-хирург",
        "department_idx": 2,  # Хирургия
    },
    {
        "username": "doctor_ahmedova",
        "first_name": "Лола",
        "last_name": "Ахмедова",
        "middle_name": "Шавкатовна",
        "position": "Врач-педиатр",
        "department_idx": 3,  # Педиатрия
    },
    {
        "username": "doctor_nazarov",
        "first_name": "Акмаль",
        "last_name": "Назаров",
        "middle_name": "Бахтиёрович",
        "position": "Врач-лаборант",
        "department_idx": 4,  # Лаборатория
    },
]

PATIENTS_DATA = [
    {
        "username": "patient_aliev",
        "first_name": "Алишер",
        "last_name": "Алиев",
        "middle_name": "Нурмухаммадович",
        "patient": {
            "full_name": "Алиев Алишер Нурмухаммадович",
            "birth_date": "1985-06-15",
            "gender": Gender.MALE,
            "passport": "AB1234567",
            "phone": "+998901234567",
            "email": "alisher.aliev@example.com",
            "address": "г. Ташкент, ул. Амира Темура, д. 15",
            "emergency_contact": "+998901112233 (супруга)",
        },
    },
    {
        "username": "patient_ibragimova",
        "first_name": "Малика",
        "last_name": "Ибрагимова",
        "middle_name": "Рашидовна",
        "patient": {
            "full_name": "Ибрагимова Малика Рашидовна",
            "birth_date": "1990-11-22",
            "gender": Gender.FEMALE,
            "passport": "BB7654321",
            "phone": "+998935556677",
            "email": "malika.ibragimova@example.com",
            "address": "г. Ташкент, ул. Шота Руставели, д. 42",
            "emergency_contact": "+998934445566 (брат)",
        },
    },
    {
        "username": "patient_sadirov",
        "first_name": "Шерзод",
        "last_name": "Садиров",
        "middle_name": "Улугбекович",
        "patient": {
            "full_name": "Садиров Шерзод Улугбекович",
            "birth_date": "1978-03-08",
            "gender": Gender.MALE,
            "passport": "AA9988776",
            "phone": "+998977778899",
            "email": "sherzod.sadirov@example.com",
            "address": "г. Ташкент, Чиланзарский р-н, кв. 15-78",
            "emergency_contact": "+998903332211 (сын)",
        },
    },
    {
        "username": "patient_rahimova",
        "first_name": "Зарина",
        "last_name": "Рахимова",
        "middle_name": "Азаматова",
        "patient": {
            "full_name": "Рахимова Зарина Азаматова",
            "birth_date": "2002-09-30",
            "gender": Gender.FEMALE,
            "passport": "AC5544332",
            "phone": "+998909998877",
            "email": "zarina.rahimova@example.com",
            "address": "г. Ташкент, ул. Навои, д. 7",
            "emergency_contact": "+998901110022 (отец)",
        },
    },
    {
        "username": "patient_usmanov",
        "first_name": "Даврон",
        "last_name": "Усманов",
        "middle_name": "Батирович",
        "patient": {
            "full_name": "Усманов Даврон Батирович",
            "birth_date": "1965-12-05",
            "gender": Gender.MALE,
            "passport": "AD1122334",
            "phone": "+998908887766",
            "email": "davron.usmanov@example.com",
            "address": "г. Ташкент, Юнусабадский р-н, ул. Богишамол, д. 21",
            "emergency_contact": "+998902223344 (супруга)",
        },
    },
]

LAB_TESTS = [
    {
        "name": "Общий анализ крови (ОАК)",
        "code": "CBC",
        "price": 35000,
        "normal_range": "Эритроциты: 3.7-4.7, Гемоглобин: 120-150",
        "description": "Клинический анализ крови, включая эритроциты, гемоглобин, лейкоциты, тромбоциты",
    },
    {
        "name": "Биохимический анализ крови",
        "code": "BIO",
        "price": 65000,
        "normal_range": "Глюкоза: 3.3-5.5, Холестерин: 3.5-5.2",
        "description": "Определение уровня глюкозы, холестерина, билирубина, АЛТ, АСТ, креатинина и мочевины",
    },
    {
        "name": "Общий анализ мочи (ОАМ)",
        "code": "URINE",
        "price": 20000,
        "normal_range": "pH: 5.0-7.0, Прозрачность: полная",
        "description": "Физико-химическое и микроскопическое исследование мочи",
    },
    {
        "name": "Электрокардиография (ЭКГ)",
        "code": "ECG",
        "price": 50000,
        "normal_range": "Ритм: синусовый, ЧСС: 60-90",
        "description": "Регистрация электрической активности сердца для выявления нарушений ритма и ишемии",
    },
    {
        "name": "Коагулограмма (гемостаз)",
        "code": "COAG",
        "price": 45000,
        "normal_range": "МНО: 0.8-1.2, АЧТВ: 25-35 сек",
        "description": "Исследование свертывающей системы крови: протромбиновое время, МНО, АЧТВ, фибриноген",
    },
]


class Command(BaseCommand):
    help = "Seed demo data: departments, doctors, patients, and lab tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Drop existing demo users/patients/departments before recreating",
        )

    def handle(self, *args, **options):
        force = options["force"]

        if force:
            self._cleanup()
            self.stdout.write(self.style.WARNING("Removed existing demo data."))

        self._ensure_hospital()
        departments = self._create_departments()
        doctors = self._create_doctors(departments)
        patients = self._create_patients()
        lab_tests = self._create_lab_tests()

        self.stdout.write(self.style.SUCCESS("\n=== Demo Data Summary ==="))
        self.stdout.write(f"  Departments: {len(departments)}")
        self.stdout.write(f"  Doctors:     {len(doctors)}")
        self.stdout.write(f"  Patients:    {len(patients)}")
        self.stdout.write(f"  Lab Tests:   {len(lab_tests)}")
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))

    def _cleanup(self):
        """Remove existing demo data (identified by our known usernames/names)."""
        demo_usernames = (
            [d["username"] for d in DOCTORS_DATA]
            + [p["username"] for p in PATIENTS_DATA]
        )
        User.objects.filter(username__in=demo_usernames).delete()

        Patient.objects.filter(passport__in=[p["patient"]["passport"] for p in PATIENTS_DATA]).delete()

        dept_names = [d["name"] for d in DEPARTMENTS]
        Department.objects.filter(name__in=dept_names).delete()

        test_codes = [t["code"] for t in LAB_TESTS]
        AnalysisType.objects.filter(code__in=test_codes).delete()

    def _ensure_hospital(self):
        """Ensure at least one Hospital exists."""
        if not Hospital.objects.exists():
            hospital = Hospital.objects.create(
                name="Городская клиническая больница №1",
                short_name="ГКБ №1",
                address="г. Ташкент, ул. Шахрисабз, д. 10",
                phone="+998712345678",
                working_hours="Круглосуточно",
                timezone="Asia/Tashkent",
                country_code="UZ",
            )
            self.stdout.write(f"  Created hospital: {hospital.name}")
        else:
            self.stdout.write("  Hospital already exists, skipping.")

    @transaction.atomic
    def _create_departments(self):
        hospital = Hospital.objects.first()
        created = []
        for dept_data in DEPARTMENTS:
            dept, was_created = Department.objects.get_or_create(
                hospital=hospital,
                name=dept_data["name"],
                defaults={
                    "department_type": dept_data["dept_type"],
                    "description": dept_data["description"],
                },
            )
            if was_created:
                self.stdout.write(f"  Created department: {dept.name}")
            created.append(dept)
        return created

    @transaction.atomic
    def _create_doctors(self, departments):
        doctors = []
        for doc_data in DOCTORS_DATA:
            user, was_created = User.objects.get_or_create(
                username=doc_data["username"],
                defaults={
                    "first_name": doc_data["first_name"],
                    "last_name": doc_data["last_name"],
                    "middle_name": doc_data["middle_name"],
                    "role": UserRole.DOCTOR,
                    "is_staff": True,
                },
            )
            if was_created:
                user.set_password("doctor123")
                user.save()
                self.stdout.write(f"  Created doctor user: {user.get_full_name()} ({user.username})")

            department = departments[doc_data["department_idx"]]
            staff, staff_created = Staff.objects.get_or_create(
                user=user,
                defaults={
                    "hospital": department.hospital,
                    "department": department,
                    "position": doc_data["position"],
                },
            )
            if staff_created:
                self.stdout.write(f"    → Assigned to department: {department.name} as {staff.position}")

            doctors.append(user)
        return doctors

    @transaction.atomic
    def _create_patients(self):
        patients = []
        for pat_data in PATIENTS_DATA:
            user, was_created = User.objects.get_or_create(
                username=pat_data["username"],
                defaults={
                    "first_name": pat_data["first_name"],
                    "last_name": pat_data["last_name"],
                    "middle_name": pat_data["middle_name"],
                    "role": UserRole.PATIENT,
                },
            )
            if was_created:
                user.set_password("patient123")
                user.save()
                self.stdout.write(f"  Created patient user: {user.get_full_name()} ({user.username})")

            p_data = pat_data["patient"]

            # Check if a patient profile already exists for this user (may have been created by signal)
            existing = Patient.objects.filter(user=user).first()
            if existing:
                # Update the existing profile with full details
                for field, value in p_data.items():
                    setattr(existing, field, value)
                existing.save()
                self.stdout.write(f"    → Updated patient profile: {existing.full_name}")
                patients.append(existing)
                continue

            patient, pat_created = Patient.objects.get_or_create(
                passport=p_data["passport"],
                defaults={
                    "user": user,
                    "full_name": p_data["full_name"],
                    "birth_date": p_data["birth_date"],
                    "gender": p_data["gender"],
                    "phone": p_data["phone"],
                    "email": p_data["email"],
                    "address": p_data["address"],
                    "emergency_contact": p_data["emergency_contact"],
                },
            )
            if pat_created:
                self.stdout.write(f"    → Created patient profile: {patient.full_name}")

            patients.append(patient)
        return patients

    @transaction.atomic
    def _create_lab_tests(self):
        tests = []
        for test_data in LAB_TESTS:
            test, was_created = AnalysisType.objects.get_or_create(
                code=test_data["code"],
                defaults={
                    "name": test_data["name"],
                    "price": test_data["price"],
                    "normal_range": test_data.get("normal_range", ""),
                    "description": test_data["description"],
                },
            )
            if was_created:
                self.stdout.write(f"  Created lab test: {test.name} (code: {test.code}, price: {test.price} UZS)")
            tests.append(test)
        return tests
