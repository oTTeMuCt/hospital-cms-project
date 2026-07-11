import { useState, useEffect } from "react";
import api from "../api";

const STATUS_LABELS = {
  pending: { label: "Ожидает", cls: "badge-warning" },
  confirmed: { label: "Подтверждена", cls: "badge-success" },
  completed: { label: "Завершена", cls: "badge-info" },
  cancelled: { label: "Отменена", cls: "badge-danger" },
  no_show: { label: "Неявка", cls: "badge-danger" },
};

export default function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ patient: "", doctor: "", department: "", scheduled_at: "", reason: "" });
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const [appRes, patRes, docRes, depRes] = await Promise.allSettled([
        api.get("/appointments/"),
        api.get("/patients/"),
        api.get("/staff/"),
        api.get("/departments/"),
      ]);

      if (appRes.status === "fulfilled") setAppointments(appRes.value.data.results || appRes.value.data);
      if (patRes.status === "fulfilled") setPatients(patRes.value.data.results || patRes.value.data);
      if (docRes.status === "fulfilled") setDoctors(docRes.value.data.results || docRes.value.data);
      if (depRes.status === "fulfilled") setDepartments(depRes.value.data.results || depRes.value.data);
    } catch {
      setError("Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/appointments/", form);
      setShowModal(false);
      setForm({ patient: "", doctor: "", department: "", scheduled_at: "", reason: "" });
      fetchData();
    } catch (err) {
      setError("Ошибка создания записи");
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/appointments/${id}/`, { status });
      fetchData();
    } catch {
      setError("Ошибка обновления статуса");
    }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1>📅 Записи на приём</h1>
            <p>Управление расписанием и записями пациентов</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>➕ Новая запись</button>
        </div>
      </div>

      <div className="page-content">
        {error && <div className="error-message">{error}</div>}

        {appointments.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📅</div>
            <h3>Нет записей</h3>
            <p>Создайте первую запись на приём</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>➕ Новая запись</button>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Пациент</th>
                  <th>Врач</th>
                  <th>Дата и время</th>
                  <th>Статус</th>
                  <th>Причина</th>
                  <th style={{ width: "160px" }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map((a) => {
                  const st = STATUS_LABELS[a.status] || { label: a.status, cls: "" };
                  return (
                    <tr key={a.id}>
                      <td style={{ fontWeight: 700 }}>
                        {a.patient_name || a.patient?.full_name || a.patient?.user?.full_name_display || `#${a.patient}`}
                      </td>
                      <td>
                        {a.doctor_name || a.doctor?.full_name || a.doctor?.user?.full_name_display || `#${a.doctor}`}
                      </td>
                      <td>{a.scheduled_at ? new Date(a.scheduled_at).toLocaleString("ru-RU") : "—"}</td>
                      <td><span className={`badge ${st.cls}`}>{st.label}</span></td>
                      <td className="text-sm text-muted truncate" style={{ maxWidth: "200px" }}>{a.reason || "—"}</td>
                      <td>
                        <div className="flex flex-gap">
                          {a.status === "pending" && (
                            <button className="btn btn-success btn-sm" onClick={() => updateStatus(a.id, "confirmed")}>✅</button>
                          )}
                          {a.status === "confirmed" && (
                            <button className="btn btn-info btn-sm" onClick={() => updateStatus(a.id, "completed")}>✔️</button>
                          )}
                          {(a.status === "pending" || a.status === "confirmed") && (
                            <button className="btn btn-danger btn-sm" onClick={() => updateStatus(a.id, "cancelled")}>❌</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>➕ Новая запись на приём</h2>
                <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Пациент *</label>
                    <select className="input" value={form.patient} onChange={(e) => setForm({ ...form, patient: e.target.value })} required>
                      <option value="">Выберите пациента</option>
                      {patients.map((p) => (
                        <option key={p.id} value={p.id}>{p.full_name}</option>
                      ))}
                    </select>
                  </div>
                    <div className="form-group">
                      <label>Врач</label>
                      <select className="input" value={form.doctor} onChange={(e) => setForm({ ...form, doctor: e.target.value })}>
                        <option value="">Выберите врача</option>
                        {doctors.filter(d => d.user).map((d) => (
                          <option key={d.id} value={d.user}>
                            {d.user_full_name || d.user_name || d.user?.full_name_display || d.user?.first_name || `#${d.user}`}
                          </option>
                        ))}
                      </select>
                    </div>
                  <div className="form-group">
                    <label>Отделение</label>
                    <select className="input" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}>
                      <option value="">Выберите отделение</option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Дата и время *</label>
                    <input className="input" type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label>Причина обращения</label>
                    <textarea className="input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Сохранение..." : "➕ Создать"}</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}