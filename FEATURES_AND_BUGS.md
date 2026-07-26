# Hospital CMS — Feature Inventory & Bug Tracker

## Spreadsheet Format: Feature | User Story | Expected Behaviour | Status | Notes

---

# ── 1. AUTHENTICATION ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 1.1 | User Login | As a user, I want to log in with username and password | POST /api/auth/token/ returns JWT tokens. Token stored in localStorage. Redirect to dashboard. | ✅ PASS | Works. JWT access + refresh pattern |
| 1.2 | Token Refresh | As a user, I want my session to stay active | axios interceptor calls POST /api/auth/token/refresh/ automatically on 401 | ✅ PASS | Auto-refresh works |
| 1.3 | Token Verify | As a system, I want to verify JWT validity | POST /api/auth/token/verify/ endpoint exists | ✅ PASS | Endpoint exists |
| 1.4 | User Registration | As a guest, I want to register | POST /api/auth/register/ creates user. Default role=patient. Returns user data. | ✅ PASS | Registration works |
| 1.5 | Get Current User | As a user, I want to see my profile | GET /api/auth/me/ returns user info (id, username, email, name, role) | ✅ PASS | Works |
| 1.6 | Logout | As a user, I want to log out | Clears localStorage tokens. No backend session. Redirect to /login. | ⚠️ ISSUE | No server-side token blacklist. Only client-side cleanup. JWT remains valid until expiry. |
| 1.7 | Password Validation | As a system, I want strong passwords | Uses Django's default validators: min length 8, common password check, numeric check, attribute similarity check | ✅ PASS | At least 4 validators active |

# ── 2. ROLE-BASED ACCESS CONTROL (RBAC) ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 2.1 | Role Assignment | As an admin, I want users to have roles | User model has `role` field with choices: admin, chief_doctor, doctor, lab_tech, registrar, patient | ✅ PASS | Defined in UserRole TextChoices |
| 2.2 | Admin Permissions | As admin, I want full access | IsAdminRole → only UserRole.ADMIN. Can list all users, destroy patients, access audit logs | ✅ PASS | Check |
| 2.3 | Doctor Permissions | As doctor, I want to see patients and create appointments | IsDoctor → role in {doctor, chief_doctor, admin}. View patients, schedule appointments, order analyses | ✅ PASS | Check |
| 2.4 | Lab Tech Permissions | As lab tech, I want to process analyses | IsLabTech → role in {lab_tech, chief_doctor, admin}. View analysis queue, enter results | ✅ PASS | Check |
| 2.5 | Registrar Permissions | As registrar, I want to register patients and appointments | IsRegistrar → role in {registrar, chief_doctor, admin}. Create patients, schedule appointments | ✅ PASS | Check |
| 2.6 | Patient Permissions | As patient, I want to see only my data | IsPatientOwnerOrStaff → patient sees only own records via queryset filter | ✅ PASS | get_queryset filters by user=request.user for patient role |
| 2.7 | Patient API Self-Service | As patient, I can only access my endpoint | PatientViewSet.get_queryset filters for patient role. "me" action returns own profile. | ✅ PASS | Implemented |
| 2.8 | Patient Nav Restrictions | As patient, I see only patient nav | Sidebar shows different links per role. Patient sees: Dashboard, Profile, My Analyses. | ✅ PASS | Role-based navigation |

