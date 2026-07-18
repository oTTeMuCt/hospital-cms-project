# HCMS Feature Inventory & User Stories — COMPREHENSIVE SPREADSHEET

## Legend
- ✅ = Working
- ❌ = Broken/Not Working
- ⚠️ = Has Issues / Needs Verification
- 🔲 = Not Implemented

---

## 1. Authentication & User Management

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 1.1 | User Registration | As a new user, I want to register with username/password so I can access the system | POST /api/auth/register/ creates User, returns 201. For patient role, auto-creates Patient profile via signal | ⚠️ | Signal works locally. Need to verify in Docker. Frontend Register.jsx redirects to /patients/new after registration for patients | accounts/views.py: RegisterView, accounts/serializers.py: UserCreateSerializer, accounts/signals.py | Register.jsx |
| 1.2 | User Login | As a registered user, I want to login with my credentials to get JWT tokens | POST /api/auth/token/ returns {access, refresh} tokens | ⚠️ | Need to verify in Docker. Frontend stores tokens in localStorage | accounts/views.py: AuthTokenObtainPairView | Login.jsx, AuthContext.jsx |
| 1.3 | Token Refresh | As a logged-in user, I want my access token to auto-refresh when expired | axios interceptor catches 401, calls /api/auth/token/refresh/ | ✅ | Implemented in api.js interceptor | accounts/views.py: AuthTokenRefreshView | api.js |
| 1.4 | Token Verify | As a user, I want to verify my token is valid | POST /api/auth/token/verify/ | ✅ | Endpoint exists | accounts/urls.py: TokenVerifyView | Not used in frontend |
| 1.5 | View Profile (Me) | As a logged-in user, I want to see my profile info | GET /api/auth/me/ returns current user data | ✅ | Used in AuthContext.login() after successful token obtain | accounts/views.py: MeView | AuthContext.jsx |
| 1.6 | User List | As admin/registrar/doctor, I want to list all users | GET /api/users/ returns paginated user list | ✅ | Permission: admin/registrar/doctor/chief_doctor can view. Used in Hospitals.jsx, Departments.jsx for doctor dropdowns | accounts/views.py: UserListView | Hospitals.jsx, Departments.jsx, PatientForm.jsx |
| 1.7 | User Detail | As admin, I want to view a specific user | GET /api/users/{id}/ returns user detail | ✅ | Admin only | accounts/views.py: UserDetailView | Not used in frontend |
| 1.8 | Role-Based Access Control | As a user with a specific role, I should only see what my role allows | Permissions checked in backend views and frontend Sidebar | ⚠️ | Need to verify all role restrictions. Backend uses IsAuthenticatedAndRole, IsAdminRole, IsChiefDoctor, IsDoctor, IsLabTech, IsRegistrar, IsPatientOwnerOrStaff | accounts/permissions.py | Sidebar.jsx, Dashboard.jsx |
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
| 3.1 | List Hospitals | As staff, I want to see all hospitals | GET /api/hospitals/ returns list with departments | ✅ | Permission: IsAuthenticatedAndRole (admin/chief_doctor/doctor/lab_tech/registrar) | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.2 | Create Hospital | As admin, I want to add a hospital | POST /api/hospitals/ creates record | ✅ | Admin only for create/update/delete | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.3 | Edit Hospital | As admin, I want to update hospital info | PATCH /api/hospitals/{id}/ updates fields | ✅ | Admin only. Modal with all fields | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.4 | Delete Hospital | As admin, I want to delete a hospital | DELETE /api/hospitals/{id}/ removes record | ✅ | Admin only. Confirm dialog | hospitals/views.py: HospitalViewSet | Hospitals.jsx |
| 3.5 | Hospital Detail with Departments | As staff, I want to see hospital departments | HospitalSerializer includes departments (DepartmentListSerializer) | ✅ | Nested serializer | hospitals/serializers.py: HospitalSerializer | Hospitals.jsx |
| 3.6 | Chief Doctor Assignment | As admin, I want to assign a chief doctor to a hospital | Hospital model has chief_doctor FK to User. Frontend fetches doctors for dropdown | ✅ | Frontend filters users by doctor/chief_doctor role | hospitals/models.py | Hospitals.jsx |
| 3.7 | Sensitive Fields Protection | As non-admin, I should not see timezone/country_code | SensitiveFieldsMixin removes timezone/country_code for non-admin/chief_doctor | ✅ | Implemented in HospitalSerializer | accounts/serializers.py | — |

