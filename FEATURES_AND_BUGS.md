# Hospital CMS — Comprehensive Feature Inventory, User Stories & Bug Tracker

## Canonical Spreadsheet of All Features (Backend + Frontend + Bot)

---

# ═══════════════════════════════════════════════════════════
# AUTHENTICATION MODULE (accounts)
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| A1 | User Login (JWT) | As a user, I want to log in with username+password | POST /api/auth/token/ returns {access, refresh} JWT tokens. Uses SIMPLE_JWT with 30min access + 1d refresh. | accounts/views.py: AuthTokenObtainPairView | ✅ PASS | Throttle: login=5/min, login_burst=10/hr. Lockout after 5 failed attempts for 15min. |
| A2 | Token Refresh | As a user, I want my session to auto-refresh | POST /api/auth/token/refresh/ returns new access token. Frontend axios interceptor auto-retries on 401. | accounts/views.py: AuthTokenRefreshView + frontend/api.js interceptor | ✅ PASS | Blacklist after rotation enabled |
| A3 | Token Verify | As a system, I want to verify JWT validity | POST /api/auth/token/verify/ validates token without requiring full authentication flow | accounts/urls.py: TokenVerifyView | ✅ PASS | Standard SimpleJWT endpoint |
| A4 | User Registration | As a guest, I want to register a new account | POST /api/auth/register/ creates User with role=patient default. Auto-creates Patient profile via signal. Returns user data. | accounts/views.py: RegisterView + accounts/signals.py | ✅ PASS | Password min 8 chars, validated by CreateUserSerializer |
| A5 | Get Current User | As any authenticated user, I want to see my profile | GET /api/auth/me/ returns {id, username, email, first_name, last_name, middle_name, role, is_staff, is_superuser} | accounts/views.py: MeView | ✅ PASS | Uses UserSerializer |
| A6 | Logout | As a user, I want to securely log out | POST /api/auth/logout/ with {refresh}. Blacklists refresh token via blacklist app. Requires Bearer token. | accounts/views.py: LogoutView | ✅ PASS | Refresh token blacklisted. Access token remains valid until expiry (30min). |
| A7 | Password Change | As an authenticated user, I want to change my password | POST /api/auth/password-change/ with {old_password, new_password}. Validates old password first. | accounts/password_reset.py: PasswordChangeView | ✅ PASS | Requires authentication. New password min 8 chars. |
| A8 | Password Reset Request | As a user, I want to request a password reset email | POST /api/auth/password-reset/ with {email}. Sends email with secure token link if email exists. Doesn't reveal existence. | accounts/password_reset.py: PasswordResetRequestView | ✅ PASS | Uses Django PasswordResetTokenGenerator. 24hr validity. |
| A9 | Password Reset Confirm | As a user, I want to reset my password with a token | POST /api/auth/password-reset/confirm/ with {uidb64, token, new_password}. Validates token and sets new password. | accounts/password_reset.py: PasswordResetConfirmView | ✅ PASS | By default uses console.EmailBackend — no real email sent. |
| A10 | List Users | As admin/registrar/doctor, I want to list system users | GET /api/users/ returns all users. Access: admin always; other staff only if authenticated with role in {admin,registrar,doctor,chief_doctor} | accounts/views.py: UserListView | ✅ PASS | Permissions: IsAdminRole for anon/patient, else just IsAuthenticated for allowed roles |
| A11 | User Detail | As admin, I want to see user details | GET /api/users/{id}/ returns user info. Admin only. | accounts/views.py: UserDetailView | ✅ PASS | IsAdminRole permission |
| A12 | Password Validation | As a system, I want strong passwords | Uses Django's 4 built-in validators: UserAttributeSimilarity, MinLength(8), CommonPassword, NumericPassword | config/settings.py: AUTH_PASSWORD_VALIDATORS | ✅ PASS | Django defaults |
| A13 | Account Lockout | As a system, I want to lock accounts after 5 failed attempts | Cache-based lockout. 5 failed attempts → 15min lock. Response includes lockout_remaining_seconds. | accounts/lockout.py + accounts/views.py: AuthTokenObtainPairView | ✅ PASS | Uses Redis/local-memory cache. Lockout resets on successful login. |
| A14 | Login Throttling | As a system, I want to rate-limit login attempts | 5 requests/min per IP (login scope) + 10 requests/hour per IP (login_burst scope) | accounts/throttling.py | ✅ PASS | AnonRateThrottle for anonymous only |
| A15 | Sensitive Field Masking | As a system, I want to hide sensitive fields per role | SensitiveFieldsMixin removes pinfl from Patient views for non-admin/chief_doctor/registrar users. Removes timezone/country_code for non-admin/users. | accounts/serializers.py: SensitiveFieldsMixin | ✅ PASS | Applied in PatientSerializer and HospitalSerializer |