# ── 3. PATIENTS ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 3.1 | List Patients | As staff, I want to see all patients | GET /api/patients/?search=&gender=&blood_group= Paginated, searchable, filterable | ✅ PASS | PatientViewSet |
| 3.2 | Create Patient | As registrar/doctor, I want to register a patient | POST /api/patients/ with full_name, birth_date, gender, pinfl, passport, phone, email, etc. | ✅ PASS | SensitiveFieldsMixin hides pinfl from non-authorized roles |
| 3.3 | View Patient Details | As staff/patient, I want to see patient info | GET /api/patients/{id}/ Returns all patient data based on role permissions | ✅ PASS | PatientViewSet.retrieve |
| 3.4 | Update Patient | As staff/patient-owner, I want to update patient data | PUT/PATCH /api/patients/{id}/ Partial updates supported | ✅ PASS | PatientViewSet.update/partial_update |
| 3.5 | Delete Patient | As admin only, I want to delete a patient | DELETE /api/patients/{id}/ Only admin can destroy | ✅ PASS | IsAdminRole for destroy |
| 3.6 | Patient Profile (Website) | As patient, I want to see my profile dashboard | /profile page with header, patient ID (P-XXXXXX), Telegram status, quick actions | ✅ PASS | PatientProfile.jsx |
| 3.7 | Copy Patient ID | As patient, I want to copy my ID | Clipboard API copies "P-XXXXXX". Toast notification shown. | ✅ PASS | Implemented |
| 3.8 | Patient Form (Staff) | As registrar, I want to create/edit patient from web UI | /patients/new page with form fields | ✅ PASS | PatientForm page |

# ── 4. HOSPITALS ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 4.1 | List Hospitals | As admin, I want to see hospitals | CRUD for hospital entities | ❓ UNVERIFIED | Need to check hospitals pages |
| 4.2 | Departments | As admin, I want to see departments | Related to hospitals | ❓ UNVERIFIED | Need to check Departments pages |