## 4. Departments

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 4.1 | List Departments | As staff, I want to see all departments | GET /api/departments/ returns list with hospital info | ✅ | Permission: IsAuthenticatedAndRole | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.2 | Create Department | As admin/chief_doctor, I want to add a department | POST /api/departments/ creates record | ✅ | Permission: IsChiefDoctor for create/update/delete | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.3 | Edit Department | As admin/chief_doctor, I want to update department | PATCH /api/departments/{id}/ updates fields | ✅ | Modal with hospital, name, type, manager, description | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.4 | Delete Department | As admin/chief_doctor, I want to delete a department | DELETE /api/departments/{id}/ removes record | ✅ | Confirm dialog | hospitals/views.py: DepartmentViewSet | Departments.jsx |
| 4.5 | Department Type Selection | As admin, I want to choose department type from predefined list | Frontend shows dropdown with all DepartmentType choices | ✅ | Types: therapy, surgery, cardiology, neurology, laboratory, xray, ultrasound, reception, other | hospitals/models.py: DepartmentType | Departments.jsx |
| 4.6 | Manager Assignment | As admin, I want to assign a department manager | Department model has manager FK to User. Frontend fetches all users for dropdown | ✅ | — | hospitals/models.py | Departments.jsx |
| 4.7 | Unique Department per Hospital | System should prevent duplicate department names in same hospital | unique_together = (("hospital", "name"),) | ✅ | DB-level constraint | hospitals/models.py | — |

## 5. Staff

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 5.1 | List Staff | As staff, I want to see all staff members | GET /api/staff/ returns list with user/hospital/department | ✅ | Permission: IsAuthenticatedAndRole. Shows user_full_name, role, position, hospital, department, phone | hospitals/views.py: StaffViewSet | Staff.jsx |
| 5.2 | Create Staff | As admin/chief_doctor, I want to add a staff member | POST /api/staff/ creates record | ✅ | Permission: IsChiefDoctor | hospitals/views.py: StaffViewSet | Not implemented in frontend |
| 5.3 | Edit Staff | As admin/chief_doctor, I want to update staff | PATCH /api/staff/{id}/ updates fields | ✅ | Permission: IsChiefDoctor | hospitals/views.py: StaffViewSet | Not implemented in frontend |
| 5.4 | Delete Staff | As admin/chief_doctor, I want to delete a staff member | DELETE /api/staff/{id}/ removes record | ✅ | Permission: IsChiefDoctor | hospitals/views.py: StaffViewSet | Not implemented in frontend |
| 5.5 | Staff Photo | As admin, I want to upload staff photo | Staff model has photo ImageField | ✅ | Not used in frontend Staff.jsx | hospitals/models.py | — |

