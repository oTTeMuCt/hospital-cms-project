# HCMS Feature Inventory & User Stories — COMPREHENSIVE SPREADSHEET

## Legend
- ✅ = Working
- ❌ = Broken/Not Working
- ⚠️ = Has Issues / Needs Verification
- 🔲 = Not Implemented
- 🚧 = In Progress

---

## 1. Authentication & User Management

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 1.1 | User Registration | As a new user, I want to register with username/password so I can access the system | POST /api/auth/register/ creates User, returns 201. For patient role, auto-creates Patient profile via signal | ✅ | Signal works. Frontend Register.jsx redirects to /patients/new after registration for patients | accounts/views.py: RegisterView, accounts/serializers.py: UserCreateSerializer, accounts/signals.py | Register.jsx |
| 1.2 | User Login | As a registered user, I want to login with my credentials to get JWT tokens | POST /api/auth/token/ returns {access, refresh} tokens | ✅ | Verified working | accounts/views.py: AuthTokenObtainPairView | Login.jsx, AuthContext.jsx |
| 1.3 | Token Refresh | As a logged-in user, I want my access token to auto-refresh when expired | axios interceptor catches 401, calls /api/auth/token/refresh/ | ✅ | Implemented in api.js interceptor | accounts/views.py: AuthTokenRefreshView | api.js |
| 1.4 | Token Verify | As a user, I want to verify my token is valid | POST /api/auth/token/verify/ | ✅ | Endpoint exists | accounts/urls.py: TokenVerifyView | Not used in frontend |
| 1.5 | View Profile (Me) | As a logged-in user, I want to see my profile info | GET /api/auth/me/ returns current user data | ✅ | Used in AuthContext.login() after successful token obtain | accounts/views.py: MeView | AuthContext.jsx |
| 1.6 | User List | As admin/registrar/doctor, I want to list all users | GET /api/users/ returns paginated user list | ✅ | Permission: admin/registrar/doctor/chief_doctor can view. Used in Hospitals.jsx, Departments.jsx for doctor dropdowns | accounts/views.py: UserListView | Hospitals.jsx, Departments.jsx, PatientForm.jsx |
| 1.7 | User Detail | As admin, I want to view a specific user | GET /api/users/{id}/ returns user detail | ✅ | Admin only | accounts/views.py: UserDetailView | Not used in frontend |
| 1.8 | Role-Based Access Control | As a user with a specific role, I should only see what my role allows | Permissions checked in backend views and frontend Sidebar | ✅ | Verified: 403 on /api/appointments/ for patient role (expected) | accounts/permissions.py | Sidebar.jsx, Dashboard.jsx |
| 1.9 | Logout | As a logged-in user, I want to logout | Clears localStorage tokens and user data | ✅ | Implemented in AuthContext.logout() | — | AuthContext.jsx, Sidebar.jsx |
| 1.10 | Registration Role Options | As a new user, I want to choose my role during registration | Frontend shows role dropdown with patient/doctor/lab_tech/registrar. Admin/chief_doctor not available for self-registration | ✅ | Hint text explains admin/chief_doctor are assigned by admin | — | Register.jsx |
| 1.11 | Password Validation | As a user, I want password validation on registration | Min 8 chars, password confirmation match | ✅ | Both frontend and backend validate | accounts/serializers.py: UserCreateSerializer | Register.jsx |

## 2. Patients

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 2.1 | List Patients | As staff, I want to see all patients | GET /api/patients/ returns paginated list | ✅ | Filtered by role: patients see only their own, staff see all | patients/views.py: PatientViewSet | Patients.jsx |
| 2.2 | Create Patient | As registrar/doctor, I want to register a new patient | POST /api/patients/ creates Patient record | ✅ | Permission: IsAuthenticatedAndRole (registrar/doctor/chief_doctor/lab_tech/admin) | patients/views.py: PatientViewSet | PatientForm.jsx |
| 2.3 | Edit Patient | As staff, I want to update patient info | PATCH /api/patients/{id}/ updates fields | ✅ | Implemented in modal. Permission: IsPatientOwnerOrStaff | patients/views.py: PatientViewSet | Patients.jsx (edit modal) |
| 2.4 | Delete Patient | As admin, I want to delete a patient | DELETE /api/patients/{id}/ removes record | ✅ | Admin only. Implemented with confirm dialog | patients/views.py: PatientViewSet | Patients.jsx |
| 2.5 | Search Patients | As staff, I want to search patients by name/phone/passport/pinfl/telegram | GET /api/patients/?search= filters results | ✅ | Search fields: full_name, phone, email, pinfl, passport, foreign_passport, telegram_id | patients/views.py: PatientViewSet | Patients.jsx |
| 2.6 | Filter Patients | As staff, I want to filter patients by gender/blood group | GET /api/patients/?gender=male&blood_group=I+ | ✅ | DjangoFilterBackend with filterset_fields | patients/views.py: PatientViewSet | Not used in frontend |
| 2.7 | View Patient Detail | As staff, I want to see full patient info | Modal shows all patient fields including gender_display, blood_group_display, telegram status | ✅ | Implemented in Patients.jsx modal | patients/serializers.py: PatientSerializer | Patients.jsx |
| 2.8 | Duplicate PINFL Rejection | As registrar, I should not be able to create duplicate PINFL | Serializer validate_pinfl() checks uniqueness | ✅ | Custom validation in serializer | patients/serializers.py: PatientSerializer | — |
| 2.9 | Duplicate Passport Rejection | As registrar, I should not be able to create duplicate passport | Serializer validate_passport() checks uniqueness + DB unique constraint | ✅ | Both serializer validation and DB UniqueConstraint with non-empty condition | patients/serializers.py, patients/models.py | — |
| 2.10 | Auto-Create Patient on Register | As a new patient user, my patient profile should be auto-created | Signal creates Patient when User with role=patient is created | ✅ | Signal in accounts/signals.py creates Patient with full_name from user name parts | accounts/signals.py | Register.jsx (redirects to /patients/new) |
| 2.11 | Sensitive Fields Protection | As a non-admin user, I should not see PINFL for patients | SensitiveFieldsMixin removes pinfl for non-admin/chief_doctor/registrar | ✅ | Implemented in accounts/serializers.py SensitiveFieldsMixin | accounts/serializers.py | — |
| 2.12 | Patient Self-View | As a patient user, I want to see only my own patient record | get_queryset filters by user=request.user for patient role | ✅ | Implemented in PatientViewSet.get_queryset() | patients/views.py | Patients.jsx |

