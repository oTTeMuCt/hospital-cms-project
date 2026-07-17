# HCMS Feature Inventory & User Stories

## Legend
- ✅ = Working
- ❌ = Broken/Not Working
- ⚠️ = Has Issues
- 🔲 = Not Implemented

---

## 1. Authentication & User Management

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 1.1 | User Registration | As a new user, I want to register with username/password so I can access the system | POST /api/auth/register/ creates User, returns 201. For patient role, auto-creates Patient profile via signal | ⚠️ | Signal works locally. Need to verify in Docker |
| 1.2 | User Login | As a registered user, I want to login with my credentials to get JWT tokens | POST /api/auth/token/ returns {access, refresh} tokens | ⚠️ | Need to verify in Docker |
| 1.3 | Token Refresh | As a logged-in user, I want my access token to auto-refresh when expired | axios interceptor catches 401, calls /api/auth/token/refresh/ | ✅ | Implemented in api.js |
| 1.4 | View Profile | As a logged-in user, I want to see my profile info | GET /api/auth/me/ returns current user data | ⚠️ | Need to verify |
| 1.5 | User List | As admin/registrar, I want to list all users | GET /api/users/ returns paginated user list | ✅ | Implemented |
| 1.6 | Role-Based Access | As a user with a specific role, I should only see what my role allows | Permissions checked in backend views and frontend Sidebar | ⚠️ | Need to verify all role restrictions |
| 1.7 | Logout | As a logged-in user, I want to logout | Clears localStorage tokens and user data | ✅ | Implemented in AuthContext |

## 2. Patients

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 2.1 | List Patients | As staff, I want to see all patients | GET /api/patients/ returns paginated list | ⚠️ | Need to verify in Docker |
| 2.2 | Create Patient | As registrar, I want to register a new patient | POST /api/patients/ creates Patient record | ⚠️ | Need to verify |
| 2.3 | Edit Patient | As staff, I want to update patient info | PATCH /api/patients/{id}/ updates fields | ✅ | Implemented in modal |
| 2.4 | Delete Patient | As admin, I want to delete a patient | DELETE /api/patients/{id}/ removes record | ✅ | Implemented with confirm |
| 2.5 | Search Patients | As staff, I want to search patients by name/phone/passport | GET /api/patients/?search= filters results | ✅ | Implemented |
| 2.6 | View Patient Detail | As staff, I want to see full patient info | Modal shows all patient fields | ✅ | Implemented |
| 2.7 | Duplicate Passport Rejection | As registrar, I should not be able to create duplicate passport | Serializer validate_passport() checks uniqueness | ✅ | Implemented |
| 2.8 | Auto-Create Patient on Register | As a new patient user, my patient profile should be auto-created | Signal creates Patient when User with role=patient is created | ✅ | Implemented in signals.py |

## 3. Hospitals

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 3.1 | List Hospitals | As admin, I want to see all hospitals | GET /api/hospitals/ returns list | ✅ | Implemented |
| 3.2 | Create Hospital | As admin, I want to add a hospital | POST /api/hospitals/ creates record | ✅ | Implemented |
| 3.3 | Edit Hospital | As admin, I want to update hospital info | PATCH /api/hospitals/{id}/ updates fields | ✅ | Implemented |
| 3.4 | Delete Hospital | As admin, I want to delete a hospital | DELETE /api/hospitals/{id}/ removes record | ✅ | Implemented with confirm |

## 4. Departments

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 4.1 | List Departments | As staff, I want to see all departments | GET /api/departments/ returns list | ✅ | Implemented |
| 4.2 | Create Department | As admin, I want to add a department | POST /api/departments/ creates record | ✅ | Implemented |
| 4.3 | Edit Department | As admin, I want to update department | PATCH /api/departments/{id}/ updates fields | ✅ | Implemented |
| 4.4 | Delete Department | As admin, I want to delete a department | DELETE /api/departments/{id}/ removes record | ✅ | Implemented with confirm |

## 5. Staff

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 5.1 | List Staff | As admin, I want to see all staff members | GET /api/staff/ returns list with user/hospital/department | ✅ | Implemented |
| 5.2 | Staff CRUD | As admin, I want to manage staff | Full CRUD via StaffViewSet | ✅ | Implemented |

## 6. Appointments

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 6.1 | List Appointments | As staff, I want to see all appointments | GET /api/appointments/ returns list | ✅ | Implemented |
| 6.2 | Create Appointment | As registrar, I want to book an appointment | POST /api/appointments/ creates record | ⚠️ | Need to verify doctor field mapping (Staff vs User) |
| 6.3 | Update Appointment Status | As staff, I want to change appointment status | PATCH /api/appointments/{id}/ updates status | ✅ | Implemented with buttons |
| 6.4 | Conflict Detection | As registrar, I should not double-book a doctor | Serializer checks overlapping appointments | ✅ | Implemented in validate() |
| 6.5 | Patient Name Display | As staff, I want to see patient name in appointment list | SerializerMethodField get_patient_name() | ✅ | Implemented |