## 6. Appointments

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 6.1 | List Appointments | As staff, I want to see all appointments | GET /api/appointments/ returns list with patient/doctor/department | ✅ | Permission: IsAuthenticatedAndRole (admin/chief_doctor/doctor/registrar) | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 6.2 | Create Appointment | As registrar/doctor, I want to book an appointment | POST /api/appointments/ creates record | ⚠️ | **BUG: Doctor field mapping issue.** Frontend sends `doctor` as Staff.user ID (from /staff/ endpoint), but backend expects User ID. The staff endpoint returns `user` field which is the User ID, so it should work if frontend uses `d.user` correctly. Need to verify. | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 6.3 | Update Appointment Status | As staff, I want to change appointment status | PATCH /api/appointments/{id}/ updates status | ✅ | Buttons: pending→confirmed, confirmed→completed, pending/confirmed→cancelled | appointments/views.py: AppointmentViewSet | Appointments.jsx |
| 6.4 | Conflict Detection | As registrar, I should not double-book a doctor | Serializer checks overlapping appointments excluding cancelled | ✅ | Implemented in AppointmentSerializer.validate() | appointments/serializers.py | — |
| 6.5 | Patient Name Display | As staff, I want to see patient name in appointment list | SerializerMethodField get_patient_name() | ✅ | — | appointments/serializers.py | Appointments.jsx |
| 6.6 | Doctor Name Display | As staff, I want to see doctor name in appointment list | SerializerMethodField get_doctor_name() | ✅ | — | appointments/serializers.py | Appointments.jsx |
| 6.7 | Filter Appointments | As staff, I want to filter by patient/doctor/department/status | GET /api/appointments/?status=pending&doctor=1 | ✅ | DjangoFilterBackend | appointments/views.py | Not used in frontend |
| 6.8 | Search Appointments | As staff, I want to search by patient name/reason/doctor | GET /api/appointments/?search=text | ✅ | Search fields: patient__full_name, reason, doctor__last_name | appointments/views.py | Not used in frontend |
| 6.9 | Status Badges | As staff, I want to see colored status badges | Frontend maps status to badge classes (warning/success/info/danger) | ✅ | STATUS_LABELS in Appointments.jsx | — | Appointments.jsx |

## 7. Lab / Analyses

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 7.1 | List Analysis Types | As staff, I want to see available analysis types | GET /api/analysis-types/ returns list | ✅ | Permission: IsAuthenticated for list/retrieve, IsAdminRole for create/update/delete | lab/views.py: AnalysisTypeViewSet | Analyses.jsx |
| 7.2 | Create Analysis Type | As admin, I want to add a new analysis type | POST /api/analysis-types/ creates record | ✅ | Admin only | lab/views.py: AnalysisTypeViewSet | Not implemented in frontend |
| 7.3 | List Analysis Orders | As staff, I want to see all analysis orders | GET /api/analysis-orders/ returns list with patient/type/status | ✅ | Permission: IsAuthenticatedAndRole. Patients see only their own | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 7.4 | Create Analysis Order | As doctor, I want to order an analysis for a patient | POST /api/analysis-orders/ creates order with orderer=request.user | ✅ | Permission: IsDoctor. Frontend shows patient/analysis_type/notes form | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 7.5 | Update Order Status | As lab tech, I want to update analysis status | PATCH /api/analysis-orders/{id}/ updates status | ✅ | Permission: IsLabTech for update. Status transitions validated by ALLOWED_TRANSITIONS | lab/views.py: AnalysisOrderViewSet, lab/serializers.py | Analyses.jsx |
| 7.6 | Enter Result | As lab tech, I want to enter analysis results | PATCH /api/analysis-orders/{id}/ with result field + status=completed | ✅ | Modal with result textarea and notes | lab/views.py: AnalysisOrderViewSet | Analyses.jsx |
| 7.7 | Status Workflow | As lab tech, I want to follow the analysis workflow | created→ordered→in_progress→completed→verified→sent | ✅ | ALLOWED_TRANSITIONS dict enforces valid transitions. Frontend shows appropriate buttons per status | lab/models.py | Analyses.jsx |
| 7.8 | Patient View Own Analyses | As a patient, I want to see my analysis results | GET /api/analysis-orders/?patient={id} filtered by patient__user=user | ⚠️ | **BUG: MyAnalyses.jsx fetches /patients/ first, then uses first patient's ID. If patient has no patient profile, this fails.** Also, the patient filter in backend get_queryset uses patient__user=user, which should work. | lab/views.py: AnalysisOrderViewSet | MyAnalyses.jsx |
| 7.9 | Bot API for Analyses | As Telegram bot, I want to fetch patient analyses by passport | GET /api/bot/patient-analyses/?passport= with X-Bot-Key header | ✅ | Public endpoint protected by X-Bot-Key header. Returns patient info + analyses list | lab/views.py: BotPatientAnalysesView | — |
| 7.10 | Bot API by PINFL | As Telegram bot, I want to fetch patient analyses by PINFL | GET /api/bot/patient-analyses/?pinfl= with X-Bot-Key header | ✅ | Supports both passport and pinfl parameters | lab/views.py: BotPatientAnalysesView | — |
| 7.11 | Analysis Type Price/Currency | As staff, I want to see analysis pricing | AnalysisType model has price and currency fields | ✅ | Default currency: UZS | lab/models.py | Not used in frontend |
| 7.12 | Status Transition Validation | As lab tech, I should not be able to skip statuses | Serializer validate_status() checks ALLOWED_TRANSITIONS | ✅ | Prevents invalid transitions like created→completed | lab/serializers.py | — |

