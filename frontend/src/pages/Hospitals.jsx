import { useState, useEffect } from "react";
import api from "../api";

export default function Hospitals() {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", address: "", phone: "", working_hours: "", short_name: "" });
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const res = await api.get("/hospitals/");
      setHospitals(res.data.results || res.data);
    } catch (err) {
      setError("Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ name: "", address: "", phone: "", working_hours: "", short_name: "" });
    setShowModal(true);
  };

  const openEdit = (h) => {
    setEditing(h.id);
    setForm({ name: h.name, address: h.address || "", phone: h.phone || "", working_hours: h.working_hours || "", short_name: h.short_name || "" });
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await api.patch(`/hospitals/${editing}/`, form);
      } else {
        await api.post("/hospitals/", form);
      }
      setShowModal(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить больницу?")) return;
    try {
      await api.delete(`/hospitals/${id}/`);
      fetchData();
    } catch {
      setError("Ошибка удаления");
    }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1>🏥 Больницы</h1>
            <p>Управление медицинскими учреждениями</p>
          </div>
          <button className="btn btn-primary" onClick={openCreate}>➕ Добавить</button>
        </div>
      </div>

      <div className="page-content">
        {error && <div className="error-message">{error}</div>}

        {hospitals.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🏥</div>
            <h3>Нет больниц</h3>
            <p>Добавьте первую больницу в систему</p>
            <button className="btn btn-primary" onClick={openCreate}>➕ Добавить больницу</button>
          </div>
        ) : (
          <div className="grid-2">
            {hospitals.map((h) => (
              <div key={h.id} className="card card-hover">
                <div className="flex-between" style={{ marginBottom: "12px" }}>
                  <h3 style={{ fontSize: "18px", fontWeight: 800 }}>{h.name}</h3>
                  <div className="flex flex-gap">
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
              <div className="modal-header">
                <h2>{editing ? "Редактировать" : "Добавить"} больницу</h2>
                <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
              </div>
              <form onSubmit={handleSave}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Название *</label>
                    <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Краткое название</label>
                      <input className="input" value={form.short_name} onChange={(e) => setForm({ ...form, short_name: e.target.value })} />
                    </div>
                    <div className="form-group">
                      <label>Телефон</label>
                      <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Адрес</label>
                    <input className="input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Режим работы</label>
                    <input className="input" value={form.working_hours} onChange={(e) => setForm({ ...form, working_hours: e.target.value })} placeholder="Пн-Пт: 8:00-18:00" />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Сохранение..." : "Сохранить"}</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}