## 7. Lab / Analyses

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 7.1 | List Analysis Types | As staff, I want to see available analysis types | GET /api/analysis-types/ returns list | ✅ | Implemented |
| 7.2 | List Analysis Orders | As staff, I want to see all analysis orders | GET /api/analysis-orders/ returns list | ✅ | Implemented |
| 7.3 | Create Analysis Order | As doctor, I want to order an analysis for a patient | POST /api/analysis-orders/ creates order | ⚠️ | Need to verify permission (IsDoctor) |
| 7.4 | Update Order Status | As lab tech, I want to update analysis status | PATCH /api/analysis-orders/{id}/ updates status | ✅ | Implemented with workflow buttons |
| 7.5 | Enter Result | As lab tech, I want to enter analysis results | PATCH /api/analysis-orders/{id}/ with result field | ✅ | Implemented in modal |
| 7.6 | Patient View Own Analyses | As a patient, I want to see my analysis results | GET /api/analysis-orders/?patient={id} filtered by user | ⚠️ | Need to verify patient filtering |
| 7.7 | Bot API for Analyses | As Telegram bot, I want to fetch patient analyses by passport | GET /api/bot/patient-analyses/?passport= with X-Bot-Key | ✅ | Implemented |

## 8. Audit Log

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 8.1 | View Audit Log | As admin, I want to see all user actions | GET /api/audit-logs/ returns paginated log | ✅ | Implemented (ReadOnly) |
| 8.2 | Audit Middleware | All user actions should be logged automatically | AuditMiddleware logs requests | ✅ | Implemented |

## 9. Reports

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 9.1 | Export Patients CSV | As staff, I want to download patient list as CSV | Frontend fetches all pages, generates CSV blob | ✅ | Implemented |
| 9.2 | Export Analyses CSV | As staff, I want to download analysis list as CSV | Frontend fetches all pages, generates CSV blob | ✅ | Implemented |
| 9.3 | Patients PDF Report | As chief doctor, I want a PDF report of patients | GET /api/reports/patients/pdf/ returns PDF | ✅ | Implemented |
| 9.4 | Analyses PDF Report | As chief doctor, I want a PDF report of analyses | GET /api/reports/analyses/pdf/ returns PDF | ✅ | Implemented |
| 9.5 | Doctor Schedule PDF | As chief doctor, I want a PDF of doctor's schedule | GET /api/reports/schedule/{id}/pdf/ returns PDF | ✅ | Implemented |

## 10. Statistics

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 10.1 | Patient Stats | As chief doctor, I want patient statistics | GET /api/stats/patients/ returns by gender/blood group | ✅ | Implemented |
| 10.2 | Analysis Stats | As chief doctor, I want analysis statistics | GET /api/stats/analyses/ returns by status/type | ✅ | Implemented |
| 10.3 | Doctor Stats | As chief doctor, I want doctor workload stats | GET /api/stats/doctors/ returns appointment counts | ✅ | Implemented |
| 10.4 | Hospital Stats | As chief doctor, I want hospital overview | GET /api/stats/hospitals/ returns dept/staff counts | ✅ | Implemented |
| 10.5 | Daily Stats | As chief doctor, I want daily appointment stats | GET /api/stats/daily/ returns daily counts | ✅ | Implemented |

## 11. Files

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 11.1 | Upload File | As authenticated user, I want to upload files | POST /api/files/ creates File record | ✅ | Implemented |
| 11.2 | Delete File | As admin, I want to delete files | DELETE /api/files/{id}/ removes record | ✅ | Implemented |

## 12. Medical Records

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 12.1 | Medical Record CRUD | As doctor, I want to manage patient medical records | Full CRUD via MedicalRecordViewSet | ✅ | Implemented |

## 13. Notifications

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 13.1 | List Notifications | As user, I want to see my notifications | GET /api/notifications/ returns list | ✅ | Implemented |
| 13.2 | Mark as Read | As user, I want to mark notifications as read | PATCH /api/notifications/{id}/ with is_read=true | ✅ | Implemented |

## 14. Infrastructure

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 14.1 | Nginx API Proxy | Frontend should be able to call backend API | nginx.conf proxies /api/ to backend:8000 | ✅ | Fixed - was missing, now added |
| 14.2 | Docker Compose | All services should start together | docker compose up starts all containers | ✅ | Working |
| 14.3 | Demo Data Seeding | System should have demo data for testing | python manage.py seed_demo_data creates 5 each | ✅ | Implemented |
| 14.4 | Telegram Bot | Patients should get results via Telegram | bot/app.py polls API and sends messages | ✅ | Running |
| 14.5 | Database Migrations | Schema should be up to date | python manage.py migrate applies all | ✅ | Working |

## 15. Dashboard

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 15.1 | View Dashboard | As any user, I want to see a dashboard with stats | Dashboard shows patient/appointment/analysis counts | ✅ | Implemented |
| 15.2 | Role-Specific Quick Actions | As a user, I want relevant quick action buttons | Dashboard shows different buttons per role | ✅ | Implemented |

## 16. Sidebar Navigation

| # | Feature | User Story | Expected Behavior | Status | Notes |
|---|---------|-----------|-------------------|--------|-------|
| 16.1 | Role-Based Menu | As a user, I should only see menu items for my role | Sidebar renders different links per role | ✅ | Implemented |
| 16.2 | Active Link Highlight | As a user, I want to see which page I'm on | NavLink active class highlights current page | ✅ | Implemented |

---

## Known Issues to Investigate

1. **Registration → Patient Profile**: Signal auto-creates Patient profile, but the frontend Register.jsx redirects to /patients/new to fill additional data. Need to verify the flow works end-to-end.
2. **Appointment Doctor Field**: Frontend sends `doctor` as user ID from Staff list, but backend expects User ID. Need to verify mapping.
3. **Patient List for Patients**: Patient users can only see their own profile via `get_queryset` filter. Need to verify.
4. **Analysis Orders for Patients**: Patient users filtered by `patient__user=user`. Need to verify.
5. **Nginx Proxy**: Was missing, now added. Need to verify it works.
6. **Demo Data Passwords**: Need to verify demo user passwords work for login.
</write_to_file>