## 8. Audit Log

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 8.1 | View Audit Log | As admin, I want to see all user actions | GET /api/audit-logs/ returns paginated log (ReadOnly) | ✅ | Admin only. Shows user, action, IP, user_agent, success status, timestamp | audit/views.py: AuditLogViewSet | AuditLog.jsx |
| 8.2 | Audit Middleware | All user actions should be logged automatically | AuditMiddleware logs POST/PUT/PATCH/DELETE + auth GET requests | ✅ | Skips /health/, /admin/jsi18n/, /static/. Logs user, action, IP, user_agent, status_code | audit/middleware.py | — |
| 8.3 | Search Audit Log | As admin, I want to search audit logs | GET /api/audit-logs/?search=text | ✅ | Search fields: action, user__username, ip_address | audit/views.py | Not used in frontend |
| 8.4 | Audit Log Ordering | As admin, I want to sort audit logs | GET /api/audit-logs/?ordering=created_at | ✅ | Default ordering: -created_at | audit/views.py | Not used in frontend |

## 9. Reports

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 9.1 | Export Patients CSV | As staff, I want to download patient list as CSV | Frontend fetches all pages (handles pagination), generates CSV blob with BOM for Excel | ✅ | Implemented in Reports.jsx with fetchAllPages() helper | — | Reports.jsx |
| 9.2 | Export Analyses CSV | As staff, I want to download analysis list as CSV | Frontend fetches all pages, generates CSV blob with BOM for Excel | ✅ | Implemented in Reports.jsx | — | Reports.jsx |
| 9.3 | Patients PDF Report | As chief doctor, I want a PDF report of patients | GET /api/reports/patients/pdf/ returns PDF with table | ✅ | Permission: IsChiefDoctor. Uses reportlab. Styled table with header/footer | reports/views.py: PatientsPDFView | Not used in frontend |
| 9.4 | Patients Excel Report | As chief doctor, I want an Excel report of patients | GET /api/reports/patients/excel/ returns XLSX | ✅ | Permission: IsChiefDoctor. Uses openpyxl. Auto-width columns | reports/views.py: PatientsExcelView | Not used in frontend |
| 9.5 | Analyses PDF Report | As chief doctor, I want a PDF report of analyses | GET /api/reports/analyses/pdf/ returns PDF | ✅ | Permission: IsChiefDoctor. Uses reportlab | reports/views.py: AnalysesPDFView | Not used in frontend |
| 9.6 | Doctor Schedule PDF | As chief doctor, I want a PDF of doctor's schedule | GET /api/reports/schedule/{doctor_id}/pdf/ returns PDF | ✅ | Permission: IsChiefDoctor. Shows appointments for specific doctor | reports/views.py: SchedulePDFView | Not used in frontend |

## 10. Statistics

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 10.1 | Patient Stats | As chief doctor, I want patient statistics | GET /api/stats/patients/ returns total, by_gender, by_blood_group | ✅ | Permission: IsChiefDoctor | stats/views.py: PatientStatsView | Not used in frontend |
| 10.2 | Analysis Stats | As chief doctor, I want analysis statistics | GET /api/stats/analyses/ returns total, by_status, by_type | ✅ | Permission: IsChiefDoctor | stats/views.py: AnalysisStatsView | Not used in frontend |
| 10.3 | Doctor Stats | As chief doctor, I want doctor workload stats | GET /api/stats/doctors/ returns appointment counts per doctor | ✅ | Permission: IsChiefDoctor | stats/views.py: DoctorStatsView | Not used in frontend |
| 10.4 | Hospital Stats | As chief doctor, I want hospital overview | GET /api/stats/hospitals/ returns dept/staff counts per hospital | ✅ | Permission: IsChiefDoctor | stats/views.py: HospitalStatsView | Not used in frontend |
| 10.5 | Daily Stats | As chief doctor, I want daily appointment stats | GET /api/stats/daily/ returns daily appointment counts | ✅ | Permission: IsChiefDoctor | stats/views.py: DailyStatsView | Not used in frontend |

