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
          setError("No patient profile is linked to your account. Please contact the clinic administrator or reception.");
        } else {
          setError("Failed to load patient profile.");
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
        Loading...
      </div>
    );
  }

  return (
    <div className="patient-profile">
      <div className="page-header">
        <h1>Patient Profile</h1>
        <p>Your personal healthcare dashboard</p>
      </div>

      <div className="page-content">
        {/* Toast notification */}
        {toastVisible && (
          <div className="toast-notification">
            <span>✔</span> Patient ID copied successfully
          </div>
        )}

        {error && (
          <div className="alert alert-warning">
            <div className="alert-icon">⚠</div>
            <div>
              <strong>No patient profile found</strong>
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
              <div className="patient-id-label">Your Patient ID</div>
              <div className="patient-id-value">{formatPatientId(patient.id)}</div>
              <p className="patient-id-hint">
                Use this Patient ID when connecting to our Telegram Bot.
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
                  <h3 className="card-title">Connect Telegram</h3>
                  {patient.telegram_id ? (
                    <span className="badge badge-success">Connected</span>
                  ) : (
                    <span className="badge badge-danger">Not Connected</span>
                  )}
                </div>
                <div className="card-body">
                  <p className="text-muted" style={{ marginBottom: 16 }}>
                    To receive notifications:
                  </p>
                  <ol className="telegram-steps">
                    <li>Open <a href={TELEGRAM_BOT_LINK} target="_blank" rel="noopener noreferrer">Telegram Bot</a>.</li>
                    <li>Send: <code>/start</code></li>
                    <li>Then send: <code>/connect</code></li>
                    <li>Enter your Patient ID: <strong>{formatPatientId(patient.id)}</strong></li>
                  </ol>
                  <p className="text-muted" style={{ marginTop: 16, fontSize: 13 }}>
                    After linking your account you will receive notifications about:
                  </p>
                  <ul className="notification-list">
                    <li>• Appointment confirmations</li>
                    <li>• Appointment cancellations</li>
                    <li>• Laboratory results</li>
                    <li>• Doctor messages</li>
                    <li>• Clinic announcements</li>
                  </ul>
                </div>
              </div>

              {/* Patient Information Card */}
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Patient Information</h3>
                </div>
                <div className="card-body">
                  <table className="info-table">
                    <tbody>
                      <tr>
                        <td className="info-label">Patient ID</td>
                        <td className="info-value">{patient.id}</td>
                      </tr>
                      {patient.birth_date && (
                        <tr>
                          <td className="info-label">Birth Date</td>
                          <td className="info-value">
                            {new Date(patient.birth_date).toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            })}
                          </td>
                        </tr>
                      )}
                      {patient.gender && (
                        <tr>
                          <td className="info-label">Gender</td>
                          <td className="info-value">{patient.gender_display || patient.gender}</td>
                        </tr>
                      )}
                      {patient.phone && (
                        <tr>
                          <td className="info-label">Phone</td>
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
                        <td className="info-label">Registration Date</td>
                        <td className="info-value">
                          {new Date(patient.created_at).toLocaleDateString("en-US", {
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