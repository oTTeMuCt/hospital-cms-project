# Stage 1 Architecture and Database Design

## Цель
Результат этапа 1 — проектирование основной архитектуры системы, построение схемы данных и подготовка к реализации backend-модулей.

## Сущности и связи

- `accounts.User` — единый пользователь системы с ролями: Admin, ChiefDoctor, Doctor, LabTech, Registrar, Patient.
- `hospitals.Hospital` — больница с адресом, телефоном, режимом работы, главным врачом.
- `hospitals.Department` — отделение больницы, которое принадлежит конкретной больнице и может иметь менеджера.
- `patients.Patient` — профиль пациента, связанный с пользователем или существующий отдельно.
- `medrecords.MedicalRecord` — медицинская запись пациента с диагнозами, аллергиями, вакцинациями и заметками.
- `appointments.Appointment` — запись на приём, связана с пациентом, врачом и отделением.
- `lab.AnalysisType` — определённый вид анализа с ценой, сроком и нормой.
- `lab.AnalysisOrder` — назначенный анализ, заказанный врачом для пациента, со статусом и результатом.
- `files.File` — универсальный файл для привязки к любой сущности через GenericForeignKey.
- `notifications.Notification` — уведомление, отправляемое пациенту или сотруднику через Telegram/SMS/Email.
- `audit.AuditLog` — журнал действий пользователей, привязанный к целевым объектам.

## Основные связи

- `Hospital` 1:N `Department`
- `User` 1:N `Hospital` (chief_doctor)
- `User` 1:N `Department` (manager)
- `Patient` 1:1 `User`
- `Patient` 1:N `MedicalRecord`
- `Patient` 1:N `Appointment`
- `Patient` 1:N `AnalysisOrder`
- `AnalysisOrder` N:1 `AnalysisType`
- `Appointment` N:1 `Department`
- `File`, `Notification`, `AuditLog` используют GenericForeignKey для связи с любой сущностью.

## Планируемые API-модули

### Accounts
- `POST /api/accounts/login/`
- `POST /api/accounts/token/`
- `POST /api/accounts/register/`
- `GET /api/accounts/me/`
- `GET /api/accounts/users/`

### Hospitals
- `GET /api/hospitals/`
- `POST /api/hospitals/`
- `GET /api/hospitals/{id}/`
- `PATCH /api/hospitals/{id}/`
- `DELETE /api/hospitals/{id}/`
- `GET /api/departments/`
- `POST /api/departments/`

### Patients
- `GET /api/patients/`
- `POST /api/patients/`
- `GET /api/patients/{id}/`
- `PATCH /api/patients/{id}/`

### Medical records
- `GET /api/medical-records/`
- `POST /api/medical-records/`
- `GET /api/medical-records/{id}/`
- `PATCH /api/medical-records/{id}/`

### Appointments
- `GET /api/appointments/`
- `POST /api/appointments/`
- `GET /api/appointments/{id}/`
- `PATCH /api/appointments/{id}/`

### Laboratory
- `GET /api/analysis-types/`
- `POST /api/analysis-types/`
- `GET /api/analysis-orders/`
- `POST /api/analysis-orders/`
- `PATCH /api/analysis-orders/{id}/`

### Files
- `POST /api/files/`
- `GET /api/files/`

### Notifications
- `GET /api/notifications/`
- `POST /api/notifications/`

### Audit
- `GET /api/audit-logs/`

## Реализация

В проекте добавлены Django-приложения для ключевых доменов:
- `accounts`
- `hospitals`
- `patients`
- `medrecords`
- `appointments`
- `lab`
- `files`
- `notifications`
- `audit`
- `stats`

Добавлены модели, зарегистрированы админские интерфейсы и созданы миграции. Проект успешно проходит Django system checks.