## 3. Hospitals

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 3.1 | List Hospitals | As staff, I want to see all hospitals | GET /api/hospitals/ returns paginated list with departments | ✅ | Prefetch related departments | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.2 | Create Hospital | As admin, I want to add a new hospital | POST /api/hospitals/ creates Hospital | ✅ | Admin only for create/update/delete | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.3 | Edit Hospital | As admin, I want to update hospital info | PATCH /api/hospitals/{id}/ updates fields | ✅ | Admin only | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.4 | Delete Hospital | As admin, I want to delete a hospital | DELETE /api/hospitals/{id}/ removes record | ✅ | Admin only with confirm dialog | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.5 | Hospital Detail View | As staff, I want to see hospital details | Card view shows name, short_name, address, phone, working_hours | ✅ | Grid-2 layout with cards | hospitals/serializers.py: HospitalSerializer | Hospitals.jsx |
| 3.6 | Hospital Chief Doctor Assignment | As admin, I want to assign a chief doctor to a hospital | Dropdown shows doctors/chief_doctors from /api/users/ | ✅ | Fetches users filtered by role | hospitals/views.py | Hospitals.jsx |
| 3.7 | Sensitive Fields Protection (Hospital) | As non-admin, I should not see timezone/country_code | SensitiveFieldsMixin removes timezone/country_code for non-admin/chief_doctor | ✅ | Implemented in HospitalSerializer | accounts/serializers.py | — |

## 4. Departments

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 4.1 | List Departments | As staff, I want to see all departments | GET /api/departments/ returns paginated list | ✅ | Select related hospital | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.2 | Create Department | As chief_doctor/admin, I want to add a department | POST /api/departments/ creates Department | ✅ | IsChiefDoctor permission for create/update/delete | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.3 | Edit Department | As chief_doctor/admin, I want to update department info | PATCH /api/departments/{id}/ updates fields | ✅ | IsChiefDoctor permission | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.4 | Delete Department | As chief_doctor/admin, I want to delete a department | DELETE /api/departments/{id}/ removes record | ✅ | IsChiefDoctor permission with confirm dialog | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.5 | Department Type Selection | As staff, I want to choose department type from predefined list | Dropdown with therapy/surgery/cardiology/neurology/laboratory/xray/ultrasound/reception/other | ✅ | DepartmentType choices in model | hospitals/models.py | Departments.jsx |
| 4.6 | Department Manager Assignment | As admin, I want to assign a manager to a department | Dropdown shows all users | ✅ | Fetches all users for manager selection | hospitals/views.py | Departments.jsx |
| 4.7 | Department-Hospital Uniqueness | As staff, I should not create duplicate department names in same hospital | unique_together = (("hospital", "name"),) | ✅ | DB-level constraint | hospitals/models.py | — |

## 5. Staff

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 5.1 | List Staff | As staff, I want to see all employees | GET /api/staff/ returns paginated list | ✅ | Select related user, hospital, department | hospitals/views.py: StaffViewSet | Staff.jsx |
| 5.2 | Create Staff | As chief_doctor/admin, I want to add a staff member | POST /api/staff/ creates Staff record | ✅ | IsChiefDoctor permission | hospitals/views.py: StaffViewSet | Not in frontend |
| 5.3 | Edit Staff | As chief_doctor/admin, I want to update staff info | PATCH /api/staff/{id}/ updates fields | ✅ | IsChiefDoctor permission | hospitals/views.py: StaffViewSet | Not in frontend |
| 5.4 | Delete Staff | As chief_doctor/admin, I want to remove a staff member | DELETE /api/staff/{id}/ removes record | ✅ | IsChiefDoctor permission | hospitals/views.py: StaffViewSet | Not in frontend |
| 5.5 | Staff Display with User Info | As staff, I want to see full name and role | Serializer includes user_full_name and role from User model | ✅ | SerializerMethodField for full name | hospitals/serializers.py: StaffSerializer | Staff.jsx |
| 5.6 | Staff Photo Upload | As staff, I want to upload a photo | ImageField uploads to staff_photos/ | ✅ | Backend supports, frontend not implemented | hospitals/models.py | Not in frontend |