## 11. Files

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 11.1 | Upload File | As authenticated user, I want to upload files | POST /api/files/ creates File record with GenericForeignKey | ✅ | Permission: IsAuthenticated for list/retrieve/create. MIME type validation (PDF, JPEG, PNG, DICOM, DOCX) | files/views.py: FileViewSet, files/serializers.py | Not implemented in frontend |
| 11.2 | List Files | As authenticated user, I want to see files | GET /api/files/ returns list | ✅ | Permission: IsAuthenticated | files/views.py | Not implemented in frontend |
| 11.3 | Delete File | As admin, I want to delete files | DELETE /api/files/{id}/ removes record | ✅ | Admin only | files/views.py | Not implemented in frontend |
| 11.4 | MIME Type Validation | System should reject unsupported file types | Serializer validate_file() checks against ALLOWED_MIME_TYPES | ✅ | Allowed: PDF, JPEG, PNG, DICOM, DOCX | files/serializers.py | — |

## 12. Medical Records

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 12.1 | List Medical Records | As doctor, I want to see patient medical records | GET /api/medical-records/ returns list | ✅ | Permission: IsDoctor | medrecords/views.py: MedicalRecordViewSet | Not implemented in frontend |
| 12.2 | Create Medical Record | As doctor, I want to create a medical record | POST /api/medical-records/ creates record | ✅ | Permission: IsDoctor | medrecords/views.py | Not implemented in frontend |
| 12.3 | Edit Medical Record | As doctor, I want to update a medical record | PATCH /api/medical-records/{id}/ updates fields | ✅ | Permission: IsDoctor | medrecords/views.py | Not implemented in frontend |
| 12.4 | Delete Medical Record | As doctor, I want to delete a medical record | DELETE /api/medical-records/{id}/ removes record | ✅ | Permission: IsDoctor | medrecords/views.py | Not implemented in frontend |
| 12.5 | JSON Diagnoses/Surgeries | As doctor, I want to store structured diagnoses and surgeries | JSONField for diagnoses and surgeries with example format | ✅ | diagnoses: [{"code": "I10", "name": "...", "date": "..."}] | medrecords/models.py | Not implemented in frontend |

## 13. Notifications

| # | Feature | User Story | Expected Behavior | Status | Notes | Backend File | Frontend File |
|---|---------|-----------|-------------------|--------|-------|-------------|---------------|
| 13.1 | List Notifications | As user, I want to see notifications | GET /api/notifications/ returns list | ✅ | Permission: IsRegistrar for list/retrieve | notifications/views.py: NotificationViewSet | Not implemented in frontend |
| 13.2 | Create Notification | As authenticated user, I want to send a notification | POST /api/notifications/ creates record | ✅ | Permission: IsAuthenticated for create | notifications/views.py | Not implemented in frontend |
| 13.3 | Delete Notification | As admin, I want to delete notifications | DELETE /api/notifications/{id}/ removes record | ✅ | Admin only | notifications/views.py | Not implemented in frontend |
| 13.4 | Celery Task for Sending | Notifications should be sent asynchronously | send_notification Celery task handles telegram/email channels | ✅ | Task with max_retries=3, retry_delay=60s. Handles telegram (via Bot API) and email (via Django SMTP) | notifications/tasks.py | — |
| 13.5 | Telegram Sending | As system, I want to send Telegram notifications | send_telegram() uses TELEGRAM_BOT_TOKEN, looks for telegram_id on recipient | ✅ | Checks multiple attr names: telegram_id, telegram_chat_id, chat_id | notifications/tasks.py | — |
| 13.6 | Email Sending | As system, I want to send email notifications | send_email_notification() uses Django send_mail | ✅ | Uses DEFAULT_FROM_EMAIL setting | notifications/tasks.py | — |

