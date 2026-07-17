import { useState, useEffect } from "react";
import api from "../api";

export default function Hospitals() {
  const [hospitals, setHospitals] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", short_name: "", address: "", phone: "", working_hours: "", chief_doctor: "", timezone: "", country_code: "" });
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const res = await api.get("/hospitals/");
      setHospitals(res.data.results || res.data);
    } catch { setError("Ошибка загрузки"); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const fetchDoctors = async () => {
    try {
      const res = await api.get("/users/");
      setDoctors((res.data.results || res.data).filter((u) => u.role === "doctor" || u.role === "chief_doctor"));
    } catch {}
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ name: "", short_name: "", address: "", phone: "", working_hours: "", chief_doctor: "", timezone: "", country_code: "" });
    setShowModal(true);
    fetchDoctors();
  };
  const openEdit = (h) => {
    setEditing(h.id);
    setForm({
      name: h.name,
      short_name: h.short_name || "",
      address: h.address || "",
      phone: h.phone || "",
      working_hours: h.working_hours || "",
      chief_doctor: h.chief_doctor || "",
      timezone: h.timezone || "",
      country_code: h.country_code || "",
    });
    setShowModal(true);
    fetchDoctors();
  };

  const handleSave = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.chief_doctor) delete payload.chief_doctor;
      if (editing) { await api.patch(`/hospitals/${editing}/`, payload); }
      else { await api.post("/hospitals/", payload); }
      setShowModal(false); fetchData();
    } catch (err) { setError(err.response?.data?.name?.[0] || "Ошибка сохранения"); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить больницу?")) return;
    try { await api.delete(`/hospitals/${id}/`); fetchData(); }
    catch { setError("Ошибка удаления"); }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header"><div className="flex-between"><div><h1>Больницы</h1><p>Управление медицинскими учреждениями</p></div><button className="btn btn-primary" onClick={openCreate}>+ Добавить</button></div></div>
      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}
        {hospitals.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🏥</div><h3>Нет больниц</h3><p>Добавьте первую больницу в систему</p><button className="btn btn-primary" onClick={openCreate}>+ Добавить больницу</button></div>
        ) : (
          <div className="grid-2">
            {hospitals.map((h) => (
              <div key={h.id} className="card card-hover">
                <div className="flex-between" style={{ marginBottom: "12px" }}>
                  <h3 style={{ fontSize: "18px", fontWeight: 600 }}>{h.name}</h3>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <button className="btn btn-outline btn-sm" onClick={() => openEdit(h)}>✏️</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(h.id)}>🗑️</button>
                  </div>
                </div>
                {h.short_name && <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px" }}>Кратко: {h.short_name}</p>}
                {h.address && <p style={{ fontSize: "14px", marginBottom: "4px" }}>📍 {h.address}</p>}
                {h.phone && <p style={{ fontSize: "14px", marginBottom: "4px" }}>📞 {h.phone}</p>}
                {h.working_hours && <p style={{ fontSize: "14px", color: "var(--text-secondary)" }}>🕐 {h.working_hours}</p>}
              </div>
            ))}
          </div>
        )}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header"><h2>{editing ? "Редактировать" : "Добавить"} больницу</h2><button className="close-btn" onClick={() => setShowModal(false)}>×</button></div>
              <form onSubmit={handleSave}><div className="modal-body">
                <div className="form-group"><label>Название *</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
                <div className="form-row">
                  <div className="form-group"><label>Краткое название</label><input className="input" value={form.short_name} onChange={(e) => setForm({ ...form, short_name: e.target.value })} /></div>
                  <div className="form-group"><label>Телефон</label><input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
                </div>
                <div className="form-group"><label>Адрес</label><input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
                <div className="form-group"><label>Режим работы</label><input className="input" value={form.working_hours} onChange={(e) => setForm({ ...form, working_hours: e.target.value })} placeholder="Пн-Пт: 8:00-18:00" /></div>
                <div className="form-row">
                  <div className="form-group"><label>Главный врач</label><select className="input" value={form.chief_doctor} onChange={(e) => setForm({ ...form, chief_doctor: e.target.value })}><option value="">Не назначен</option>{doctors.map((d) => <option key={d.id} value={d.id}>{d.last_name} {d.first_name} ({d.username})</option>)}</select></div>
                  <div className="form-group"><label>Часовой пояс (IANA)</label><input className="input" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })} placeholder="Asia/Tashkent" /></div>
                </div>
                <div className="form-group"><label>Код страны (ISO)</label><input className="input" value={form.country_code} onChange={(e) => setForm({ ...form, country_code: e.target.value })} placeholder="UZ" maxLength={8} /></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Сохранение..." : "Сохранить"}</button></div></form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}