## 6. Medical Records

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 6.1 | List Medical Records | As a doctor, I want to see medical records | GET /api/medical-records/ returns list | ✅ | Doctor only permission | medrecords/views.py: MedicalRecordViewSet | Not in frontend |
| 6.2 | Create Medical Record | As a doctor, I want to create a medical record | POST /api/medical-records/ creates record | ✅ | Doctor only permission | medrecords/views.py: MedicalRecordViewSet | Not in frontend |
| 6.3 | Edit Medical Record | As a doctor, I want to update a medical record | PATCH /api/medical-records/{id}/ updates fields | ✅ | Doctor only permission | medrecords/views.py: MedicalRecordViewSet | Not in frontend |
| 6.4 | Delete Medical Record | As a doctor, I want to delete a medical record | DELETE /api/medical-records/{id}/ removes record | ✅ | Doctor only permission | medrecords/views.py: MedicalRecordViewSet | Not in frontend |
| 6.5 | Structured Diagnoses | As a doctor, I want to store diagnoses with ICD codes | JSONField with code, name, date structure | ✅ | JSONField with example format | medrecords/models.py | — |
| 6.6 | Structured Surgeries | As a doctor, I want to store surgery history | JSONField with name, date, hospital structure | ✅ | JSONField with example format | medrecords/models.py | — |
| 6.7 | Medical Record Fields | As a doctor, I want to record complaints, chronic conditions, allergies, vaccinations, medications | TextFields for each category | ✅ | Comprehensive medical record fields | medrecords/models.py | — |

## 7. Appointments

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 7.1 | List Appointments | As staff, I want to see all appointments | GET /api/appointments/ returns paginated list | ✅ | Select related patient, doctor, department, created_by | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 7.2 | Create Appointment | As staff, I want to create a new appointment | POST /api/appointments/ creates Appointment | ✅ | IsAuthenticatedAndRole (admin/chief_doctor/doctor/registrar) | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 7.3 | Edit Appointment | As staff, I want to update appointment details | PATCH /api/appointments/{id}/ updates fields | ✅ | IsAuthenticatedAndRole | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 7.4 | Delete Appointment | As staff, I want to delete an appointment | DELETE /api/appointments/{id}/ removes record | ✅ | IsAuthenticatedAndRole | appointments/views.py: AppointmentViewSet | Not in frontend |
| 7.5 | Appointment Status Management | As staff, I want to change appointment status | Buttons for pending→confirmed→completed, pending/confirmed→cancelled, no_show | ✅ | Status workflow buttons in table | appointments/models.py | Appointments.jsx |
| 7.6 | Appointment Status Display | As staff, I want to see status with color coding | Badge with warning/success/info/danger classes | ✅ | STATUS_LABELS mapping in frontend | — | Appointments.jsx |
| 7.7 | Doctor Time Conflict Prevention | As staff, I should not be able to double-book a doctor | Serializer checks overlapping appointments for same doctor | ✅ | Excludes cancelled appointments from conflict check | appointments/serializers.py: AppointmentSerializer | — |
| 7.8 | Appointment Search | As staff, I want to search appointments by patient/doctor/reason | GET /api/appointments/?search= filters results | ✅ | Search fields: patient__full_name, reason, doctor__last_name | appointments/views.py: AppointmentViewSet | Not used in frontend |
| 7.9 | Appointment Filtering | As staff, I want to filter by patient/doctor/department/status | GET /api/appointments/?status=pending filters | ✅ | DjangoFilterBackend with filterset_fields | appointments/views.py: AppointmentViewSet | Not used in frontend |
| 7.10 | Appointment End Time Auto-Calculation | As staff, I want end_time auto-set to 30 min after start | Serializer sets end_time = scheduled_at + 30 min if not provided | ✅ | Implemented in validate() | appointments/serializers.py: AppointmentSerializer | — |
| 7.11 | Appointment Patient/Doctor Name Display | As staff, I want to see patient and doctor names | SerializerMethodField for patient_name and doctor_name | ✅ | Falls back to IDs if names not available | appointments/serializers.py: AppointmentSerializer | Appointments.jsx |

