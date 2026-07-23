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
from lab.models import AnalysisField, AnalysisType
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
        from lab.models import AnalysisOrder, AnalysisResultValue

        demo_usernames = (
            [d["username"] for d in DOCTORS_DATA]
            + [p["username"] for p in PATIENTS_DATA]
        )

        # Delete analysis orders first (they have PROTECT FK to AnalysisType)
        test_codes = [t["code"] for t in LAB_TESTS]
        additional_codes = [t["code"] for t in self.ADDITIONAL_LAB_TESTS]
        all_codes = test_codes + additional_codes
        AnalysisType.objects.filter(code__in=all_codes).delete()

        User.objects.filter(username__in=demo_usernames).delete()

        Patient.objects.filter(passport__in=[p["patient"]["passport"] for p in PATIENTS_DATA]).delete()

        dept_names = [d["name"] for d in DEPARTMENTS]
        Department.objects.filter(name__in=dept_names).delete()

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

    # ── Standardized field definitions for each lab test ──
    LAB_TEST_FIELDS = {
        "CBC": [
            {"field_key": "hemoglobin", "field_name": "Гемоглобин (Hb)", "field_type": "numeric", "unit": "г/л", "reference_range_min": 120, "reference_range_max": 160, "sort_order": 1},
            {"field_key": "rbc", "field_name": "Эритроциты (RBC)", "field_type": "numeric", "unit": "×10¹²/л", "reference_range_min": 3.7, "reference_range_max": 4.7, "sort_order": 2},
            {"field_key": "wbc", "field_name": "Лейкоциты (WBC)", "field_type": "numeric", "unit": "×10⁹/л", "reference_range_min": 4.0, "reference_range_max": 9.0, "sort_order": 3},
            {"field_key": "platelets", "field_name": "Тромбоциты (PLT)", "field_type": "numeric", "unit": "×10⁹/л", "reference_range_min": 180, "reference_range_max": 320, "sort_order": 4},
            {"field_key": "hematocrit", "field_name": "Гематокрит (HCT)", "field_type": "numeric", "unit": "%", "reference_range_min": 35, "reference_range_max": 45, "sort_order": 5},
            {"field_key": "esr", "field_name": "СОЭ (ESR)", "field_type": "numeric", "unit": "мм/ч", "reference_range_min": 2, "reference_range_max": 15, "sort_order": 6},
        ],
        "BIO": [
            {"field_key": "glucose", "field_name": "Глюкоза", "field_type": "numeric", "unit": "ммоль/л", "reference_range_min": 3.3, "reference_range_max": 5.5, "sort_order": 1},
            {"field_key": "cholesterol", "field_name": "Холестерин общий", "field_type": "numeric", "unit": "ммоль/л", "reference_range_min": 3.5, "reference_range_max": 5.2, "sort_order": 2},
            {"field_key": "bilirubin_total", "field_name": "Билирубин общий", "field_type": "numeric", "unit": "мкмоль/л", "reference_range_min": 5, "reference_range_max": 21, "sort_order": 3},
            {"field_key": "alt", "field_name": "АЛТ (ALT)", "field_type": "numeric", "unit": "Ед/л", "reference_range_min": 10, "reference_range_max": 40, "sort_order": 4},
            {"field_key": "ast", "field_name": "АСТ (AST)", "field_type": "numeric", "unit": "Ед/л", "reference_range_min": 10, "reference_range_max": 40, "sort_order": 5},
            {"field_key": "creatinine", "field_name": "Креатинин", "field_type": "numeric", "unit": "мкмоль/л", "reference_range_min": 44, "reference_range_max": 106, "sort_order": 6},
            {"field_key": "urea", "field_name": "Мочевина", "field_type": "numeric", "unit": "ммоль/л", "reference_range_min": 2.5, "reference_range_max": 8.3, "sort_order": 7},
        ],
        "URINE": [
            {"field_key": "color", "field_name": "Цвет", "field_type": "choice", "options": ["Соломенно-жёлтый", "Тёмно-жёлтый", "Красный", "Мутный", "Бесцветный"], "sort_order": 1},
            {"field_key": "transparency", "field_name": "Прозрачность", "field_type": "choice", "options": ["Полная", "Неполная", "Мутная"], "sort_order": 2},
            {"field_key": "ph", "field_name": "pH", "field_type": "numeric", "unit": "", "reference_range_min": 5.0, "reference_range_max": 7.0, "sort_order": 3},
            {"field_key": "protein", "field_name": "Белок", "field_type": "choice", "options": ["Отрицательно", "Следы", "+", "++", "+++", "++++"], "sort_order": 4},
            {"field_key": "glucose_urine", "field_name": "Глюкоза", "field_type": "choice", "options": ["Отрицательно", "+", "++", "+++"], "sort_order": 5},
            {"field_key": "leukocytes", "field_name": "Лейкоциты", "field_type": "numeric", "unit": "в п/зр", "reference_range_min": 0, "reference_range_max": 5, "sort_order": 6},
        ],
        "ECG": [
            {"field_key": "rhythm", "field_name": "Ритм", "field_type": "choice", "options": ["Синусовый", "Мерцательная аритмия", "Синусовая тахикардия", "Синусовая брадикардия", "Экстрасистолия"], "sort_order": 1},
            {"field_key": "heart_rate", "field_name": "ЧСС", "field_type": "numeric", "unit": "уд/мин", "reference_range_min": 60, "reference_range_max": 90, "sort_order": 2},
            {"field_key": "conclusion", "field_name": "Заключение", "field_type": "text", "is_required": True, "sort_order": 3},
        ],
        "COAG": [
            {"field_key": "pt", "field_name": "Протромбиновое время (PT)", "field_type": "numeric", "unit": "сек", "reference_range_min": 11, "reference_range_max": 15, "sort_order": 1},
            {"field_key": "inr", "field_name": "МНО (INR)", "field_type": "numeric", "unit": "", "reference_range_min": 0.8, "reference_range_max": 1.2, "sort_order": 2},
            {"field_key": "aptt", "field_name": "АЧТВ (APTT)", "field_type": "numeric", "unit": "сек", "reference_range_min": 25, "reference_range_max": 35, "sort_order": 3},
            {"field_key": "fibrinogen", "field_name": "Фибриноген", "field_type": "numeric", "unit": "г/л", "reference_range_min": 2.0, "reference_range_max": 4.0, "sort_order": 4},
        ],
    }

    ADDITIONAL_LAB_TESTS = [
        {
            "name": "Группа крови и резус-фактор",
            "code": "BLOOD_GROUP",
            "price": 25000,
            "description": "Определение группы крови по системе AB0 и резус-фактора",
            "fields": [
                {"field_key": "blood_group", "field_name": "Группа крови", "field_type": "choice", "options": ["O (I) Rh+", "O (I) Rh-", "A (II) Rh+", "A (II) Rh-", "B (III) Rh+", "B (III) Rh-", "AB (IV) Rh+", "AB (IV) Rh-"], "sort_order": 1},
            ],
        },
        {
            "name": "Тест на COVID-19 (ПЦР)",
            "code": "COVID_PCR",
            "price": 80000,
            "description": "Выявление РНК коронавируса SARS-CoV-2 методом ПЦР",
            "fields": [
                {"field_key": "result", "field_name": "Результат", "field_type": "choice", "options": ["Положительный", "Отрицательный"], "sort_order": 1},
            ],
        },
        {
            "name": "Тест на ВИЧ",
            "code": "HIV",
            "price": 30000,
            "description": "Скрининговое исследование на антитела к ВИЧ 1/2",
            "fields": [
                {"field_key": "result", "field_name": "Результат", "field_type": "choice", "options": ["Положительный", "Отрицательный"], "sort_order": 1},
            ],
        },
        {
            "name": "HBsAg (Гепатит B)",
            "code": "HEP_B",
            "price": 25000,
            "description": "Определение поверхностного антигена вируса гепатита B",
            "fields": [
                {"field_key": "result", "field_name": "Результат", "field_type": "choice", "options": ["Положительный", "Отрицательный"], "sort_order": 1},
            ],
        },
        {
            "name": "Anti-HCV (Гепатит C)",
            "code": "HEP_C",
            "price": 30000,
            "description": "Определение суммарных антител к вирусу гепатита C",
            "fields": [
                {"field_key": "result", "field_name": "Результат", "field_type": "choice", "options": ["Положительный", "Отрицательный"], "sort_order": 1},
            ],
        },
        {
            "name": "Тест на беременность (ХГЧ)",
            "code": "PREGNANCY",
            "price": 15000,
            "description": "Определение хорионического гонадотропина человека в моче",
            "fields": [
                {"field_key": "result", "field_name": "Результат", "field_type": "choice", "options": ["Положительный", "Отрицательный"], "sort_order": 1},
            ],
        },
        {
            "name": "Рентгенография грудной клетки",
            "code": "XRAY_CHEST",
            "price": 60000,
            "description": "Обзорная рентгенография органов грудной клетки",
            "fields": [
                {"field_key": "findings", "field_name": "Описание", "field_type": "text", "is_required": True, "sort_order": 1},
                {"field_key": "conclusion", "field_name": "Заключение", "field_type": "text", "is_required": True, "sort_order": 2},
            ],
        },
        {
            "name": "УЗИ органов брюшной полости",
            "code": "US_ABDOMEN",
            "price": 70000,
            "description": "Ультразвуковое исследование органов брюшной полости",
            "fields": [
                {"field_key": "findings", "field_name": "Описание", "field_type": "text", "is_required": True, "sort_order": 1},
                {"field_key": "conclusion", "field_name": "Заключение", "field_type": "text", "is_required": True, "sort_order": 2},
            ],
        },
    ]

    @transaction.atomic
    def _create_lab_tests(self):
        tests = []
        # Create original 5 tests with their fields
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
            # Create fields for this test
            self._create_fields_for_test(test, test_data["code"])
            tests.append(test)

        # Create additional standardized tests
        for test_data in self.ADDITIONAL_LAB_TESTS:
            test, was_created = AnalysisType.objects.get_or_create(
                code=test_data["code"],
                defaults={
                    "name": test_data["name"],
                    "price": test_data["price"],
                    "description": test_data.get("description", ""),
                },
            )
            if was_created:
                self.stdout.write(f"  Created lab test: {test.name} (code: {test.code}, price: {test.price} UZS)")
            # Create fields for this test
            self._create_fields_for_test(test, test_data["code"], test_data.get("fields"))
            tests.append(test)

        return tests

    def _create_fields_for_test(self, test, code, custom_fields=None):
        """Create AnalysisField entries for a given test type."""
        if custom_fields:
            fields_defs = custom_fields
        else:
            fields_defs = self.LAB_TEST_FIELDS.get(code, [])

        for field_def in fields_defs:
            field, was_created = AnalysisField.objects.get_or_create(
                analysis_type=test,
                field_key=field_def["field_key"],
                defaults={
                    "field_name": field_def["field_name"],
                    "field_type": field_def["field_type"],
                    "options": field_def.get("options"),
                    "unit": field_def.get("unit", ""),
                    "reference_range_min": field_def.get("reference_range_min"),
                    "reference_range_max": field_def.get("reference_range_max"),
                    "is_required": field_def.get("is_required", True),
                    "sort_order": field_def.get("sort_order", 0),
                },
            )
            if was_created:
                self.stdout.write(f"    → Created field: {field.field_name} ({field.get_field_type_display()})")
