import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({ full_name: "", birth_date: "", gender: "", blood_group: "", phone: "", email: "", address: "", emergency_contact: "" });
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = search ? { search } : {};
        const res = await api.get("/patients/", { params });
        setPatients(res.data.results || res.data);
      } catch {
        setError("Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [search]);

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить пациента?")) return;
    try {
      await api.delete(`/patients/${id}/`);
      setPatients(patients.filter((p) => p.id !== id));
    } catch {
      setError("Ошибка удаления");
    }
  };

  const openEdit = (p) => {
    setEditModal(p.id);
    setEditForm({
      full_name: p.full_name || "",
      birth_date: p.birth_date || "",
      gender: p.gender || "",
      blood_group: p.blood_group || "",
      phone: p.phone || "",
      email: p.email || "",
      address: p.address || "",
      emergency_contact: p.emergency_contact || "",
    });
  };

  const handleEditSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch(`/patients/${editModal}/`, editForm);
      setEditModal(null);
      const res = await api.get("/patients/", { params: search ? { search } : {} });
      setPatients(res.data.results || res.data);
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const messages = Object.entries(data)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val[0] : val}`)
          .join("; ");
        setError(messages);
      } else {
        setError("Ошибка сохранения");
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1>Пациенты</h1>
            <p>Поиск и управление карточками пациентов</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/patients/new")}>+ Регистрация</button>
        </div>
      </div>

      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}

        <div className="toolbar">
          <div className="search-box">
            <span className="search-box-icon">🔍</span>
            <input
              className="input"
              placeholder="Поиск по ФИО, телефону, паспорту..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {patients.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">👤</div>
            <h3>{search ? "Ничего не найдено" : "Нет пациентов"}</h3>
            <p>{search ? "Попробуйте изменить поисковый запрос" : "Зарегистрируйте первого пациента"}</p>
            {!search && (
              <button className="btn btn-primary" onClick={() => navigate("/patients/new")}>+ Регистрация</button>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Дата рождения</th>
                  <th>Телефон</th>
                  <th>ПИНФЛ</th>
                  <th>Паспорт</th>
                  <th style={{ width: "160px" }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600 }}>{p.full_name}</td>
                    <td>{p.birth_date || "—"}</td>
                    <td>{p.phone || "—"}</td>
                    <td>{p.pinfl || "—"}</td>
                    <td>{p.passport || "—"}</td>
                    <td>
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button className="btn btn-outline btn-sm" onClick={() => setSelectedPatient(p)}>👁️</button>
                        <button className="btn btn-outline btn-sm" onClick={() => openEdit(p)}>✏️</button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)}>🗑️</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selectedPatient && (
          <div className="modal-overlay" onClick={() => setSelectedPatient(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{selectedPatient.full_name}</h2>
                <button className="close-btn" onClick={() => setSelectedPatient(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="grid-2">
                  <div>
                    <p className="text-sm text-muted font-medium">Дата рождения</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.birth_date || "—"}</p>
                    <p className="text-sm text-muted font-medium">Пол</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.gender_display || (selectedPatient.gender === "male" ? "Мужской" : selectedPatient.gender === "female" ? "Женский" : "—")}</p>
                    <p className="text-sm text-muted font-medium">Группа крови</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.blood_group || "—"}</p>
                    <p className="text-sm text-muted font-medium">Телефон</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.phone || "—"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted font-medium">ПИНФЛ</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.pinfl || "—"}</p>
                    <p className="text-sm text-muted font-medium">Паспорт</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.passport || "—"}</p>
                    <p className="text-sm text-muted font-medium">Email</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.email || "—"}</p>
                    <p className="text-sm text-muted font-medium">Telegram</p>
                    <p style={{ marginBottom: "16px" }}>{selectedPatient.telegram_id ? `✅ ID: ${selectedPatient.telegram_id}` : "❌ Не привязан"}</p>
                  </div>
                </div>
                {selectedPatient.address && (
                  <>
                    <p className="text-sm text-muted font-medium" style={{ marginTop: "8px" }}>Адрес</p>
                    <p>{selectedPatient.address}</p>
                  </>
                )}
                {selectedPatient.emergency_contact && (
                  <>
                    <p className="text-sm text-muted font-medium" style={{ marginTop: "8px" }}>Экстренный контакт</p>
                    <p>{selectedPatient.emergency_contact}</p>
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-outline" onClick={() => setSelectedPatient(null)}>Закрыть</button>
              </div>
            </div>
          </div>
        )}

        {editModal && (
          <div className="modal-overlay" onClick={() => setEditModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Редактировать пациента</h2>
                <button className="close-btn" onClick={() => setEditModal(null)}>×</button>
              </div>
              <form onSubmit={handleEditSave}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>ФИО *</label>
                    <input className="input" value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} required />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Дата рождения</label>
                      <input className="input" type="date" value={editForm.birth_date} onChange={(e) => setEditForm({ ...editForm, birth_date: e.target.value })} />
                    </div>
                    <div className="form-group">
                      <label>Пол</label>
                      <select className="input" value={editForm.gender} onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}>
                        <option value="">Не указан</option>
                        <option value="male">Мужской</option>
                        <option value="female">Женский</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Телефон</label>
                      <input className="input" type="tel" value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} placeholder="+998 XX XXX XX XX" />
                    </div>
                    <div className="form-group">
                      <label>Email</label>
                      <input className="input" type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} placeholder="email@example.com" />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Группа крови</label>
                      <select className="input" value={editForm.blood_group} onChange={(e) => setEditForm({ ...editForm, blood_group: e.target.value })}>
                        <option value="">Не указана</option>
                        {["I+", "I-", "II+", "II-", "III+", "III-", "IV+", "IV-"].map((bg) => (
                          <option key={bg} value={bg}>{bg}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Экстренный контакт</label>
                      <input className="input" value={editForm.emergency_contact} onChange={(e) => setEditForm({ ...editForm, emergency_contact: e.target.value })} placeholder="ФИО и телефон" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Адрес регистрации</label>
                    <input className="input" value={editForm.address} onChange={(e) => setEditForm({ ...editForm, address: e.target.value })} placeholder="Город, улица, дом" />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setEditModal(null)}>Отмена</button>
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