## 8. Lab / Analyses

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 8.1 | List Analysis Types | As staff, I want to see available analysis types | GET /api/analysis-types/ returns list | ✅ | Authenticated users can view | lab/views.py: AnalysisTypeViewSet | Analyses.jsx |
| 8.2 | Create Analysis Type | As admin, I want to add a new analysis type | POST /api/analysis-types/ creates AnalysisType | ✅ | Admin only | lab/views.py: AnalysisTypeViewSet | Not in frontend |
| 8.3 | Edit Analysis Type | As admin, I want to update analysis type | PATCH /api/analysis-types/{id}/ updates fields | ✅ | Admin only | lab/views.py: AnalysisTypeViewSet | Not in frontend |
| 8.4 | Delete Analysis Type | As admin, I want to delete an analysis type | DELETE /api/analysis-types/{id}/ removes record | ✅ | Admin only | lab/views.py: AnalysisTypeViewSet | Not in frontend |
| 8.5 | List Analysis Orders | As staff, I want to see all analysis orders | GET /api/analysis-orders/ returns paginated list | ✅ | Patients see only their own, staff see all | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 8.6 | Create Analysis Order | As a doctor, I want to order an analysis for a patient | POST /api/analysis-orders/ creates order | ✅ | Doctor only for creation | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 8.7 | Edit Analysis Order | As lab_tech, I want to update analysis order (status, results) | PATCH /api/analysis-orders/{id}/ updates fields | ✅ | Lab tech for updates | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 8.8 | Delete Analysis Order | As admin, I want to delete an analysis order | DELETE /api/analysis-orders/{id}/ removes record | ✅ | Admin only | lab/views.py: AnalysisOrderViewSet | Not in frontend |
| 8.9 | Analysis Status Workflow | As staff, I want to progress analysis through statuses | created→ordered→in_progress→completed→verified→sent | ✅ | ALLOWED_TRANSITIONS dict enforces valid transitions | lab/models.py | Analyses.jsx |
| 8.10 | Status Transition Validation | As staff, I should not be able to skip statuses | Serializer validate_status() checks ALLOWED_TRANSITIONS | ✅ | Returns descriptive error message | lab/serializers.py: AnalysisOrderSerializer | — |
| 8.11 | Analysis Order Search | As staff, I want to search orders by patient/type/result | GET /api/analysis-orders/?search= filters | ✅ | Search fields: patient__full_name, analysis_type__name, result | lab/views.py: AnalysisOrderViewSet | Not used in frontend |
| 8.12 | Analysis Order Filtering | As staff, I want to filter by patient/status/type | GET /api/analysis-orders/?status=completed filters | ✅ | DjangoFilterBackend | lab/views.py: AnalysisOrderViewSet | Not used in frontend |
| 8.13 | AnalysisField Model | Lab tests should have predefined structured fields | AnalysisField model with field_type (choice/numeric/text), options, unit, reference_range_min/max | ✅ | Implemented | lab/models.py | — |
| 8.14 | AnalysisResultValue Model | Lab results should be stored as structured field values | AnalysisResultValue stores value per field per order, with interpretation for numeric | ✅ | Implemented | lab/models.py | — |
| 8.15 | Field Validation — Choice | Choice fields should only accept valid options | Serializer validates value is in field.options list | ✅ | Implemented | lab/serializers.py | — |
| 8.16 | Field Validation — Numeric | Numeric fields should only accept numbers | Serializer validates value is numeric, computes interpretation | ✅ | Implemented | lab/serializers.py | — |
| 8.17 | Field Validation — Required | Required fields must have values | Serializer validates required fields are present | ✅ | Implemented | lab/serializers.py | — |
| 8.18 | Dynamic Result Entry UI | Depending on selected analysis type, show appropriate input controls | Dropdown for choice, number input for numeric, textarea for text | ✅ | Implemented | — | Analyses.jsx |
| 8.19 | Structured Results Display | Results display with field names, values, units, reference ranges | Table format with interpretation badges | ✅ | Implemented | — | Analyses.jsx |
| 8.20 | Auto-Interpretation for Numeric Fields | Numeric results should auto-compute normal/high/low | Serializer.update() computes interpretation based on reference ranges | ✅ | Implemented in update() method | lab/serializers.py: AnalysisOrderSerializer | — |
| 8.21 | Legacy result Field Preservation | Old result field should still work alongside new result_values | update() sets result field from structured values | ✅ | Backward compatible | lab/serializers.py: AnalysisOrderSerializer | — |
| 8.22 | Analysis Type Detail with Fields | As staff, I want to see analysis type with its predefined fields | GET /api/analysis-types/{id}/ returns fields nested | ✅ | AnalysisTypeDetailSerializer with nested fields | lab/serializers.py | Analyses.jsx (openResultModal) |
| 8.23 | Patient Self-View Analyses | As a patient, I want to see only my own analyses | get_queryset filters by patient__user=request.user for patient role | ✅ | Implemented in AnalysisOrderViewSet | lab/views.py | MyAnalyses.jsx |

## 9. Files

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 9.1 | List Files | As authenticated user, I want to see uploaded files | GET /api/files/ returns list | ✅ | IsAuthenticated for list/retrieve/create | files/views.py: FileViewSet | Not in frontend |
| 9.2 | Upload File | As authenticated user, I want to upload a file | POST /api/files/ creates File record | ✅ | GenericForeignKey to any model | files/views.py: FileViewSet | Not in frontend |
| 9.3 | Delete File | As admin, I want to delete a file | DELETE /api/files/{id}/ removes record | ✅ | Admin only | files/views.py: FileViewSet | Not in frontend |
| 9.4 | Generic File Attachment | Files can be attached to any model via ContentType | GenericForeignKey with content_type/object_id | ✅ | Flexible attachment system | files/models.py | — |
| 9.5 | Organized File Storage | Files should be stored in organized directories | upload_to: files/<app_label>/<model>/<object_id>/<filename> | ✅ | Clean directory structure | files/models.py | — |