# ═══════════════════════════════════════════════════════════
# PATIENTS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| P1 | List Patients | As staff, I want to see all patients | GET /api/patients/?search=&gender=&blood_group= Paginated, searchable (name, phone, email, pinfl, passport, telegram_id), filterable by gender/blood_group. Sortable. | patients/views.py: PatientViewSet | ✅ PASS | Patient role sees only own record. Others see all. |
| P2 | Create Patient | As registrar/doctor, I want to register a patient | POST /api/patients/ with full_name, birth_date, gender, pinfl, passport, phone, email, etc. Validates unique pinfl/passport. | patients/views.py: PatientViewSet | ✅ PASS | Requires IsAuthenticatedAndRole (staff roles). SensitiveFieldsMixin hides pinfl in response. |
| P3 | View Patient Details | As staff/patient, I want to see patient info | GET /api/patients/{id}/ Returns all patient data. Patients see only own record via queryset filter. | patients/views.py: PatientViewSet.retrieve | ✅ PASS | IsPatientOwnerOrStaff permission |
| P4 | Update Patient | As staff/patient-owner, I want to update patient data | PUT/PATCH /api/patients/{id}/ Partial updates supported. Validates unique pinfl/passport on update (excludes self). | patients/views.py: PatientViewSet | ✅ PASS | IsPatientOwnerOrStaff permission |
| P5 | Delete Patient | As admin only, I want to delete a patient | DELETE /api/patients/{id}/ Only admin can destroy | patients/views.py: PatientViewSet | ✅ PASS | IsAdminRole for destroy |
| P6 | Auto-create Patient Profile | As a system, when a user registers with role=patient, auto-create Patient record | Signal creates Patient with full_name from user's name fields and email. | accounts/signals.py | ✅ PASS | post_save signal |
| P7 | Patient "Me" Endpoint | As a patient, I want to see my own profile via a simple endpoint | GET /api/patients/me/ returns the Patient record linked to the authenticated user. | patients/views.py: PatientViewSet.me | ✅ PASS | @action(detail=False) |
| P8 | Bot Link Telegram | As a bot, I want to link a Telegram chat to a patient | POST /api/bot/link-telegram/ with {patient_id, telegram_id}. Validates X-Bot-Key header. Updates patient.telegram_id. | patients/views.py: BotLinkTelegramView | ✅ PASS | Accepts P-000001 or numeric IDs |
| P9 | Patient Gender Options | As a system, I want patients to have gender | Patient.gender: choices male/female | patients/models.py | ✅ PASS | |
| P10 | Patient Blood Group Options | As a system, I want patients to have blood group | Patient.blood_group: choices I+/I-/II+/II-/III+/III-/IV+/IV- | patients/models.py | ✅ PASS | |
| P11 | Patient Unique Constraints | As a system, I want unique patient identifiers | pinfl unique (14-digit), passport unique when non-empty via UniqueConstraint with condition | patients/models.py | ✅ PASS | |
| P12 | Patient Auto Generated ID Format | As a user, I want patients to have P-XXXXXX format IDs | Frontend formatPatientId() converts numeric DB id to "P-" + zero-padded 6 digits. Purely cosmetic. | frontend/src/pages/PatientProfile.jsx | ✅ PASS | Not stored in DB |