## 14. Telegram Bot

| # | Feature | User Story | Expected Behavior | Status | Notes | File |
|---|---------|-----------|-------------------|--------|-------|------|
| 14.1 | Bot Start | As a Telegram user, I want to start the bot | /start command shows welcome message with keyboard | ✅ | ReplyKeyboardMarkup with menu buttons | bot/app.py |
| 14.2 | View Profile | As a Telegram user, I want to see my subscription status | Shows chat ID, patient ID if subscribed | ✅ | — | bot/app.py |
| 14.3 | Subscribe to Patient | As a Telegram user, I want to subscribe to a patient's notifications | Asks for patient ID, stores in subscriptions.json | ✅ | Thread-safe with Lock. Persists to JSON file | bot/app.py |
| 14.4 | Unsubscribe | As a Telegram user, I want to unsubscribe | Removes chat_id from subscriptions | ✅ | — | bot/app.py |
| 14.5 | View Analyses | As a Telegram user, I want to see my analysis results by passport/PINFL | Asks for passport/PINFL, calls backend API, formats results | ✅ | Handles errors, timeouts, connection errors. Formats with emoji. Truncates at 4000 chars for Telegram limit | bot/app.py |
| 14.6 | Help | As a Telegram user, I want to see help | Shows command descriptions | ✅ | — | bot/app.py |
| 14.7 | Error Handling | Bot should handle errors gracefully | Error handler sends user-friendly message | ✅ | Logs errors, notifies user | bot/app.py |
| 14.8 | Bot Runner | Bot should load .env and start | run_bot.py loads .env, sets API_BASE_URL for local dev, starts bot | ✅ | — | bot/run_bot.py |

## 15. Dashboard

| # | Feature | User Story | Expected Behavior | Status | Notes | Frontend File |
|---|---------|-----------|-------------------|--------|-------|---------------|
| 15.1 | View Dashboard | As any user, I want to see a dashboard with stats | Dashboard shows patient/appointment/analysis counts from API | ✅ | Uses Promise.allSettled to fetch counts. Shows "—" on failure | Dashboard.jsx |
| 15.2 | Role-Specific Welcome | As a user, I want to see a role-specific welcome message | ROLE_WELCOME map shows different text per role | ✅ | — | Dashboard.jsx |
| 15.3 | Role Badge | As a user, I want to see my role displayed | Badge with role label and email | ✅ | — | Dashboard.jsx |
| 15.4 | Quick Actions for Doctor | As a doctor, I want quick action buttons | Links to patients, appointments, analyses | ✅ | — | Dashboard.jsx |
| 15.5 | Quick Actions for Registrar | As a registrar, I want quick action buttons | Links to new patient, appointments, patient search | ✅ | — | Dashboard.jsx |
| 15.6 | Quick Actions for Lab Tech | As a lab tech, I want quick action buttons | Link to analyses queue | ✅ | — | Dashboard.jsx |
| 15.7 | Quick Actions for Admin | As an admin, I want management and monitoring links | Links to hospitals, departments, staff, audit, reports | ✅ | — | Dashboard.jsx |

## 16. Sidebar Navigation

| # | Feature | User Story | Expected Behavior | Status | Notes | Frontend File |
|---|---------|-----------|-------------------|--------|-------|---------------|
| 16.1 | Role-Based Menu | As a user, I should only see menu items for my role | Sidebar renders different links per role | ✅ | 6 role-specific menu configurations | Sidebar.jsx |
| 16.2 | Active Link Highlight | As a user, I want to see which page I'm on | NavLink active class highlights current page | ✅ | Uses isActive from NavLink | Sidebar.jsx |
| 16.3 | User Info in Sidebar | As a user, I want to see my name and role in sidebar | Shows user name and role label in sidebar footer | ✅ | — | Sidebar.jsx |
| 16.4 | Logout Button | As a user, I want to logout from sidebar | Logout button in sidebar footer | ✅ | — | Sidebar.jsx |
| 16.5 | Responsive Sidebar | Sidebar should adapt to screen size | Tablet: collapsed (64px). Mobile: hidden (0px) | ✅ | CSS media queries | index.css |