## 10. Notifications

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 10.1 | List Notifications | As registrar+, I want to see notifications | GET /api/notifications/ returns list | ✅ | IsRegistrar for list/retrieve | notifications/views.py: NotificationViewSet | Not in frontend |
| 10.2 | Create Notification | As authenticated user, I want to send a notification | POST /api/notifications/ creates Notification | ✅ | IsAuthenticated for create | notifications/views.py: NotificationViewSet | Not in frontend |
| 10.3 | Edit/Delete Notification | As admin, I want to manage notifications | PATCH/DELETE /api/notifications/{id}/ | ✅ | Admin only for update/delete | notifications/views.py: NotificationViewSet | Not in frontend |
| 10.4 | Multi-Channel Support | Notifications can be sent via Telegram/SMS/Email/Push | NotificationChannel choices: telegram, sms, email, push | ✅ | Channel field in model | notifications/models.py | — |
| 10.5 | Notification Status Tracking | As staff, I want to track notification delivery status | Status: pending/sent/failed with error_message | ✅ | Status tracking with timestamps | notifications/models.py | — |
| 10.6 | Generic Recipient | Notifications can be sent to any model via ContentType | GenericForeignKey for recipient | ✅ | Flexible recipient system | notifications/models.py | — |

## 11. Audit

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 11.1 | List Audit Logs | As admin, I want to see all audit logs | GET /api/audit-logs/ returns paginated list | ✅ | Admin only, ReadOnlyModelViewSet | audit/views.py: AuditLogViewSet | AuditLog.jsx |
| 11.2 | Automatic Audit Logging | All mutating API calls should be logged automatically | AuditMiddleware logs POST/PUT/PATCH/DELETE + auth GETs | ✅ | Middleware logs method, path, user, IP, user-agent, status | audit/middleware.py | — |
| 11.3 | Audit Log Search | As admin, I want to search audit logs | GET /api/audit-logs/?search= filters by action/username/ip | ✅ | SearchFilter on action, user__username, ip_address | audit/views.py: AuditLogViewSet | Not used in frontend |
| 11.4 | Audit Log Ordering | As admin, I want to sort audit logs | Ordered by -created_at by default | ✅ | OrderingFilter available | audit/views.py: AuditLogViewSet | Not used in frontend |
| 11.5 | Health Check Skipped | Health check endpoint should not create audit logs | SKIP_PREFIXES includes /health/ | ✅ | Middleware skips health, admin jsi18n, static | audit/middleware.py | — |
| 11.6 | Audit Log Display | As admin, I want to see formatted audit logs | Table with datetime, user, action, IP, success/failure badge | ✅ | Implemented in AuditLog.jsx | — | AuditLog.jsx |

## 12. Reports

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 12.1 | Patients PDF Report | As chief_doctor, I want to download patients list as PDF | GET /api/reports/patients/pdf/ returns PDF | ✅ | IsChiefDoctor permission. ReportLab PDF with styled table | reports/views.py: PatientsPDFView | Reports.jsx (CSV only) |
| 12.2 | Patients Excel Report | As chief_doctor, I want to download patients list as Excel | GET /api/reports/patients/excel/ returns XLSX | ✅ | IsChiefDoctor permission. OpenPyXL with auto-width columns | reports/views.py: PatientsExcelView | Reports.jsx (CSV only) |
| 12.3 | Analyses PDF Report | As chief_doctor, I want to download analyses report as PDF | GET /api/reports/analyses/pdf/ returns PDF | ✅ | IsChiefDoctor permission. ReportLab PDF with styled table | reports/views.py: AnalysesPDFView | Reports.jsx (CSV only) |
| 12.4 | Doctor Schedule PDF Report | As chief_doctor, I want to download a doctor's schedule as PDF | GET /api/reports/schedule/{doctor_id}/pdf/ returns PDF | ✅ | IsChiefDoctor permission. Raises NotFound if no appointments | reports/views.py: SchedulePDFView | Not in frontend |
| 12.5 | Patients CSV Export (Frontend) | As staff, I want to export patients to CSV | Frontend fetches all pages, generates CSV with BOM | ✅ | Handles pagination via fetchAllPages() | — | Reports.jsx |
| 12.6 | Analyses CSV Export (Frontend) | As staff, I want to export analyses to CSV | Frontend fetches all pages, generates CSV with BOM | ✅ | Handles pagination via fetchAllPages() | — | Reports.jsx |