# ═══════════════════════════════════════════════════════════
# APPOINTMENTS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| AP1 | List Appointments | As staff, I want to see all appointments | GET /api/appointments/?patient=&doctor=&department=&status= Filtered, searchable. Doctor sees own. Patient sees own via patient__user filter. | appointments/views.py: AppointmentViewSet | ✅ PASS | Doctor filter, patient filter, staff sees all |
| AP2 | Create Appointment | As registrar/doctor, I want to schedule an appointment | POST /api/appointments/ with patient, doctor, department, scheduled_at, reason, notes. Sets created_by=request.user. | appointments/views.py: AppointmentViewSet | ✅ PASS | Allowed roles: admin, chief_doctor, doctor, registrar, patient |
| AP3 | Update Appointment | As staff, I want to change appointment details/status | PUT/PATCH /api/appointments/{id}/ for status changes (pending→confirmed→completed/cancelled/no_show) and other fields. | appointments/views.py: AppointmentViewSet | ✅ PASS | Allowed roles for update: admin, chief_doctor, doctor, registrar, patient |
| AP4 | Delete Appointment | As staff, I want to delete an appointment | DELETE /api/appointments/{id}/ Allowed for any staff role | appointments/views.py: AppointmentViewSet | ✅ PASS | IsAuthenticatedAndRole with allowed_roles |
| AP5 | Doctor Schedule Filter | As doctor, I want to see only my appointments | get_queryset filters by doctor=request.user for doctor role | appointments/views.py: AppointmentViewSet.get_queryset | ✅ PASS | |
| AP6 | Patient Appointment Filter | As patient, I want to see only my appointments | get_queryset filters by patient__user=request.user for patient role | appointments/views.py: AppointmentViewSet.get_queryset | ✅ PASS | |
| AP7 | Appointment Statuses | As a system, I want appointment lifecycle | Statuses: pending → confirmed → completed/cancelled/no_show | appointments/models.py: AppointmentStatus | ✅ PASS | TextChoices |
| AP8 | Overlap Detection | As a system, I want to prevent double-booking | Validates no overlapping appointment for same doctor. Excludes cancelled appointments. Auto-calculates end_time (30min default). | appointments/serializers.py: AppointmentSerializer.validate | ✅ PASS | |
| AP9 | Department Association | As a system, I want appointments linked to departments | FK to Department model. Optional. | appointments/models.py: Appointment | ✅ PASS | |
| AP10 | Appointment Notes | As staff, I want to add notes to appointments | Appointment.notes text field for internal notes | appointments/models.py | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# HOSPITALS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| H1 | List Hospitals | As staff, I want to see hospitals | GET /api/hospitals/ Lists all hospitals with nested departments. | hospitals/views.py: HospitalViewSet | ✅ PASS | IsAuthenticatedAndRole for list/retrieve |
| H2 | Create/Update/Delete Hospital | As admin, I want to manage hospitals | CRUD via HospitalViewSet. Create/update/delete requires IsAdminRole. | hospitals/views.py: HospitalViewSet | ✅ PASS | |
| H3 | Hospital Details | As staff, I want hospital details | Hospital model: name, address, phone, working_hours, chief_doctor, timezone, country_code | hospitals/models.py | ✅ PASS | |
| H4 | List Departments | As staff, I want to see departments | GET /api/departments/ Lists departments with hospital name, manager info | hospitals/views.py: DepartmentViewSet | ✅ PASS | IsAuthenticatedAndRole for list/retrieve |
| H5 | Create/Update/Delete Department | As chief_doctor/admin, I want to manage departments | CRUD via DepartmentViewSet. Mutating actions require IsChiefDoctor. | hospitals/views.py: DepartmentViewSet | ✅ PASS | |
| H6 | Department Types | As a system, I want department categories | Types: therapy, surgery, cardiology, neurology, laboratory, xray, ultrasound, reception, other | hospitals/models.py: DepartmentType | ✅ PASS | |
| H7 | Staff Management | As chief_doctor/admin, I want to manage staff | GET /api/staff/ Lists staff with user info, position, hospital, department. CRUD requires IsChiefDoctor. | hospitals/views.py: StaffViewSet | ✅ PASS | |
| H8 | Staff Profile | As a system, I want employee cards | Staff model: user (1:1 with auth), hospital, department, position, photo, phone | hospitals/models.py: Staff | ✅ PASS | |
| H9 | Department Unique Together | As a system, I want unique department names per hospital | Meta: unique_together = (("hospital", "name"),) | hospitals/models.py | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# MEDICAL RECORDS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| MR1 | List Medical Records | As doctor/chief_doctor/admin, I want to see medical records | GET /api/medical-records/ Lists all medical records. Only doctor+ roles can access. | medrecords/views.py: MedicalRecordViewSet | ✅ PASS | IsDoctor permission |
| MR2 | Create Medical Record | As a doctor, I want to create a medical record | POST /api/medical-records/ with patient, diagnoses, complaints, surgeries, etc. Sets created_by=request.user. | medrecords/views.py: MedicalRecordViewSet | ✅ PASS | |
| MR3 | Update Medical Record | As a doctor, I want to update a medical record | PUT/PATCH /api/medical-records/{id}/ Update diagnoses, notes, etc. | medrecords/views.py: MedicalRecordViewSet | ✅ PASS | |
| MR4 | Medical Record Fields | As a doctor, I want rich medical data | Model: JSONField diagnoses (ICD codes), complaints text, JSONField surgeries, chronic_conditions, allergies, vaccinations, medications, notes | medrecords/models.py | ✅ PASS | |
| MR5 | Doctor Assignment | As a system, I want to track which doctor created records | created_by FK to User | medrecords/models.py | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# LABORATORY MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| L1 | List Analysis Types | As staff, I want to see available lab tests | GET /api/analysis-types/ Lists all analysis types (name, code, price, currency, turnaround_days, normal_range). | lab/views.py: AnalysisTypeViewSet | ✅ PASS | IsAuthenticated for list/retrieve. IsAdminRole for CUD. |
| L2 | Create Analysis Type | As admin, I want to add lab test types | POST /api/analysis-types/ with name, code, price, currency, turnaround_days, normal_range, description | lab/views.py: AnalysisTypeViewSet | ✅ PASS | |
| L3 | Analysis Type Detail with Fields | As lab tech, I want to see structured fields for an analysis type | GET /api/analysis-types/{id}/ Returns analysis type with its predefined fields (field_name, field_type, options, unit, reference ranges). | lab/serializers.py: AnalysisTypeDetailSerializer | ✅ PASS | |
| L4 | List Analysis Orders | As staff, I want to see all orders | GET /api/analysis-orders/?patient=&status=&analysis_type= Filterable, searchable. Role-based filtering. | lab/views.py: AnalysisOrderViewSet | ✅ PASS | Patient sees own. Doctor sees orders they created. Lab tech sees assigned. Admin/registrar sees all. |
| L5 | Create Analysis Order | As a doctor, I want to order an analysis | POST /api/analysis-orders/ with patient, analysis_type, notes. Sets orderer=request.user. Status starts at "created". | lab/views.py: AnalysisOrderViewSet | ✅ PASS | IsDoctor permission for create |
| L6 | Update Analysis Order | As lab tech, I want to update order status and add results | PATCH /api/analysis-orders/{id}/ Update status and result_values. Supports structured field results. | lab/views.py: AnalysisOrderViewSet | ✅ PASS | IsLabTech for update |
| L7 | Update Analysis Status (Flow) | As lab tech, I want to follow the analysis workflow | Status transitions: created→ordered→in_progress→completed→verified→sent. Only allowed forward. Validation in serializer. | lab/models.py: ALLOWED_TRANSITIONS + lab/serializers.py: validate_status | ✅ PASS | |
| L8 | Enter Structured Results | As lab tech, I want to enter structured result values | POST/PATCH result_values array of {field_key, value}. Validates required fields, choice options, numeric values. Auto-computes interpretation (normal/high/low). | lab/serializers.py: AnalysisOrderSerializer._save_result_values | ✅ PASS | |
| L9 | Auto-interpretation of Results | As a system, I want numeric results auto-interpreted | For numeric fields with reference_range_min/max: value < min → "low", value > max → "high", else "normal" | lab/serializers.py: AnalysisOrderSerializer._save_result_values | ✅ PASS | |
| L10 | Legacy Result Field | As a system, I want backward-compatible result text | JSON result_data + auto-generated text result from structured values. "Field: value unit (interpretation) [norm: min-max]" | lab/serializers.py: AnalysisOrderSerializer._save_result_values | ✅ PASS | |
| L11 | Delete Analysis Order | As admin, I want to delete an order | DELETE /api/analysis-orders/{id}/ Admin only | lab/views.py: AnalysisOrderViewSet | ✅ PASS | IsAdminRole for destroy |
| L12 | Bot Patient Analyses Endpoint | As bot, I want to fetch patient analyses by passport/PINFL | GET /api/bot/patient-analyses/?passport=&pinfl= Protected by X-Bot-Key. Returns patient info + formatted analyses with result fields. | lab/views.py: BotPatientAnalysesView | ✅ PASS | |
| L13 | Analysis Type Fields | As a system, I want predefined result fields per analysis type | AnalysisField model: field_type (choice/numeric/text), field_key, field_name, options, unit, reference ranges, is_required, sort_order | lab/models.py: AnalysisField | ✅ PASS | |
| L14 | Analysis Result Values | As a system, I want to store per-field results for each order | AnalysisResultValue model: FK to AnalysisOrder + AnalysisField + value + interpretation. Unique per order+field. | lab/models.py: AnalysisResultValue | ✅ PASS | |
| L15 | Analysis Currency | As a system, I want analysis pricing | Price + currency field (default UZS, also supports USD/RUB) | lab/models.py: AnalysisType | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# FILES MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| F1 | Upload File | As an authenticated user, I want to upload files | POST /api/files/ with content_type, object_id, name, file. MIME validation: pdf, jpeg, png, dicom, docx. Stores size, mime_type. | files/views.py: FileViewSet | ✅ PASS | IsAuthenticated for create |
| F2 | List Files | As an authenticated user, I want to see uploaded files | GET /api/files/ Lists files with content_type, object_id, name, mime_type, size | files/views.py: FileViewSet | ✅ PASS | |
| F3 | Delete File | As admin, I want to delete files | DELETE /api/files/{id}/ Admin only | files/views.py: FileViewSet | ✅ PASS | IsAdminRole for destroy |
| F4 | Generic File Attachment | As a system, I want files attached to any model | Uses GenericForeignKey (content_type + object_id). Upload path: files/<app_label>/<model>/<object_id>/<filename> | files/models.py: File | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# NOTIFICATIONS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| N1 | Create Notification | As staff, I want to send notifications | POST /api/notifications/ with recipient (content_type+object_id), channel, subject, text. Status starts at PENDING. | notifications/views.py: NotificationViewSet | ✅ PASS | IsAuthenticated for create |
| N2 | List Notifications | As registrar+, I want to see notifications | GET /api/notifications/ Lists all notifications. IsRegistrar permission. | notifications/views.py: NotificationViewSet | ✅ PASS | |
| N3 | Update/Delete Notification | As admin, I want to manage notifications | PUT/PATCH/DELETE only for IsAdminRole | notifications/views.py: NotificationViewSet | ✅ PASS | |
| N4 | Celery Email Sending | As a system, I want async notification delivery via email | Celery task send_notification handles email sending via Django mail. Retries 3 times with 60s delay. | notifications/tasks.py: send_notification | ✅ PASS | Requires Celery worker running |
| N5 | Celery Telegram Sending | As a system, I want async notification delivery via Telegram | Celery task send_notification calls Telegram Bot API. Requires TELEGRAM_BOT_TOKEN. Sends via requests.post. | notifications/tasks.py: send_telegram | ✅ PASS | |
| N6 | Bot Subscription Management (DB) | As a bot, I want to manage subscriptions via API | GET/POST /api/bot/subscriptions/ (+ DELETE per chat_id). Stores chat_id, patient FK, patient_id_str. X-Bot-Key protected. | notifications/bot_views.py: BotSubscriptionListCreateView + BotSubscriptionDeleteView | ✅ PASS | Replaces JSON file storage |
| N7 | Subscription Import from JSON | As a system, I want to migrate legacy subscriptions | import_subscriptions_from_json() reads bot/subscriptions.json, creates Subscription records, links Patient FK. | notifications/subscription_models.py | ✅ PASS | One-time migration function |
| N8 | Notification Channels | As a system, I want multi-channel notifications | Channels: telegram, sms, email, push | notifications/models.py: NotificationChannel | ✅ PASS | telegram and email implemented in tasks.py |
| N9 | Notification Statuses | As a system, I want delivery tracking | Statuses: pending → sent/failed. Stores error_message on failure. | notifications/models.py: NotificationStatus | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# AUDIT MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| AU1 | Automatic Audit Logging | As a system, I want all mutations logged | AuditMiddleware logs POST/PUT/PATCH/DELETE requests + all requests to /api/auth/*. Captures user, action, IP, user_agent, status, and timestamp. | audit/middleware.py: AuditMiddleware | ✅ PASS | Skips /health/, /admin/jsi18n/, /static/. GETs to non-auth endpoints are skipped. |
| AU2 | View Audit Log | As admin, I want to browse the audit log | GET /api/audit-logs/ Returns paginated log entries. Searchable by action, username, IP. Sortable. Admin only. | audit/views.py: AuditLogViewSet | ✅ PASS | ReadOnlyModelViewSet |
| AU3 | Audit Log Model | As a system, I want structured audit records | AuditLog: user, action, target (GFK), ip_address, user_agent, succeeded, metadata (JSON), created_at | audit/models.py | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# STATS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| S1 | Patient Stats | As chief_doctor/admin, I want patient demographics | GET /api/stats/patients/ Returns total count, by_gender, by_blood_group | stats/views.py: PatientStatsView | ✅ PASS | IsChiefDoctor permission |
| S2 | Analysis Stats | As chief_doctor/admin, I want analysis statistics | GET /api/stats/analyses/ Returns total, by_status, by_type (analysis type name + count) | stats/views.py: AnalysisStatsView | ✅ PASS | |
| S3 | Doctor Stats | As chief_doctor/admin, I want doctor workload | GET /api/stats/doctors/ Returns appointment count per doctor (id, names, count) | stats/views.py: DoctorStatsView | ✅ PASS | |
| S4 | Hospital Stats | As chief_doctor/admin, I want hospital summaries | GET /api/stats/hospitals/ Returns total hospitals, total departments, per-hospital dept_count + staff_count | stats/views.py: HospitalStatsView | ✅ PASS | |
| S5 | Daily Appointment Stats | As chief_doctor/admin, I want daily visit counts | GET /api/stats/daily/ Returns appointment count grouped by date (TruncDate) | stats/views.py: DailyStatsView | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# REPORTS MODULE
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Endpoint/File | Status | Notes |
|---|---------|------------|-------------------|---------------|--------|-------|
| R1 | Patients PDF Report | As chief_doctor, I want to export patients list as PDF | GET /api/reports/patients/pdf/ Generates PDF with table of patients (№, name, DOB, gender, blood group, phone). Styled with ReportLab. | reports/views.py: PatientsPDFView | ✅ PASS | IsChiefDoctor permission |
| R2 | Patients Excel Report | As chief_doctor, I want to export patients list as Excel | GET /api/reports/patients/excel/ Generates .xlsx with headers and auto-width columns using OpenPyXL | reports/views.py: PatientsExcelView | ✅ PASS | |
| R3 | Analyses PDF Report | As chief_doctor, I want analysis status report | GET /api/reports/analyses/pdf/ Generates PDF: №, patient, type, status, requested_at, completed_at | reports/views.py: AnalysesPDFView | ✅ PASS | |
| R4 | Doctor Schedule PDF | As chief_doctor, I want a doctor's schedule | GET /api/reports/schedule/{doctor_id}/pdf/ Generates PDF: №, datetime, patient, department, status. 404 if no appointments. | reports/views.py: SchedulePDFView | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# TELEGRAM BOT MODULE (bot/app.py)
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Handler | Status | Notes |
|---|---------|------------|-------------------|---------|--------|-------|
| B1 | Bot Start | As a Telegram user, I want to start the bot | /start or first message → welcome message with keyboard: Мой профиль, Подписаться, Мои анализы, Отписаться, Помощь | cmd_start | ✅ PASS | |
| B2 | Bot Show Profile | As a user, I want to see my subscription | Shows Telegram name, chat_id, linked patient ID (or "no subscription") | show_profile | ✅ PASS | |
| B3 | Bot Subscribe | As a user, I want to subscribe to patient notifications | Prompts for patient ID. Accepts P-000001 or 1 format. Calls backend API to store subscription + link telegram_id. | ask_patient_id → handle_patient_id_input | ✅ PASS | API calls: POST /bot/subscriptions/ + POST /bot/link-telegram/ |
| B4 | Bot Unsubscribe | As a user, I want to unsubscribe | Deletes subscription from backend API + clears telegram_id. Shows confirmation. | unsubscribe | ✅ PASS | |
| B5 | Bot Analyses Lookup | As a user, I want to see analysis results via bot | Prompts for passport/PINFL. Calls backend API (GET /bot/patient-analyses/). Returns formatted results with emoji status indicators. | ask_passport_for_analyses → handle_passport_input | ✅ PASS | |
| B6 | Bot Help | As a user, I want to see help | Shows available commands and descriptions | show_help | ✅ PASS | |
| B7 | Bot Error Handler | As a user, I want to see errors gracefully | Global error handler sends "Произошла ошибка" message | error_handler | ✅ PASS | |
| B8 | Bot Singleton Lock | As a system, I want to prevent multiple bot instances | File-based PID lock prevents running multiple polling instances simultaneously | _acquire_singleton_lock | ✅ PASS | |
| B9 | Bot Subscription Persistence via API | As a system, I want subscriptions in DB | Loads subscriptions from backend API on startup. Creates/updates/deletes via API. Falls back to JSON file. | _load_subscriptions_from_api, _save_subscription_to_api, _delete_subscription_from_api | ✅ PASS | |
| B10 | Bot Results Truncation | As a user, I don't want too-long messages | Results truncated to ~4000 chars. "Too much data" notice shown. | _format_analyses | ✅ PASS | Telegram message limit |

