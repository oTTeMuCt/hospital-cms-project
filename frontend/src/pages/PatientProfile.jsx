import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";

export default function PatientProfile() {
  const { user } = useAuth();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toastVisible, setToastVisible] = useState(false);

  useEffect(() => {
    const fetchPatient = async () => {
      if (!user || user.role !== "patient") {
        setLoading(false);
        return;
      }
      try {
        const res = await api.get("/patients/me/");
        setPatient(res.data);
      } catch (err) {
        if (err.response?.status === 404) {
          setError(
            "Профиль пациента не привязан к вашей учётной записи. " +
            "Пожалуйста, обратитесь к администратору клиники или в регистратуру."
          );
        } else {
          setError("Не удалось загрузить профиль пациента. Пожалуйста, попробуйте позже.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchPatient();
  }, [user]);

  const TELEGRAM_BOT_LINK = "https://t.me/HospitalCMSbot";

  const formatPatientId = (id) => `P-${String(id).padStart(6, "0")}`;

  const copyPatientId = async () => {
    if (!patient) return;
    try {
      await navigator.clipboard.writeText(formatPatientId(patient.id));
      setToastVisible(true);
      setTimeout(() => setToastVisible(false), 2500);
    } catch {
      // Clipboard API not available
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        Загрузка...
      </div>
    );
  }

  return (
    <div className="patient-profile">
      <div className="page-header">
        <h1>Профиль пациента</h1>
        <p>Ваш персональный медицинский кабинет</p>
      </div>

      <div className="page-content">
        {/* Toast notification */}
        {toastVisible && (
          <div className="toast-notification">
            <span>✔</span> ID пациента скопирован
          </div>
        )}

        {error && (
          <div className="alert alert-warning">
            <div className="alert-icon">⚠</div>
            <div>
              <strong>Профиль не найден</strong>
              <p style={{ marginTop: 4, fontWeight: 400 }}>{error}</p>
            </div>
          </div>
        )}

        {!error && patient && (
          <>
            {/* Profile Header Card */}
            <div className="profile-header-card">
              <div className="profile-avatar">
                <div className="avatar-placeholder">
                  {user?.first_name?.[0] || user?.username?.[0] || "?"}
                </div>
              </div>
              <div className="profile-info">
                <h2 className="profile-name">
                  {user?.last_name} {user?.first_name} {user?.middle_name || ""}
                </h2>
                <p className="profile-email">{user?.email || patient.email}</p>
                {patient.phone && <p className="profile-phone">{patient.phone}</p>}
                <p className="profile-date">
                  Registered: {new Date(patient.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </p>
              </div>
            </div>

            {/* Patient ID Card */}
            <div className="patient-id-card">
              <div className="patient-id-label">ID пациента</div>
              <div className="patient-id-value">{formatPatientId(patient.id)}</div>
              <p className="patient-id-hint">
                Используйте этот ID для подключения к Telegram-боту.
              </p>
              <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                <button className="btn btn-primary btn-copy" onClick={copyPatientId}>
                  📋 Copy Patient ID
                </button>
                <a
                  href={TELEGRAM_BOT_LINK}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-outline btn-copy"
                  style={{ textDecoration: "none" }}
                >
                  💬 Open Telegram Bot
                </a>
              </div>
            </div>

            {/* Two column layout */}
            <div className="profile-grid-2">
              {/* Telegram Connection Card */}
                <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Подключение Telegram</h3>
                  {patient.telegram_id ? (
                    <span className="badge badge-success">Подключено</span>
                  ) : (
                    <span className="badge badge-danger">Не подключено</span>
                  )}
                </div>
                <div className="card-body">
                  <p className="text-muted" style={{ marginBottom: 16 }}>
                    Для получения уведомлений:
                  </p>
                  <ol className="telegram-steps">
                    <li>Откройте <a href={TELEGRAM_BOT_LINK} target="_blank" rel="noopener noreferrer">Telegram-бота</a>.</li>
                    <li>Отправьте: <code>/start</code></li>
                    <li>Затем отправьте: <code>/connect</code></li>
                    <li>Введите ID пациента: <strong>{formatPatientId(patient.id)}</strong></li>
                  </ol>
                  <p className="text-muted" style={{ marginTop: 16, fontSize: 13 }}>
                    После подключения вы будете получать уведомления о:
                  </p>
                  <ul className="notification-list">
                    <li>• Подтверждении записей</li>
                    <li>• Отмене записей</li>
                    <li>• Результатах анализов</li>
                    <li>• Сообщениях врача</li>
                    <li>• Объявлениях клиники</li>
                  </ul>
                </div>
              </div>

              {/* Patient Information Card */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Информация о пациенте</h3>
                </div>
                <div className="card-body">
                  <table className="info-table">
                    <tbody>
                      <tr>
                        <td className="info-label">ID пациента</td>
                        <td className="info-value">{patient.id}</td>
                      </tr>
                      {patient.birth_date && (
                        <tr>
                          <td className="info-label">Дата рождения</td>
                          <td className="info-value">
                            {new Date(patient.birth_date).toLocaleDateString("ru-RU", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            })}
                          </td>
                        </tr>
                      )}
                      {patient.gender && (
                        <tr>
                          <td className="info-label">Пол</td>
                          <td className="info-value">{patient.gender_display || patient.gender}</td>
                        </tr>
                      )}
                      {patient.phone && (
                        <tr>
                          <td className="info-label">Телефон</td>
                          <td className="info-value">{patient.phone}</td>
                        </tr>
                      )}
                      {patient.email && (
                        <tr>
                          <td className="info-label">Email</td>
                          <td className="info-value">{patient.email}</td>
                        </tr>
                      )}
                      <tr>
                        <td className="info-label">Дата регистрации</td>
                        <td className="info-value">
                          {new Date(patient.created_at).toLocaleDateString("ru-RU", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="card quick-actions-card">
              <div className="card-header">
                <h3 className="card-title">Quick Actions</h3>
              </div>
              <div className="quick-actions-grid">
                <button className="btn btn-outline" disabled>
                  📅 My Appointments
                  <span className="coming-soon-badge">Coming Soon</span>
                </button>
                <button className="btn btn-outline" disabled>
                  🧪 Laboratory Results
                  <span className="coming-soon-badge">Coming Soon</span>
                </button>
                <button className="btn btn-outline" disabled>
                  💊 Prescriptions
                  <span className="coming-soon-badge">Coming Soon</span>
                </button>
                <button className="btn btn-outline" disabled>
                  👤 Edit Profile
                  <span className="coming-soon-badge">Coming Soon</span>
                </button>
                <button className="btn btn-outline" disabled>
                  🔔 Telegram Notifications
                  <span className="coming-soon-badge">Coming Soon</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}