## 13. Stats

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 13.1 | Patient Stats | As chief_doctor, I want to see patient statistics | GET /api/stats/patients/ returns total, by_gender, by_blood_group | ✅ | IsChiefDoctor permission | stats/views.py: PatientStatsView | Not in frontend |
| 13.2 | Analysis Stats | As chief_doctor, I want to see analysis statistics | GET /api/stats/analyses/ returns total, by_status, by_type | ✅ | IsChiefDoctor permission | stats/views.py: AnalysisStatsView | Not in frontend |
| 13.3 | Doctor Stats | As chief_doctor, I want to see doctor appointment counts | GET /api/stats/doctors/ returns appointment counts per doctor | ✅ | IsChiefDoctor permission | stats/views.py: DoctorStatsView | Not in frontend |
| 13.4 | Hospital Stats | As chief_doctor, I want to see hospital summary | GET /api/stats/hospitals/ returns hospital/department/staff counts | ✅ | IsChiefDoctor permission | stats/views.py: HospitalStatsView | Not in frontend |
| 13.5 | Daily Stats | As chief_doctor, I want to see daily appointment counts | GET /api/stats/daily/ returns appointments grouped by date | ✅ | IsChiefDoctor permission | stats/views.py: DailyStatsView | Not in frontend |

## 14. Telegram Bot

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 14.1 | Bot Patient Lookup by Passport | As a patient, I want to find my data via Telegram by passport | GET /api/bot/patient-analyses/?passport= returns patient + analyses | ✅ | X-Bot-Key header authentication | lab/views.py: BotPatientAnalysesView | — |
| 14.2 | Bot Patient Lookup by PINFL | As a patient, I want to find my data via Telegram by PINFL | GET /api/bot/patient-analyses/?pinfl= returns patient + analyses | ✅ | X-Bot-Key header authentication | lab/views.py: BotPatientAnalysesView | — |
| 14.3 | Bot Authentication | Bot endpoint should be protected by API key | X-Bot-Key header must match BOT_API_KEY env var | ✅ | Returns 403 if key missing/wrong | lab/views.py: BotPatientAnalysesView | — |
| 14.4 | Bot Structured Results | Bot should return structured analysis results | BotAnalysisResultSerializer includes result_fields with field_name, value, unit, interpretation, reference_range | ✅ | Implemented | lab/bot_serializers.py | — |
| 14.5 | Bot Error Handling | Bot should return proper error messages | 400 for missing params, 404 for patient not found, 409 for multiple patients | ✅ | Comprehensive error handling | lab/views.py: BotPatientAnalysesView | — |
| 14.6 | Bot Logging | Bot requests should be logged | Logger with request details, patient lookup, analysis count | ✅ | INFO/WARNING/ERROR levels | lab/views.py: BotPatientAnalysesView | — |
| 14.7 | Bot App | Telegram bot application | bot/app.py and bot/run_bot.py | ✅ | Dockerized bot service | bot/app.py, bot/run_bot.py | — |

## 15. Dashboard

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 15.1 | Dashboard Stats Cards | As a user, I want to see key metrics on dashboard | Cards showing patient/appointment/analysis counts | ✅ | Uses Promise.allSettled for resilience | — | Dashboard.jsx |
| 15.2 | Role-Specific Welcome Message | As a user, I want to see a role-appropriate welcome | Different welcome text per role | ✅ | ROLE_WELCOME mapping | — | Dashboard.jsx |
| 15.3 | Role Badge Display | As a user, I want to see my role and email | Badge with role label and email | ✅ | Uses roleLabel from AuthContext | — | Dashboard.jsx |
| 15.4 | Doctor Quick Actions | As a doctor, I want quick links to common tasks | Links to patients, appointments, analyses | ✅ | Role-specific quick action cards | — | Dashboard.jsx |
| 15.5 | Registrar Quick Actions | As a registrar, I want quick links to registration | Links to new patient, appointments, patient search | ✅ | Role-specific quick action cards | — | Dashboard.jsx |
| 15.6 | Lab Tech Quick Actions | As a lab tech, I want quick link to analysis queue | Link to analyses page | ✅ | Role-specific quick action cards | — | Dashboard.jsx |
| 15.7 | Admin Management Links | As admin, I want links to management sections | Links to hospitals, departments, staff, audit, reports | ✅ | Grid-2 layout with management and monitoring cards | — | Dashboard.jsx |
| 15.8 | Error Handling on Dashboard | As a user, I should see errors gracefully | Error message if stats fail to load, individual API failures show "—" | ✅ | Promise.allSettled with fallback values | — | Dashboard.jsx |

## 16. Sidebar

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 16.1 | Role-Based Navigation | As a user, I should only see links relevant to my role | Different link sets per role (admin/chief_doctor/doctor/lab_tech/registrar/patient) | ✅ | links object maps role to nav items | — | Sidebar.jsx |
| 16.2 | Active Link Highlighting | As a user, I want to see which page I'm on | NavLink active class with CSS styling | ✅ | React Router NavLink with isActive | — | Sidebar.jsx |
| 16.3 | User Info in Sidebar | As a user, I want to see my name and role in sidebar | Footer shows user name and role label | ✅ | Sidebar footer with user info | — | Sidebar.jsx |
| 16.4 | Logout Button | As a user, I want to logout from sidebar | Logout button in sidebar footer | ✅ | Calls logout() from AuthContext | — | Sidebar.jsx |
| 16.5 | Admin Full Navigation | As admin, I want access to all system sections | 9 links: Dashboard, Hospitals, Departments, Staff, Patients, Appointments, Analyses, Reports, Audit | ✅ | Most comprehensive nav set | — | Sidebar.jsx |
| 16.6 | Patient Limited Navigation | As a patient, I want only my relevant sections | 2 links: My Data (Dashboard), My Analyses | ✅ | Minimal nav set | — | Sidebar.jsx |