## 17. Infrastructure

| # | Feature | User Story | Expected Behavior | Status | Notes | File |
|---|---------|-----------|-------------------|--------|-------|------|
| 17.1 | Nginx API Proxy | Frontend should be able to call backend API | nginx.conf proxies /api/ to backend:8000 | ✅ | Added to nginx.conf | frontend/nginx.conf |
| 17.2 | Docker Compose | All services should start together | docker compose up starts all containers | ✅ | Services: backend, frontend, nginx, postgres, redis, bot | docker-compose.yml |
| 17.3 | Demo Data Seeding | System should have demo data for testing | python manage.py seed_demo_data creates 5 departments, 5 doctors, 5 patients, 5 lab tests | ✅ | With --force flag to reset | seed_demo_data.py |
| 17.4 | Database Migrations | Schema should be up to date | python manage.py migrate applies all | ✅ | 2 patient migrations (initial + passport unique constraint) | migrations/ |
| 17.5 | Health Check | System should have a health endpoint | GET /health/ returns {"status": "ok", "service": "backend"} | ✅ | — | config/urls.py |
| 17.6 | API Documentation | Developers should have API docs | Swagger UI at /api/docs/, Redoc at /api/redoc/, Schema at /api/schema/ | ✅ | drf-spectacular configured | config/urls.py |
| 17.7 | CORS Configuration | Frontend should be able to call backend from different origin | CORS_ALLOW_ALL_ORIGINS or CORS_ALLOWED_ORIGINS | ✅ | Configurable via env vars | config/settings.py |
| 17.8 | SQLite Fallback | System should work without PostgreSQL for local dev | USE_SQLITE env var switches to SQLite | ✅ | — | config/settings.py |
| 17.9 | Celery Configuration | Async tasks should be supported | Celery with Redis broker | ✅ | Configured in config/celery.py and settings.py | config/celery.py |

## 18. Frontend Routing & Layout

| # | Feature | User Story | Expected Behavior | Status | Notes | Frontend File |
|---|---------|-----------|-------------------|--------|-------|---------------|
| 18.1 | Login Route | As a user, I want to access the login page | /login renders Login component | ✅ | Redirects to / if already authenticated | App.jsx |
| 18.2 | Register Route | As a new user, I want to access the registration page | /register renders Register component | ✅ | — | App.jsx |
| 18.3 | Protected Routes | As a user, I should be redirected to login if not authenticated | MainLayout checks isAuthenticated, redirects to /login | ✅ | Shows loading spinner while checking auth | MainLayout.jsx |
| 18.4 | All Routes | All page routes should be accessible | /, /hospitals, /departments, /staff, /patients, /patients/new, /appointments, /analyses, /audit, /reports, /my-analyses | ✅ | 11 routes defined | App.jsx |
| 18.5 | Catch-All Redirect | Unknown routes should redirect to dashboard | * route redirects to / | ✅ | — | App.jsx |
| 18.6 | Axios Instance | API calls should have consistent base URL and auth headers | api.js creates axios instance with /api base, Bearer token interceptor | ✅ | — | api.js |
| 18.7 | Token Refresh Interceptor | Expired tokens should auto-refresh | 401 response triggers refresh token flow | ✅ | If refresh fails, redirects to /login | api.js |

## 19. Known Issues & Bugs

