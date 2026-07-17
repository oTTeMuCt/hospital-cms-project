import { useState, useEffect } from "react";
import api from "../api";

export default function Departments() {
  const [departments, setDepartments] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: "", hospital: "", department_type: "", description: "", manager: "" });

  const fetchData = async () => {
    try {
      const [depRes, hospRes] = await Promise.all([
        api.get("/departments/"), api.get("/hospitals/"),
      ]);
      setDepartments(depRes.data.results || depRes.data);
      setHospitals(hospRes.data.results || hospRes.data);
    } catch { setError("Ошибка загрузки"); }
    finally { setLoading(false); }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get("/users/");
      setUsers(res.data.results || res.data);
    } catch {}
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ name: "", hospital: hospitals[0]?.id || "", department_type: "", description: "", manager: "" });
    setShowModal(true);
    fetchUsers();
  };
  const openEdit = (d) => {
    setEditing(d.id);
    setForm({
      name: d.name,
      hospital: d.hospital?.id || d.hospital,
      department_type: d.department_type || "",
      description: d.description || "",
      manager: d.manager || "",
    });
    setShowModal(true);
    fetchUsers();
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...form };
      if (!payload.manager) delete payload.manager;
      if (editing) { await api.patch(`/departments/${editing}/`, payload); }
      else { await api.post("/departments/", payload); }
      setShowModal(false); fetchData();
    } catch { setError("Ошибка сохранения"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить отделение?")) return;
    try { await api.delete(`/departments/${id}/`); fetchData(); }
    catch { setError("Ошибка удаления"); }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header"><div className="flex-between"><div><h1>Отделения</h1><p>Управление отделениями больниц</p></div><button className="btn btn-primary" onClick={openCreate}>+ Добавить</button></div></div>
      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}
        {departments.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🏛️</div><h3>Нет отделений</h3><p>Создайте первое отделение</p><button className="btn btn-primary" onClick={openCreate}>+ Добавить отделение</button></div>
        ) : (
          <div className="table-wrap"><table><thead><tr><th>Название</th><th>Больница</th><th>Тип</th><th>Заведующий</th><th style={{ width: "100px" }}>Действия</th></tr></thead>
            <tbody>{departments.map((d) => (
              <tr key={d.id}>
                <td style={{ fontWeight: 600 }}>{d.name}</td>
                <td>{d.hospital?.name || d.hospital_name || `#${d.hospital}` || "—"}</td>
                <td><span className="badge badge-info">{d.department_type || "—"}</span></td>
                <td className="text-sm">{d.manager_name || d.manager?.full_name_display || d.manager?.username || (d.manager ? `#${d.manager}` : "—")}</td>
                <td><div style={{ display: "flex", gap: "6px" }}><button className="btn btn-outline btn-sm" onClick={() => openEdit(d)}>✏️</button><button className="btn btn-danger btn-sm" onClick={() => handleDelete(d.id)}>🗑️</button></div></td>
              </tr>
            ))}</tbody></table></div>
        )}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header"><h2>{editing ? "Редактировать" : "Добавить"} отделение</h2><button className="close-btn" onClick={() => setShowModal(false)}>×</button></div>
              <form onSubmit={handleSave}><div className="modal-body">
                <div className="form-group"><label>Больница *</label><select className="input" value={form.hospital} onChange={(e) => setForm({ ...form, hospital: e.target.value })} required><option value="">Выберите больницу</option>{hospitals.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}</select></div>
                <div className="form-group"><label>Название *</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
                <div className="form-group"><label>Тип отделения</label><select className="input" value={form.department_type} onChange={(e) => setForm({ ...form, department_type: e.target.value })}><option value="">Выберите тип</option><option value="therapy">Терапия</option><option value="surgery">Хирургия</option><option value="cardiology">Кардиология</option><option value="neurology">Неврология</option><option value="laboratory">Лаборатория</option><option value="xray">Рентген</option><option value="ultrasound">УЗИ</option><option value="reception">Приёмное отделение</option><option value="other">Другое</option></select></div>
                <div className="form-group"><label>Заведующий отделением</label><select className="input" value={form.manager} onChange={(e) => setForm({ ...form, manager: e.target.value })}><option value="">Не назначен</option>{users.map((u) => <option key={u.id} value={u.id}>{u.last_name} {u.first_name} ({u.username})</option>)}</select></div>
                <div className="form-group"><label>Описание</label><textarea className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button><button type="submit" className="btn btn-primary">Сохранить</button></div></form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}