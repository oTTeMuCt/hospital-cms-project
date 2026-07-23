import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api";

const STATUS_META = {
  created: { label: "Создан", cls: "badge-warning" },
  ordered: { label: "Назначен", cls: "badge-info" },
  in_progress: { label: "В работе", cls: "badge-primary" },
  completed: { label: "Готов", cls: "badge-success" },
  verified: { label: "Проверен", cls: "badge-purple" },
  sent: { label: "Отправлен", cls: "badge-info" },
};

const INTERP_LABELS = {
  normal: { label: "Норма", cls: "badge-success" },
  high: { label: "Повышен", cls: "badge-danger" },
  low: { label: "Понижен", cls: "badge-warning" },
};

export default function MyAnalyses() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    const fetchMyAnalyses = async () => {
      if (!user || user.role !== "patient") {
        setLoading(false);
        return;
      }
      try {
        // Backend filters by patient__user=request.user for patient role,
        // so we can fetch all analysis orders and only ours will be returned
        const res = await api.get("/analysis-orders/");
        setAnalyses(res.data.results || res.data);
      } catch (err) {
        if (err.response?.status === 403) {
          setError("У вас нет доступа. Обратитесь к администратору.");
        } else {
          setError("Не удалось загрузить анализы");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchMyAnalyses();
  }, [user]);

  const renderResultDetails = (a) => {
    if (!a.result_values || a.result_values.length === 0) {
      return <span style={{ color: "var(--text-muted)" }}>{a.result || "—"}</span>;
    }
    return (
      <div style={{ fontSize: "13px", lineHeight: "1.8" }}>
        {a.result_values.map((rv) => (
          <div key={rv.id || rv.field_key} style={{ display: "flex", gap: "8px", alignItems: "center", padding: "4px 0", borderBottom: "1px solid #f1f5f9" }}>
            <span style={{ fontWeight: 500, minWidth: "160px" }}>{rv.field_name}:</span>
            <span style={{ fontWeight: 600 }}>{rv.value}</span>
            {rv.unit && <span style={{ color: "var(--text-muted)" }}>{rv.unit}</span>}
            {rv.interpretation && (
              <span className={`badge ${INTERP_LABELS[rv.interpretation]?.cls || "badge-info"}`} style={{ fontSize: "10px" }}>
                {INTERP_LABELS[rv.interpretation]?.label || rv.interpretation}
              </span>
            )}
            {rv.reference_range_text && (
              <span style={{ color: "var(--text-muted)", fontSize: "11px" }}>
                (норма: {rv.reference_range_text})
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
      <div className="page-header">
        <h1>Мои анализы</h1>
        <p>Просмотр результатов ваших анализов и исследований</p>
      </div>
      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}
        {analyses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔬</div>
            <h3>У вас пока нет анализов</h3>
            <p>Когда врач назначит вам анализ, он появится здесь. Также вы можете проверить результаты через Telegram-бота.</p>
            <div className="flex-center flex-gap" style={{ marginTop: "16px" }}>
              <a href="https://t.me/HospitalCMSbot" target="_blank" rel="noopener noreferrer" className="badge badge-info" style={{ cursor: "pointer", textDecoration: "none" }}>💬 Telegram: @HospitalCMSbot</a>
              <span className="badge badge-success">✅ SMS</span>
              <span className="badge badge-primary">📧 Email</span>
            </div>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>#</th><th>Вид анализа</th><th>Статус</th><th>Дата назначения</th><th>Результат</th></tr></thead>
              <tbody>
                {analyses.map((a, idx) => {
                  const meta = STATUS_META[a.status] || { label: a.status, cls: "badge-warning" };
                  const hasDetails = a.result_values && a.result_values.length > 0;
                  return (
                    <tr key={a.id}
                      onClick={() => hasDetails && setExpandedId(expandedId === a.id ? null : a.id)}
                      style={{ cursor: hasDetails ? "pointer" : "default" }}
                    >
                      <td>{idx + 1}</td>
                      <td style={{ fontWeight: 600 }}>{a.analysis_type_name || a.analysis_type?.name || `#${a.analysis_type}`}</td>
                      <td><span className={`badge ${meta.cls}`}>{meta.label}</span></td>
                      <td className="text-sm">{a.requested_at ? new Date(a.requested_at).toLocaleDateString("ru-RU") : "—"}</td>
                      <td>
                        {expandedId === a.id ? renderResultDetails(a) : (
                          <span className="text-sm truncate" style={{ maxWidth: "200px", display: "inline-block" }}>
                            {a.result || "—"}
                            {hasDetails && <span style={{ color: "var(--primary)", marginLeft: "8px", fontSize: "11px" }}>👁️ нажмите для просмотра</span>}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}