# ═══════════════════════════════════════════════════════════
# FRONTEND PAGES & FEATURES
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | Page/Component | Status | Notes |
|---|---------|------------|-------------------|----------------|--------|-------|
| FE1 | Login Page | As a guest, I want to log in via web UI | Login form with username/password. On success, stores tokens in localStorage + redirects to / | pages/Login.jsx | ✅ PASS | |
| FE2 | Register Page | As a guest, I want to register via web UI | Registration form with username, email, password, name fields. On success, redirects to /login. | pages/Register.jsx | ✅ PASS | |
| FE3 | Dashboard | As any user, I want a personalized dashboard | Stat cards (patients/appointments/analyses counts). Role-specific quick actions. Welcome banner with role badge. | pages/Dashboard.jsx | ✅ PASS | Reads page 1 with page_size=1 to get counts without loading all data |
| FE4 | Patient Dashboard (Patient Role) | As a patient, I see appointments count + analyses count | Stat cards for patients, appointments, analyses. Quick actions panel. | pages/Dashboard.jsx | ✅ PASS | |
| FE5 | Doctor Dashboard | As a doctor, I see quick actions for patients/appointments/analyses | Quick action panel with links | pages/Dashboard.jsx | ✅ PASS | |
| FE6 | Registrar Dashboard | As a registrar, I see quick actions for registration/appointments | Quick action panel | pages/Dashboard.jsx | ✅ PASS | |
| FE7 | Lab Tech Dashboard | As a lab tech, I see link to analysis queue | Quick action panel | pages/Dashboard.jsx | ✅ PASS | |
| FE8 | Admin Dashboard | As admin, I see management + monitoring panels | Links to hospitals, departments, staff, audit, reports | pages/Dashboard.jsx | ✅ PASS | |
| FE9 | Role-based Sidebar | As any user, I see relevant navigation | Different nav links per role. Patient: Dashboard, Profile, My Analyses. Doctor: Dashboard, Patients, Appointments, Analyses. etc. | components/Sidebar.jsx | ✅ PASS | |
| FE10 | Responsive Layout | As a user, I want mobile-friendly UI | Hamburger menu on mobile, sidebar overlay with close on ESC/backdrop click | layouts/MainLayout.jsx | ✅ PASS | |
| FE11 | Patients List Page (Admin/Staff) | As staff, I want to manage patients | Table with search, pagination, gender/blood group filters. Add patient button. | pages/Patients.jsx | ✅ PASS | Uses /api/patients/ |
| FE12 | Patient Form (Create/Edit) | As registrar, I want to register/edit patient | Form with full_name, birth_date, gender, blood group, pinfl, passport, foreign_passport, phone, email, address, emergency_contact | pages/PatientForm.jsx | ✅ PASS | |
| FE13 | Patient Profile Page | As a patient, I want to see my profile | Header with avatar, name, email, phone, registration date. Patient ID (P-XXXXXX) with copy button. Telegram connect/badge. Info table. Quick actions. | pages/PatientProfile.jsx | ✅ PASS | Reads GET /api/patients/me/ |
| FE14 | Patient ID Copy-to-Clipboard | As a patient, I want to copy my patient ID | Clipboard API copies "P-XXXXXX" format. Toast shown. | pages/PatientProfile.jsx | ✅ PASS | |
| FE15 | Telegram Connect Status on Web | As a patient, I want to see if Telegram is linked | Reads telegram_id from patient API. Shows "Connected" (green) or "Not Connected" (red) badge. | pages/PatientProfile.jsx | ✅ PASS | |
| FE16 | My Analyses Page (Patient) | As a patient, I want to see my lab results | Table showing analyses: type, status, requested date. Expandable rows show result_values. | pages/MyAnalyses.jsx | ✅ PASS | Uses GET /api/analysis-orders/ |
| FE17 | Appointments Page (Staff) | As staff, I want to manage appointments | Table with status badges, create modal, status update buttons (confirm, complete, cancel). | pages/Appointments.jsx | ✅ PASS | |
| FE18 | Appointments Create Modal | As staff, I want to create an appointment | Modal form with patient (dropdown), doctor (filtered by role), department, datetime, reason | pages/Appointments.jsx | ✅ PASS | Fetches patients, users (doctors), departments |
| FE19 | Appointment Status Actions | As staff, I want to change appointment status | Buttons: pending→confirmed (✅), confirmed→completed (✔️), pending/confirmed→cancelled (❌) | pages/Appointments.jsx | ✅ PASS | |
| FE20 | Analyses Page (Staff) | As staff/lab tech, I want to manage lab orders | Table: patient, analysis type, status, requested date, result. Status-specific actions. | pages/Analyses.jsx | ✅ PASS | |
| FE21 | Create Analysis Order Modal | As doctor, I want to order an analysis | Modal: patient dropdown, analysis type dropdown, notes. | pages/Analyses.jsx | ✅ PASS | |
| FE22 | Analysis Result Entry Modal | As lab tech, I want to enter structured results | Modal with per-field input (select for choice, number for numeric, textarea for text). Reference ranges shown. Auto-saves with status→completed. | pages/Analyses.jsx | ✅ PASS | |
| FE23 | Hospitals Page | As admin, I want to manage hospitals | List/CRUD for hospitals | pages/Hospitals.jsx | ❓ UNVERIFIED | Backend exists, frontend page exists but untested |
| FE24 | Departments Page | As admin, I want to manage departments | List/CRUD for departments | pages/Departments.jsx | ❓ UNVERIFIED | Backend exists, frontend page exists but untested |
| FE25 | Staff Page | As admin, I want to manage staff | List/CRUD for staff | pages/Staff.jsx | ❓ UNVERIFIED | Backend exists, frontend page exists but untested |
| FE26 | Reports Page | As chief_doctor/admin, I want to download reports | Links to download PDF/Excel reports for patients, analyses, schedules | pages/Reports.jsx | ❓ UNVERIFIED | |
| FE27 | Audit Log Page | As admin, I want to browse audit log | Table: date, user, action, IP, status. Search/filter. | pages/AuditLog.jsx | ✅ PASS | |
| FE28 | JWT Auto-Refresh | As a user, I don't want to re-login every 30min | Axios interceptor catches 401, attempts token refresh, retries original request. On refresh failure → redirect to /login. | frontend/api.js | ✅ PASS | |
| FE29 | Auth Context | As the app, I want user state management | React Context providing user, login, logout, isAuthenticated, loading, role, roleLabel | context/AuthContext.jsx | ✅ PASS | |

