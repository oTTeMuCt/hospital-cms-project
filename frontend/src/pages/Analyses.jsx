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

const INTERP_LABELS = {
  normal: { label: "Норма", cls: "badge-success" },
  high: { label: "Повышен", cls: "badge-danger" },
  low: { label: "Понижен", cls: "badge-warning" },
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
  const [resultOrder, setResultOrder] = useState(null);
  const [resultFields, setResultFields] = useState([]);
  const [resultValues, setResultValues] = useState({});
  const [resultNotes, setResultNotes] = useState("");
  const [loadingFields, setLoadingFields] = useState(false);

  const fetchData = async () => {
    try {
      const [ordRes, typesRes, patRes] = await Promise.allSettled([
        api.get("/analysis-orders/"), api.get("/analysis-types/"), api.get("/patients/"),
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
    e.preventDefault(); setSaving(true);
    try {
      await api.post("/analysis-orders/", form);
      setShowModal(false); setForm({ patient: "", analysis_type: "", notes: "" }); fetchData();
    } catch (err) {
      setError(err.response?.data ? JSON.stringify(err.response.data) : "Ошибка создания");
    } finally { setSaving(false); }
  };

  const updateStatus = async (id, status) => {
    try { await api.patch(`/analysis-orders/${id}/`, { status }); fetchData(); }
    catch (err) { setError(err.response?.data ? JSON.stringify(err.response.data) : "Ошибка обновления статуса"); }
  };

  const openResultModal = async (order) => {
    setResultOrder(order);
    setResultModal(order.id);
    setResultNotes(order.notes || "");

    // Ensure analysis_type_fields are loaded
    let fields = order.analysis_type_fields;
    if (!fields || fields.length === 0) {
      setLoadingFields(true);
      try {
        const res = await api.get(`/analysis-types/${order.analysis_type}/`);
        fields = res.data.fields || [];
        order.analysis_type_fields = fields;
      } catch {
        fields = [];
      }
      setLoadingFields(false);
    }
    setResultFields(fields);

    // Initialize result values from existing data or empty
    const values = {};
    if (order.result_values && order.result_values.length > 0) {
      order.result_values.forEach((rv) => {
        values[rv.field_key] = rv.value || "";
      });
    }
    setResultValues(values);
  };

  const handleFieldChange = (fieldKey, value) => {
    setResultValues((prev) => ({ ...prev, [fieldKey]: value }));
  };

  const handleSaveResult = async (e) => {
    e.preventDefault();
    if (!resultModal || !resultOrder) return;

    // Build result_values array from the form — use resultFields state
    const fields = resultFields.length > 0 ? resultFields : (resultOrder.analysis_type_fields || []);
    const resultValuesPayload = fields.map((f) => ({
      field_key: f.field_key,
      value: resultValues[f.field_key] || "",
    }));

    try {
      await api.patch(`/analysis-orders/${resultModal}/`, {
        result_values: resultValuesPayload,
        notes: resultNotes,
        status: "completed",
      });
      setResultModal(null);
      setResultOrder(null);
      fetchData();
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const messages = Object.entries(data)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val[0] : val}`)
          .join("; ");
        setError(messages);
      } else {
        setError("Ошибка сохранения результата");
      }
    }
  };

  const renderFieldInput = (field, value) => {
    switch (field.field_type) {
      case "choice":
        return (
          <select
            className="input"
            value={value || ""}
            onChange={(e) => handleFieldChange(field.field_key, e.target.value)}
            required={field.is_required}
          >
            <option value="">— Выберите —</option>
            {(field.options || []).map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      case "numeric":
        return (
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <input
              className="input"
              type="number"
              step="any"
              value={value || ""}
              onChange={(e) => handleFieldChange(field.field_key, e.target.value)}
              required={field.is_required}
              placeholder="Введите значение"
              style={{ flex: 1 }}
            />
            {field.unit && <span style={{ color: "var(--text-muted)", whiteSpace: "nowrap", fontSize: "14px" }}>{field.unit}</span>}
          </div>
        );
      case "text":
        return (
          <textarea
            className="input"
            value={value || ""}
            onChange={(e) => handleFieldChange(field.field_key, e.target.value)}
            required={field.is_required}
            rows={4}
            placeholder="Введите результат..."
          />
        );
      default:
        return (
          <input
            className="input"
            value={value || ""}
            onChange={(e) => handleFieldChange(field.field_key, e.target.value)}
            required={field.is_required}
          />
        );
    }
  };

  const renderReferenceRange = (field) => {
    if (field.reference_range_text) return field.reference_range_text;
    if (field.reference_range_min != null && field.reference_range_max != null) {
      return `${field.reference_range_min} – ${field.reference_range_max}`;
    }
    return null;
  };

  const renderResultValues = (order) => {
    if (!order.result_values || order.result_values.length === 0) {
      return order.result || "—";
    }
    return (
      <div style={{ fontSize: "12px", lineHeight: "1.6" }}>
        {order.result_values.map((rv) => (
          <div key={rv.id || rv.field_key} style={{ marginBottom: "2px" }}>
            <strong>{rv.field_name}:</strong> {rv.value}
            {rv.unit && <span style={{ color: "var(--text-muted)" }}> {rv.unit}</span>}
            {rv.interpretation && (
              <span className={`badge ${INTERP_LABELS[rv.interpretation]?.cls || "badge-info"}`} style={{ marginLeft: "4px", fontSize: "10px" }}>
                {INTERP_LABELS[rv.interpretation]?.label || rv.interpretation}
              </span>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header"><div className="flex-between"><div><h1>Лаборатория</h1><p>Управление анализами и результатами исследований</p></div><button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Назначить анализ</button></div></div>
      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}
        {orders.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🔬</div><h3>Нет назначенных анализов</h3><p>Назначьте первый анализ пациенту</p><button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Назначить анализ</button></div>
        ) : (
          <div className="table-wrap">
            <table><thead><tr><th>Пациент</th><th>Анализ</th><th>Статус</th><th>Назначен</th><th>Результат</th><th style={{ width: "200px" }}>Действия</th></tr></thead>
              <tbody>{orders.map((o) => {
                const meta = STATUS_META[o.status] || { label: o.status, icon: "❓", cls: "" };
                return (
                  <tr key={o.id}>
                    <td style={{ fontWeight: 600 }}>{o.patient_name || o.patient?.full_name || o.patient?.user?.full_name_display || `#${o.patient}`}</td>
                    <td>{o.analysis_type_name || o.analysis_type?.name || `#${o.analysis_type}`}</td>
                    <td><span className={`badge ${meta.cls}`}>{meta.icon} {meta.label}</span></td>
                    <td className="text-sm">{o.requested_at ? new Date(o.requested_at).toLocaleDateString("ru-RU") : "—"}</td>
                    <td className="text-sm" style={{ maxWidth: "250px" }}>{renderResultValues(o)}</td>
                    <td>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {o.status === "created" && <button className="btn btn-info btn-sm" onClick={() => updateStatus(o.id, "ordered")}>📋 Назначить</button>}
                        {o.status === "ordered" && <button className="btn btn-primary btn-sm" onClick={() => updateStatus(o.id, "in_progress")}>🔬 В работу</button>}
                        {o.status === "in_progress" && <button className="btn btn-success btn-sm" onClick={() => openResultModal(o)}>✅ Результат</button>}
                        {o.status === "completed" && <button className="btn btn-outline btn-sm" onClick={() => updateStatus(o.id, "verified")}>✔️ Проверить</button>}
                        {o.status === "verified" && <button className="btn btn-info btn-sm" onClick={() => updateStatus(o.id, "sent")}>📨 Отправить</button>}
                      </div>
                    </td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        )}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header"><h2>Назначить анализ</h2><button className="close-btn" onClick={() => setShowModal(false)}>×</button></div>
              <form onSubmit={handleCreate}><div className="modal-body">
                <div className="form-group"><label>Пациент *</label><select className="input" value={form.patient} onChange={(e) => setForm({ ...form, patient: e.target.value })} required><option value="">Выберите пациента</option>{patients.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</select></div>
                <div className="form-group"><label>Вид анализа *</label><select className="input" value={form.analysis_type} onChange={(e) => setForm({ ...form, analysis_type: e.target.value })} required><option value="">Выберите анализ</option>{analysisTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></div>
                <div className="form-group"><label>Примечание</label><textarea className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-outline" onClick={() => setShowModal(false)}>Отмена</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Сохранение..." : "Назначить"}</button></div></form>
            </div>
          </div>
        )}
        {resultModal && resultOrder && (
          <div className="modal-overlay" onClick={() => setResultModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "700px" }}>
              <div className="modal-header">
                <h2>Результат: {resultOrder.analysis_type_name}</h2>
                <button className="close-btn" onClick={() => setResultModal(null)}>×</button>
              </div>
              <form onSubmit={handleSaveResult}>
                <div className="modal-body">
                  <p style={{ marginBottom: "16px", color: "var(--text-secondary)", fontSize: "14px" }}>
                    Пациент: <strong>{resultOrder.patient_name || resultOrder.patient?.full_name || `#${resultOrder.patient}`}</strong>
                  </p>

                  {(resultFields.length > 0 ? resultFields : (resultOrder.analysis_type_fields || [])).map((field) => (
                    <div key={field.field_key} className="form-group">
                      <label>
                        {field.field_name}
                        {field.unit && <span style={{ color: "var(--text-muted)", fontWeight: "normal" }}> ({field.unit})</span>}
                        {field.is_required && <span style={{ color: "var(--danger)" }}> *</span>}
                      </label>
                      {renderFieldInput(field, resultValues[field.field_key])}
                      {renderReferenceRange(field) && (
                        <p className="form-hint">Норма: {renderReferenceRange(field)}</p>
                      )}
                    </div>
                  ))}

                  <div className="form-group">
                    <label>Примечания</label>
                    <textarea className="input" value={resultNotes} onChange={(e) => setResultNotes(e.target.value)} rows={2} />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline" onClick={() => setResultModal(null)}>Отмена</button>
                  <button type="submit" className="btn btn-success">Сохранить результат</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}