## 17. Frontend Infrastructure

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 17.1 | JWT Token Interceptor | API calls should automatically include JWT token | axios interceptor adds Bearer token to all requests | ✅ | Implemented in api.js | — | api.js |
| 17.2 | Auto Token Refresh | Expired tokens should auto-refresh | 401 response triggers refresh token flow | ✅ | Interceptor retries original request after refresh | — | api.js |
| 17.3 | Auth Context | User state should be available app-wide | AuthProvider with login/logout/isAuthenticated/role/roleLabel | ✅ | Context with localStorage persistence | — | AuthContext.jsx |
| 17.4 | Route Protection | Unauthenticated users should be redirected to login | MainLayout checks isAuthenticated, redirects to /login | ✅ | Navigate component for redirect | — | MainLayout.jsx |
| 17.5 | Loading States | Users should see loading indicators | Spinner component during data fetching | ✅ | Consistent loading pattern across pages | — | All pages |
| 17.6 | Error Alerts | Users should see error messages | Alert component with error styling | ✅ | Consistent error handling pattern | — | All pages |
| 17.7 | Empty States | Users should see helpful empty state messages | Empty state with icon, message, and CTA button | ✅ | Consistent empty state pattern | — | All pages |
| 17.8 | Pagination | API responses should be paginated | PageNumberPagination with PAGE_SIZE=50 | ✅ | DRF default pagination | config/settings.py | — |
| 17.9 | API Documentation | Developers should have API docs | Swagger UI at /api/docs/, Redoc at /api/redoc/ | ✅ | drf-spectacular integration | config/urls.py | — |
| 17.10 | Health Check | System health should be checkable | GET /health/ returns {"status": "ok", "service": "backend"} | ✅ | Simple health endpoint | config/urls.py | — |

## 18. Routing

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 18.1 | Login Route | Users can access login page | /login renders Login component | ✅ | Public route | — | App.jsx |
| 18.2 | Register Route | Users can access registration page | /register renders Register component | ✅ | Public route | — | App.jsx |
| 18.3 | Dashboard Route | Authenticated users see dashboard | / renders Dashboard component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.4 | Hospitals Route | Admin can manage hospitals | /hospitals renders Hospitals component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.5 | Departments Route | Admin can manage departments | /departments renders Departments component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.6 | Staff Route | Admin can view staff | /staff renders Staff component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.7 | Patients Route | Staff can manage patients | /patients renders Patients component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.8 | New Patient Route | Staff can register patients | /patients/new renders PatientForm component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.9 | Appointments Route | Staff can manage appointments | /appointments renders Appointments component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.10 | Analyses Route | Staff can manage lab analyses | /analyses renders Analyses component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.11 | Audit Log Route | Admin can view audit logs | /audit renders AuditLog component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.12 | Reports Route | Chief doctor/admin can view reports | /reports renders Reports component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.13 | My Analyses Route | Patients can view their analyses | /my-analyses renders MyAnalyses component | ✅ | Protected by MainLayout | — | App.jsx |
| 18.14 | Catch-All Redirect | Unknown routes redirect to dashboard | * redirects to / | ✅ | Navigate component | — | App.jsx |

## 19. Known Issues & Bugs