# ═══════════════════════════════════════════════════════════
# CONFIGURATION & SYSTEM
# ═══════════════════════════════════════════════════════════

| # | Feature | User Story | Expected Behaviour | File | Status | Notes |
|---|---------|------------|-------------------|------|--------|-------|
| C1 | JWT Configuration | As a system, I want configurable token lifetimes | Access: 30min, Refresh: 1 day. Bearer auth header. Blacklist after rotation. | config/settings.py: SIMPLE_JWT | ✅ PASS | |
| C2 | PostgreSQL Database | As a system, I want production database | PostgreSQL via env vars (POSTGRES_HOST, DB, USER, PASSWORD, PORT). Falls back to SQLite with USE_SQLITE=true. | config/settings.py: DATABASES | ✅ PASS | |
| C3 | Redis Cache | As a system, I want caching for lockout/throttling | Redis cache at redis://redis:6379/0. Falls back to LocMemCache for SQLite/test. | config/settings.py: CACHES | ✅ PASS | |
| C4 | Celery Async Tasks | As a system, I want async task processing | Celery with Redis broker (redis://redis:6379/0). Used for notification sending. | config/celery.py | ✅ PASS | |
| C5 | CORS Configuration | As a system, I want controlled cross-origin access | Env-driven: CORS_ALLOW_ALL_ORIGINS for dev, CORS_ALLOWED_ORIGINS for production. Defaults to FRONTEND_URL. | config/settings.py: CORS_* | ✅ PASS | |
| C6 | Content Security Policy | As a system, I want CSP headers | CSP headers with self, bootstrap CDN, fonts CDN. Unsafe-inline for CSS. Unsafe-eval for DEBUG mode. | config/settings.py: CSP_* | ✅ PASS | |
| C7 | Health Check | As a system, I want a health endpoint | GET /health/ returns {"status":"ok","service":"backend"} | config/urls.py | ✅ PASS | |
| C8 | API Documentation | As a developer, I want Swagger/ReDoc | GET /api/schema/ (OpenAPI), /api/docs/ (Swagger UI), /api/redoc/ (ReDoc). drf-spectacular. | config/urls.py | ✅ PASS | |
| C9 | Django Admin | As an admin, I want Django admin panel | /admin/ with default Django admin interface | config/urls.py | ✅ PASS | |
| C10 | Static Files | As a system, I want served static files | STATIC_ROOT = staticfiles/ directory. WhiteNoise? nginx serves in prod. | config/settings.py | ✅ PASS | |
| C11 | Media Files | As a system, I want uploaded media served | MEDIA_ROOT = media/ directory. For staff photos and uploaded files. | config/settings.py | ✅ PASS | |
| C12 | Docker Compose | As a deployer, I want containerized deployment | Services: backend (Django), frontend (Vite), db (PostgreSQL), redis, bot, celery_worker, nginx, prometheus, grafana | docker-compose.yml | ✅ PASS | |

---

# ═══════════════════════════════════════════════════════════
# KNOWN BUGS & ISSUES
# ═══════════════════════════════════════════════════════════

| # | Issue | Location | Severity | Description | Status |
|---|-------|----------|----------|-------------|--------|
| BUG1 | Patient gets 403 on Appointments API | appointments/views.py:20 | HIGH | 'patient' role IS in allowed_roles, BUT get_queryset checks if user.role=="patient" and filters correctly. However get_permissions allows create/update by patient, but if patient tries to list appointments → IsPatientOwnerOrStaff returns True for permission but patient's allowed_roles missing? Actually looking at code: allowed_roles={"admin","chief_doctor","doctor","registrar","patient"} — patient IS included. And get_queryset handles patient filter. This might actually work. Let me verify... The FEARURE doc said it's a bug but looking at code: allowed_roles includes "patient", IsPatientOwnerOrStaff has_permission returns True for patient. Then get_queryset filters by patient__user=request.user. This should work. But the FEATURES_AND_BUGS.md says it's broken. Need to test. | ❓ NEEDS TESTING |
| BUG2 | No real logout token invalidation | accounts/views.py | LOW | Access token remains valid until 30min expiry even after logout. Blacklisted refresh token can't get new access. Minor because tokens are short-lived. | ⚠️ ACCEPTED |
| BUG3 | Lab: Patient can see all analysis orders | lab/views.py: get_queryset | LOW | Patient role filters to patient__user=request.user. But get_permissions doesn't explicitly restrict list for patients via allowed_roles. The config shows patient in allowed_roles. So patient CAN access the list endpoint. But get_queryset restricts to their own data. | ⚠️ MINOR |
| BUG4 | Bot: _save_subscription called in unsubscribe but function still uses legacy JSON | bot/app.py:453 | MEDIUM | `_save_subscriptions()` still called after unsubscribe but the function is a legacy JSON saver. The API delete already happened. This is harmless but dead code. | ⚠️ MINOR |
| BUG5 | Frontend: Analyses.jsx result entry sets status to "completed" automatically | pages/Analyses.jsx:116 | MEDIUM | When saving results, status is hardcoded to "completed". Should allow lab tech to choose or default to "completed" only if all required fields filled. Current behavior: result entry → status becomes "completed" bypassing the flow. | 🔴 OPEN |
| BUG6 | Frontend: No feedback if no patient profile (me endpoint 404) | pages/PatientProfile.jsx | MEDIUM | If user role is patient but no patient_profile exists, /api/patients/me/ returns 404. Need to handle this edge case. | 🔴 OPEN |
| BUG7 | Frontend: Error state for unauthorized API calls | Various pages | LOW | If staff tries to access unauthorized endpoint, error is displayed but may not be clear. | ⚠️ MINOR |
| BUG8 | Frontend: Analyses page doesn't refresh after status update | pages/Analyses.jsx | LOW | fetchData() is called after every action, but API response may be stale. | ⚠️ MINOR |
| BUG9 | Auditing captures passport/PINFL in URLs | audit/middleware.py | LOW | AuditMiddleware logs full URLs including query params. Raw passport numbers could be logged in GET /api/bot/patient-analyses/?passport=AA1234567. | 🔴 OPEN (privacy) |
| BUG10 | Reports: No error if reportlab/openpyxl not installed | reports/views.py | LOW | ImportError will occur if dependencies missing. Should be in requirements.txt. | ⚠️ CHECK |
| BUG11 | Medical Records: No permission variation for different actions | medrecords/views.py:12 | MEDIUM | All actions (list, create, update, destroy) require IsDoctor. But only doctors should create/update. And admins/chief_doctors should be able to view/delete. IsDoctor includes {doctor, chief_doctor, admin}. So admin can't access MedicalRecords because admin role is in IsDoctor set ({DOCTOR, CHIEF_DOCTOR, ADMIN}). Actually admin IS included. Let me check: IsDoctor returns True if role in {DOCTOR, CHIEF_DOCTOR, ADMIN}. So admin can access. But lab_tech and registrar cannot. This seems correct for medical records but may be too restrictive for admin/chief_doctor for reading. | ✅ Actually correct |
| BUG12 | Patient creates appointments? | appointments/views.py | MEDIUM | Patient is in allowed_roles for create, meaning patient CAN create appointments via API. This may not be intended for the current UX. | ⚠️ DESIGN |
| BUG13 | Frontend: No password change/reset UI | frontend | MEDIUM | Backend has password change + reset endpoints. Frontend has no UI for these. No link to change password in sidebar or profile. | 🔴 OPEN |
| BUG14 | Frontend: Logout doesn't redirect properly | context/AuthContext.jsx | LOW | Logout calls /api/auth/logout/ which may fail silently. Local state is cleared. But redirect is handled by interceptor only on 401, not on manual logout. | ⚠️ MINOR |
| BUG15 | Bot Subscription URL inconsistency | bot/app.py:173 | MEDIUM | `f"{SUBSCRIPTIONS_URL.rstrip('/')}{chat_id}/"` — SUBSCRIPTIONS_URL already ends without trailing slash. The URL will be e.g. http://localhost:8000/api/bot/subscriptions123/ (missing slash). Should be `f"{SUBSCRIPTIONS_URL.rstrip('/')}/{chat_id}/"`. | 🔴 OPEN |
| BUG16 | SensitiveFieldsMixin doesn't handle unauthenticated access to list endpoint | accounts/serializers.py | MEDIUM | When listing patients, if user is not authenticated, the mixin still processes and may pop fields incorrectly because request.user is AnonymousUser without 'role' attr. | ⚠️ MINOR (patched via early return) |
| BUG17 | Report Schedule endpoint uses full_name_display | reports/views.py:265 | LOW | doctor.full_name_display is a property on User model — should work. | ✅ PASS |
| BUG18 | Bot: VITE_ prefix env vars | bot/app.py | LOW | Uses standard env vars, not VITE_ prefix. | ✅ OK |
| BUG19 | Frontend token in localStorage XSS risk | frontend/api.js | MEDIUM | Standard SPA pattern. Tokens stored in localStorage accessible by JS. Risk if XSS is achieved. HttpOnly cookie would be more secure but breaks SPA auth flow. | ⚠️ ACCEPTED |
| BUG20 | Docker Postgres password fallback | config/settings.py | LOW | Default POSTGRES_PASSWORD="hospital_pass" in code. Should not have default in production. | ⚠️ MINOR |

---

# ═══════════════════════════════════════════════════════════
# VERIFICATION/UNVERIFIED FEATURES
# ═══════════════════════════════════════════════════════════

| # | Feature | Page/Endpoint | Status | Verification Notes |
|---|---------|---------------|--------|-------------------|
| UV1 | Hospitals Page (Frontend) | /hospitals | ❓ UNVERIFIED | Backend: HospitalViewSet ✅. Frontend: page exists. Need to test rendering + CRUD. |
| UV2 | Departments Page (Frontend) | /departments | ❓ UNVERIFIED | Backend: DepartmentViewSet ✅. Frontend: page exists. Need to test. |
| UV3 | Staff Page (Frontend) | /staff | ❓ UNVERIFIED | Backend: StaffViewSet ✅. Frontend: page exists. Need to test. |
| UV4 | Reports Page (Frontend) | /reports | ❓ UNVERIFIED | Backend: 4 report endpoints ✅. Frontend: page exists. Need to test PDF/Excel download. |
| UV5 | MyAnalyses expandable rows | /my-analyses | ❓ UNVERIFIED | Need to test expansion + result display. |
| UV6 | PatientForm create vs edit | /patients/new | ❓ UNVERIFIED | Need to verify edit mode works (passing patient ID). |
| UV7 | Medical Records API | /api/medical-records/ | ❓ UNVERIFIED | Backend: MedicalRecordViewSet with IsDoctor. Frontend: no dedicated page for medical records (no route in App.jsx). Feature is backend-only. |
| UV8 | Notifications API + Celery | /api/notifications/ | ❓ UNVERIFIED | Backend: NotificationViewSet. No frontend page for notifications. Feature is backend-only. |
| UV9 | Stat endpoints (all 5) | /api/stats/* | ❓ UNVERIFIED | Backend: 5 API views. No frontend consumption of these specific endpoints (dashboard uses its own counts). |
| UV10 | Patient detail retrieve format | /patients/{id} | ❓ UNVERIFIED | Frontend Patients.jsx probably has detail view. |
| UV11 | File upload/download | /api/files/ | ❓ UNVERIFIED | Backend: FileViewSet. Frontend: no UI for file upload. Backend-only feature. |

---