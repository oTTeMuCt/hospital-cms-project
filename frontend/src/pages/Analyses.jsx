import { useState, useEffect } from "react";
import api from "../api";

const STATUS_META = {
  created: { label: "Создан", icon: "📝", cls: "badge-warning" },
  ordered: { label: "Назначен", icon: "📋", cls: "badge-info" },
  in_progress: { label: "В работе", icon: "🔬", cls: "badge-primary" },
  completed: { label: "Готов", icon: "✅", cls: "badge-success" },
  verified: { label: "Проверен", icon: "✔️", cls: "badge-purple" },
  sent: { label: "Отправлен", icon: "📨", cls: "badge-info" },
};

export default function Analyses() {
  const [orders, setOrders] = useState([]);
  const [analysisTypes, setAnalysisTypes] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ patient: "", analysis_type: "", notes: "" });
  const [resultModal, setResultModal] = useState(null);
  const [resultForm, setResultForm] = useState({ result: "", notes: "" });

  const fetchData = async () => {
    try {
      const [ordRes, typesRes, patRes] = await Promise.allSettled([
        api.get("/analysis-orders/"),
        api.get("/analysis-types/"),
        api.get("/patients/"),
      ]);
      if (ordRes.status === "fulfilled") setOrders(ordRes.value.data.results || ordRes.value.data);
      if (typesRes.status === "fulfilled") setAnalysisTypes(typesRes.value.data.results || typesRes.value.data);
      if (patRes.status === "fulfilled") setPatients(patRes.value.data.results || patRes.value.data);
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
      await api.post("/analysis-orders/", form);
      setShowModal(false);
      setForm({ patient: "", analysis_type: "", notes: "" });
      fetchData();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : "Ошибка создания";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/analysis-orders/${id}/`, { status });
      fetchData();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : "Ошибка обновления статуса";
      setError(msg);
    }
  };

  const handleSaveResult = async (e) => {
    e.preventDefault();
    if (!resultModal) return;
    try {
      await api.patch(`/analysis-orders/${resultModal}/`, { ...resultForm, status: "completed" });
      setResultModal(null);
      fetchData();
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : "Ошибка сохранения результата";
      setError(msg);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1>🔬 Лаборатория</h1>
            <p>Управление анализами и результатами исследований</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>➕ Назначить анализ</button>
        </div>
      </div>

      <div className="page-content">
        {error && <div className="error-message">{error}</div>}

        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔬</div>
            <h3>Нет назначенных анализов</h3>
            <p>Назначьте первый анализ пациенту</p>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>➕ Назначить анализ</button>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Пациент</th>
                  <th>Анализ</th>
                  <th>Статус</th>
                  <th>Назначен</th>
                  <th>Результат</th>
                  <th style={{ width: "200px" }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => {
                  const meta = STATUS_META[o.status] || { label: o.status, icon: "❓", cls: "" };
                  return (
                    <tr key={o.id}>
                      <td style={{ fontWeight: 700 }}>
                        {o.patient_name || o.patient?.full_name || o.patient?.user?.full_name_display || `#${o.patient}`}
                      </td>
                      <td>{o.analysis_type_name || o.analysis_type?.name || `#${o.analysis_type}`}</td>
                      <td><span className={`badge ${meta.cls}`}>{meta.icon} {meta.label}</span></td>
                      <td className="text-sm">{o.requested_at ? new Date(o.requested_at).toLocaleDateString("ru-RU") : "—"}</td>
                      <td className="text-sm truncate" style={{ maxWidth: "150px" }}>{o.result || "—"}</td>
                      <td>
                        <div className="flex flex-gap">
                          {o.status === "created" && (
                            <button className="btn btn-info btn-sm" onClick={() => updateStatus(o.id, "ordered")}>📋 Назначить</button>
                          )}
                          {o.status === "ordered" && (
                            <button className="btn btn-primary btn-sm" onClick={() => updateStatus(o.id, "in_progress")}>🔬 В работу</button>
                          )}
                          {o.status === "in_progress" && (
                            <button className="btn btn-success btn-sm" onClick={() => { setResultModal(o.id); setResultForm({ result: o.result || "", notes: o.notes || "" }); }}>
                              ✅ Загрузить результат
                            </button>
                          )}
                          {o.status === "completed" && (
                            <button className="btn btn-outline btn-sm" onClick={() => updateStatus(o.id, "verified")}>✔️ Проверить</button>
                          )}
                          {o.status === "verified" && (
                            <button className="btn btn-info btn-sm" onClick={() => updateStatus(o.id, "sent")}>📨 Отправить</button>
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
                <h2>➕ Назначить анализ</h2>
                <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
              </div>
              <form onSubmit={handleCreate}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Пациент *</label>
                    <select className="input" value={form.patient} onChange={(e) => setForm({ ...form, patient: e.target.value })} required>
                      <option value="">Выберите пациента</option>
                      {patients.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Вид анализа *</label>
                    <select className="input" value={form.analysis_type} onChange={(e) => setForm({ ...form, analysis_type: e.target.value })} required>
                      <option value="">Выберите анализ</option>
                      {analysisTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Примечание</label>
                    <textarea className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Сохранение..." : "Назначить"}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {resultModal && (
          <div className="modal-overlay" onClick={() => setResultModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>📝 Загрузить результат</h2>
                <button className="close-btn" onClick={() => setResultModal(null)}>×</button>
              </div>
              <form onSubmit={handleSaveResult}>
                <div className="modal-body">
                  <div className="form-group">
                    <label>Результат анализа *</label>
                    <textarea className="input" value={resultForm.result} onChange={(e) => setResultForm({ ...resultForm, result: e.target.value })} required rows={4} placeholder="Введите результат анализа..." />
                  </div>
                  <div className="form-group">
                    <label>Примечания</label>
                    <textarea className="input" value={resultForm.notes} onChange={(e) => setResultForm({ ...resultForm, notes: e.target.value })} rows={2} />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setResultModal(null)}>Отмена</button>
                  <button type="submit" className="btn btn-success">💾 Сохранить результат</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}