| # | Issue | Severity | Description | File(s) |
|---|-------|----------|-------------|---------|
| 19.1 | Appointment Doctor Field Mapping | ⚠️ Medium | Frontend Appointments.jsx fetches /staff/ and uses `d.user` as doctor value. The staff endpoint returns `user` (User ID). This should work if the User ID is correct, but the doctor field in Appointment model is a FK to User. Need to verify the mapping works end-to-end. | Appointments.jsx line 121, appointments/models.py |
| 19.2 | MyAnalyses First Patient Assumption | ⚠️ Medium | MyAnalyses.jsx fetches /patients/ and uses `patients[0].id` as the patient ID. If a patient user has no patient profile (e.g., just registered but didn't fill patient form), this will fail or return wrong data. | MyAnalyses.jsx lines 23-27 |
| 19.3 | PatientForm User Lookup | ⚠️ Low | PatientForm.jsx fetches all users to find the newly registered user by username. This could be slow with many users. Also, if the user was just created by signal, the patient profile already exists, so creating another one would fail. | PatientForm.jsx lines 54-63 |
| 19.4 | Staff Page No CRUD | ⚠️ Low | Staff.jsx only lists staff members. No create/edit/delete functionality in frontend, though backend supports it. | Staff.jsx |
| 19.5 | Medical Records No Frontend | ⚠️ Low | MedicalRecordViewSet is fully implemented in backend but has no frontend pages. | — |
| 19.6 | Files No Frontend | ⚠️ Low | FileViewSet is fully implemented in backend but has no frontend pages. | — |
| 19.7 | Notifications No Frontend | ⚠️ Low | NotificationViewSet is fully implemented in backend but has no frontend pages. | — |
| 19.8 | Stats No Frontend | ⚠️ Low | All 5 stats endpoints are implemented but have no frontend pages. | — |
| 19.9 | Reports Backend Endpoints Not Used | ⚠️ Low | Backend has PDF/Excel report endpoints but frontend Reports.jsx uses client-side CSV generation instead. | Reports.jsx, reports/views.py |
| 19.10 | Patient Edit Modal Missing PINFL/Passport | ✅ Fixed | Patient edit modal (Patients.jsx) now includes PINFL and passport fields. | Patients.jsx editForm |
| 19.11 | Analysis Order Delete Not in Frontend | ⚠️ Low | Backend supports DELETE on analysis orders (admin only) but frontend has no delete button. | Analyses.jsx |
| 19.12 | Appointment Delete Not in Frontend | ⚠️ Low | Backend supports DELETE on appointments but frontend has no delete button. | Appointments.jsx |
| 19.13 | Demo Data Passwords Hardcoded | ⚠️ Low | Passwords "doctor123" and "patient123" are hardcoded in seed_demo_data.py | seed_demo_data.py |
| 19.14 | No Loading State on Appointment Create | ⚠️ Low | Appointments.jsx handleCreate doesn't disable button during save (saving state exists but not used to disable) | Appointments.jsx |
| 19.15 | Dashboard Stats Uses List Endpoints | ⚠️ Medium | Dashboard fetches full list endpoints (/patients/, /appointments/, /analysis-orders/) just to get counts. This is inefficient with large datasets. Should use dedicated stats endpoints. | Dashboard.jsx |
| 19.16 | AuditMiddleware Logs All Requests | ⚠️ Low | AuditMiddleware logs every POST/PUT/PATCH/DELETE + auth GET. This could generate a lot of log entries. | audit/middleware.py |
| 19.17 | No Pagination Controls in Frontend | ⚠️ Medium | All list pages use default pagination (50 per page) but have no pagination controls (next/prev page buttons). | All list pages |
| 19.18 | SensitiveFieldsMixin Context Bug | ⚠️ Medium | SensitiveFieldsMixin.__init__ checks `hasattr(self, "context")` but context is always set by DRF. The check `if not model_name: return` may silently skip protection if model has no __name__. | accounts/serializers.py |
| 19.19 | PatientViewSet select_for_update on List | ✅ Fixed | Fixed: select_for_update() now only applied on create/update/partial_update/destroy actions, not on list. | patients/views.py |
| 19.20 | Register Page Shows Admin Role Hint | ⚠️ Low | Register page shows hint "Admin/Chief Doctor roles are assigned by admin" but the role dropdown doesn't include those options anyway. | Register.jsx line 143 |