# ── 5. APPOINTMENTS ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 5.1 | List Appointments | As staff, I want to see all appointments | GET /api/appointments/ Filtered by patient, doctor, department, status | ✅ PASS | AppointmentViewSet |
| 5.2 | Create Appointment | As registrar/doctor, I want to schedule an appointment | POST /api/appointments/ with patient, doctor, department, scheduled_at, reason | ✅ PASS | Check |
| 5.3 | Update Appointment | As staff, I want to change appointment status | PATCH /api/appointments/{id/ for status changes (confirmed, cancelled, completed) | ✅ PASS | Check |
| 5.4 | Doctor's Schedule | As doctor, I want to see my appointments | Filter appointments by doctor | ✅ PASS | filterset_fields includes doctor |
| 5.5 | Patient Appointments (Web) | As patient, I want to see my appointments | Via Appointments page (role-filtered) | ❓ UNVERIFIED | Frontend Appointments page exists |
| 5.6 | Patient Appointment Restriction | As patient, I can't access all appointments | AppointmentViewSet has no patient-specific queryset filter → Forbidden for patients | ⚠️ ISSUE | Patient gets 403 on /api/appointments/ even for own appointments |

# ── 6. LABORATORY ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 6.1 | Analysis Types | As admin, I want to manage analysis types | GET /api/analysis-types/ Lists available lab tests | ✅ PASS | AnalysisTypeViewSet |
| 6.2 | Create Analysis Order | As doctor, I want to order an analysis | POST /api/analysis-orders/ Creates analysis order for a patient | ✅ PASS | AnalysisOrderViewSet |
| 6.3 | List Analysis Orders | As staff, I want to see all orders | GET /api/analysis-orders/ Filterable, searchable | ✅ PASS | Check |
| 6.4 | Update Analysis Status | As lab tech, I want to update order status | PATCH /api/analysis-orders/{id}/ Update status (in_progress, completed, verified) and add results | ✅ PASS | Check |
| 6.5 | Patient My Analyses | As patient, I want to see my analysis results | /my-analyses page. Calls GET /api/analysis-orders/ which filters by patient__user=request.user | ✅ PASS | MyAnalyses.jsx works |
| 6.6 | Analysis Results | As lab tech, I want to enter structured results | Result values with fields, interpretations, reference ranges | ✅ PASS | AnalysisResult model |

# ── 7. TELEGRAM BOT ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 7.1 | Bot /start | As user, I want to start the bot | Reply with welcome message and keyboard | ✅ PASS | cmd_start handler |
| 7.2 | Bot Subscribe | As user, I want to subscribe to notifications | Accepts P-000001 or numeric ID. Calls backend API to store telegram_id. | ✅ PASS | Handle with _link_telegram() + _parse_patient_id() |
| 7.3 | Bot Unsubscribe | As user, I want to unsubscribe | Removes from local subscriptions. Clears telegram_id on backend. | ✅ PASS | unsubscribe handler |
| 7.4 | Bot Analyses Lookup | As user, I want to see my analyses via bot | Enter passport/PINFL. Bot calls backend API. Returns formatted results. | ✅ PASS | handle_passport_input + _fetch_analyses |
| 7.5 | Bot My Profile | As user, I want to see my Telegram subscription status | Shows linked patient ID or "no subscription" | ✅ PASS | show_profile handler |
| 7.6 | Bot Help | As user, I want to see help | Shows available commands and descriptions | ✅ PASS | show_help handler |
| 7.7 | Backend Bot Auth | As system, I want secure bot API access | BotPatientAnalysesView + BotLinkTelegramView require X-Bot-Key header | ✅ PASS | BOT_API_KEY validation |
| 7.8 | Telegram Link Status on Web | As patient, I want to see if Telegram is connected | PatientProfile reads patient.telegram_id → shows "Connected"/"Not Connected" badge | ✅ PASS | Works after bot calls link-telegram endpoint |

# ── 8. AUDIT ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 8.1 | Audit Logging | As admin, I want to see activity log | AuditMiddleware logs requests. GET /api/audit/ lists logged actions. | ✅ PASS | AuditMiddleware + ViewSet |
| 8.2 | Audit Log Web UI | As admin, I want to browse audit log | /audit page with table | ✅ PASS | AuditLog page |

# ── 9. REPORTS ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 9.1 | Reports | As chief_doctor/admin, I want to see reports | Reports generation and viewing | ❓ UNVERIFIED | Reports page exists |
| 9.2 | Stats | As admin, I want statistics | Stats API endpoint | ✅ PASS | stats app exists |

# ── 10. NOTIFICATIONS ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 10.1 | Notifications Model | As system, I want to store notifications | Notification model with recipient, type, content, read status | ✅ PASS | notifications app |
| 10.2 | Celery Tasks | As system, I want async notification delivery | Celery worker configured for async tasks | ✅ PASS | celery_worker in docker-compose |

# ── 11. FRONTEND UI/UX ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 11.1 | Dashboard | As user, I want a dashboard with stats | Stat cards (patients, appointments, analyses counts). Role-specific quick actions. | ✅ PASS | Dashboard.jsx |
| 11.2 | Responsive Layout | As user, I want the site to work on mobile | Hamburger menu, sidebar slides in/out. Responsive grid. | ✅ PASS | Full responsive implementation |
| 11.3 | Patient Profile Page | As patient, I want my profile | /profile page with header, P-XXXXXX ID, Telegram connection, quick actions | ✅ PASS | PatientProfile.jsx |
| 11.4 | My Analyses Page | As patient, I want my lab results | /my-analyses page. Table with expandable results. | ✅ PASS | MyAnalyses.jsx |
| 11.5 | Admin Patient List | As admin, I want to manage patients | /patients page with table, search, pagination | ✅ PASS | Patients.jsx |
| 11.6 | Appointment Management | As staff, I want to manage appointments | /appointments page. List, create, edit, status changes. | ✅ PASS | Appointments.jsx |
| 11.7 | Analysis Management (Staff) | As staff, I want to manage lab orders | /analyses page. Create orders, update status, enter results. | ✅ PASS | Analyses.jsx |
| 11.8 | Login Page | As guest, I want to log in | /login page with username/password form | ✅ PASS | Login.jsx |
| 11.9 | Register Page | As guest, I want to register | /register page | ✅ PASS | Register.jsx |

# ── 12. PATIENT PORTAL (NEW) ──

| # | Feature | User Story | Expected Behaviour | Status | Notes |
|---|---------|------------|-------------------|--------|-------|
| 12.1 | Patient Profile Header | As patient, I see my info | Gradient card with avatar, name, email, phone, registration date | ✅ PASS | Implemented |
| 12.2 | Patient ID Display | As patient, I see P-XXXXXX | Formatted patient ID in large font, centered | ✅ PASS | formatPatientId() |
| 12.3 | Copy Patient ID | As patient, I can copy my ID | Clipboard API. Toast notification. | ✅ PASS | Works |
| 12.4 | Open Telegram Bot | As patient, I can open Telegram | Button linking to https://t.me/HospitalCMSbot | ✅ PASS | Implemented |
| 12.5 | Telegram Connect Status | As patient, I see if Telegram is linked | Green badge "Connected" if telegram_id exists, Red "Not Connected" otherwise | ✅ PASS | Reads from API |
| 12.6 | Telegram Instructions | As patient, I see how to connect | Step-by-step instructions with Telegram link and pre-filled Patient ID | ✅ PASS | Implemented |
| 12.7 | Patient Info Table | As patient, I see my details | ID, birth date, gender, phone, email, registration date | ✅ PASS | Only shows fields that exist |
| 12.8 | Quick Actions | As patient, I see future features | 5 disabled buttons with "Coming Soon" badges | ✅ PASS | No empty pages created |

# ── 13. KNOWN BUGS & ISSUES ──

| # | Issue | File | Severity | Description | Status |
|---|-------|------|----------|-------------|--------|
| B1 | Patient gets 403 on appointments | appointments/views.py | MEDIUM | Patient role not in allowed_roles for AppointmentViewSet. Patients can't view own appointments via API. | 🔴 OPEN |
| B2 | No logout token invalidation | accounts/views.py | LOW | JWT tokens remain valid until expiry. No blacklist. | 🔴 OPEN |
| B3 | No rate limiting on login | accounts/views.py | MEDIUM | No brute-force protection on /api/auth/token/ | 🔴 OPEN |
| B4 | No password reset endpoint | accounts/urls.py | MEDIUM | No password reset flow implemented | 🔴 OPEN |
| B5 | No password change endpoint | accounts/views.py | MEDIUM | Users cannot change passwords via API | 🔴 OPEN |
| B6 | DB credentials in settings.py | config/settings.py | LOW | Database config reads from env vars but has fallback defaults | ⚠️ MINOR |
| B7 | SECRET_KEY fallback in code | config/settings.py | HIGH | SECRET_KEY fallback to "dev-secret-key" in production | ✅ FIXED in .env |
| B8 | CORS_ALLOW_ALL_ORIGINS | config/settings.py | MEDIUM | In production this should be restricted | ⚠️ CONFIG |
| B9 | No HSTS headers | config/settings.py | LOW | SECURE_HSTS_SECONDS not configured | 🔴 OPEN |
| B10 | No Content Security Policy | config/settings.py | LOW | CSP headers not configured | 🔴 OPEN |
| B11 | Patient can access all analysis orders | lab/views.py | LOW | AnalysisOrderViewSet has no patient-specific filtering in get_permissions. Relies on backend queryset filtering. | ⚠️ MINOR |
| B12 | Bot conflict errors | bot/app.py | LOW | Multiple bot instances cause 409 Conflict errors | ⚠️ DOCUMENTED |
| B13 | Subscription file persistence | bot/app.py | LOW | subscriptions.json local file — not distributed | ⚠️ DOCUMENTED |
| B14 | No account lockout | accounts/views.py | MEDIUM | No lockout after failed login attempts | 🔴 OPEN |

# ── 14. SECURITY FINDINGS ──

| # | Finding | Location | Severity | Description |
|---|---------|----------|----------|-------------|
| S1 | Weak JWT secret key | config/settings.py | MEDIUM | JWT uses same SECRET_KEY which defaults to "dev-secret-key" if not set in env |
| S2 | SQLite fallback for production | config/settings.py | LOW | USE_SQLITE env var allows switching to SQLite — dangerous in production |
| S3 | No sensitive data masking in logs | lab/views.py | LOW | Patient IDs logged (acceptable), but passport numbers logged in search params |
| S4 | Frontend stores tokens in localStorage | frontend/src/api.js | MEDIUM | XSS vulnerability — if XSS is achieved, tokens are stolen |
| S5 | No CSRF for DRF API | config/settings.py | LOW | DRF uses JWTAuthentication which is immune to CSRF when using Bearer tokens. Safe. |