| # | Issue | Severity | Description | File(s) |
|---|-------|----------|-------------|---------|
| 19.1 | Appointment Doctor Field Mapping | ✅ Fixed | Changed from /staff/ to /users/ with role=doctor/chief_doctor filter. Now properly maps User IDs. | Appointments.jsx |
| 19.2 | MyAnalyses First Patient Assumption | ✅ Fixed | Now relies on backend filtering (patient role sees only their own analyses via get_queryset). | MyAnalyses.jsx |
| 19.3 | PatientForm User Lookup | ✅ Fixed | Now stores user ID in sessionStorage as JSON object. Falls back to legacy lookup for old format. | PatientForm.jsx, Register.jsx |
| 19.4 | Staff Page No CRUD | ⚠️ Low | Staff.jsx only lists staff, no create/edit/delete frontend. Backend supports full CRUD. | Staff.jsx |
| 19.5 | Medical Records No Frontend | ⚠️ Low | Backend has full MedicalRecord CRUD but no frontend pages. | — |
| 19.6 | Files No Frontend | ⚠️ Low | Backend has full File CRUD but no frontend pages. | — |
| 19.7 | Notifications No Frontend | ⚠️ Low | Backend has full Notification CRUD but no frontend pages. | — |
| 19.8 | Stats No Frontend | ⚠️ Low | Backend has 5 stats endpoints but no frontend pages. | — |
| 19.9 | Reports Backend Endpoints Not Used | ⚠️ Low | Backend has PDF/Excel report endpoints but frontend Reports.jsx only uses CSV export via API data fetching. | reports/views.py, Reports.jsx |
| 19.10 | Appointment Delete Not in Frontend | ⚠️ Low | Backend supports DELETE on appointments but frontend has no delete button. | Appointments.jsx |
| 19.11 | Analysis Order Delete Not in Frontend | ⚠️ Low | Backend supports DELETE on analysis orders but frontend has no delete button. | Analyses.jsx |
| 19.12 | Department Manager Name Display | ✅ Fixed | Added `manager_name` SerializerMethodField to DepartmentSerializer. Now shows full name. | hospitals/serializers.py |
| 19.13 | Hospital Chief Doctor Name Display | ⚠️ Low | Hospitals.jsx doesn't display chief doctor name in the card view, only in the edit form. | Hospitals.jsx |
| 19.14 | Staff Filtering for Doctor Dropdown | ✅ Fixed | Changed from /staff/ to /users/ with role filter (doctor/chief_doctor only). | Appointments.jsx |
| 19.15 | Poor Error Handling on Appointment Create | ✅ Fixed | Added proper error extraction from response data with field-specific messages. | Appointments.jsx |
| 19.16 | Audit Log User Name Display | ✅ Already Working | Serializer already includes user_name field that shows full_name_display. | audit/serializers.py |
| 19.17 | Reports Page No Backend PDF/Excel Integration | ⚠️ Low | Reports.jsx only does CSV export via frontend aggregation. Backend PDF/Excel endpoints exist but aren't linked in the UI. | Reports.jsx |
| 19.18 | Patient Edit Modal No Blood Group Display | ⚠️ Low | Patient edit modal doesn't show blood_group_display, only raw value. | Patients.jsx |
| 19.19 | No Pagination Controls in Frontend | ⚠️ Medium | Frontend pages don't implement pagination controls. They fetch all results at once. Works for small datasets. | All list pages |
| 19.20 | Dashboard Stats Uses List Endpoints | ✅ Fixed | Now uses paginated queries with page_size=1 to efficiently get counts without fetching full data. | Dashboard.jsx |
| 19.21 | No Confirmation on Appointment Status Change | ⚠️ Low | Appointments.jsx status change buttons don't have confirmation dialogs. | Appointments.jsx |
| 19.22 | Analysis Status Change No Confirmation | ⚠️ Low | Analyses.jsx status change buttons don't have confirmation dialogs. | Analyses.jsx |
| 19.23 | Register Page Missing Admin/Chief Doctor Roles | ⚠️ Low | Register page doesn't allow selecting admin or chief_doctor roles, which is intentional but could be confusing. | Register.jsx |
| 19.24 | No Password Change/Reset Feature | 🔲 Missing | There's no password change or reset functionality anywhere. | — |
| 19.25 | No User Profile Edit Page | 🔲 Missing | Users cannot edit their own profile (name, email, etc.) from the frontend. | — |
| 19.26 | No Department Filter by Hospital | ⚠️ Low | Departments page doesn't filter by hospital. Shows all departments. | Departments.jsx |
| 19.27 | No Staff Filter by Hospital/Department | ⚠️ Low | Staff page doesn't have search or filter functionality. | Staff.jsx |
| 19.28 | No Analysis Type Management UI | ⚠️ Low | Analysis types can only be managed via admin panel or API directly. | — |
| 19.29 | No Analysis Field Management UI | ⚠️ Low | Analysis fields can only be managed via admin panel or API directly. | — |
| 19.30 | No File Upload UI | 🔲 Missing | File upload feature has no frontend UI anywhere. | — |
| 19.31 | No Notification UI | 🔲 Missing | Notification feature has no frontend UI anywhere. | — |
| 19.32 | No Medical Records UI | 🔲 Missing | Medical records feature has no frontend UI anywhere. | — |
| 19.33 | No Stats Dashboard UI | 🔲 Missing | Stats endpoints have no frontend visualization. | — |
| 19.34 | No Doctor Schedule PDF Download UI | 🔲 Missing | Backend has SchedulePDFView but no frontend button to download it. | — |
| 19.35 | No Analysis Type Filter on Analyses Page | ⚠️ Low | Analyses page doesn't filter by analysis type. | Analyses.jsx |
| 19.36 | No Date Range Filter on Appointments | ⚠️ Low | Appointments page doesn't have date range filtering. | Appointments.jsx |
| 19.37 | No Patient History Timeline | 🔲 Missing | No timeline view of patient's appointments, analyses, and medical records. | — |
| 19.38 | No Data Export for Individual Patient | 🔲 Missing | Cannot export a single patient's data. | — |
| 19.39 | No Bulk Patient Import | 🔲 Missing | No CSV/Excel import for bulk patient registration. | — |
| 19.40 | No SMS/Email/Telegram Sending Implementation | ⚠️ Low | Notification model supports channels but actual sending logic is not implemented in the frontend or backend tasks. | notifications/models.py |
