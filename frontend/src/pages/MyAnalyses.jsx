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

export default function MyAnalyses() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMyAnalyses = async () => {
      try {
        const patientsRes = await api.get("/patients/");
        const patients = patientsRes.data.results || patientsRes.data;
        if (patients && patients.length > 0) {
          const patientId = patients[0].id;
          const res = await api.get("/analysis-orders/", { params: { patient: patientId } });
          setAnalyses(res.data.results || res.data);
        }
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
    if (user?.role === "patient") {
      fetchMyAnalyses();
    } else {
      setLoading(false);
    }
  }, [user]);

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
                  return (
                    <tr key={a.id}>
                      <td>{idx + 1}</td>
                      <td style={{ fontWeight: 600 }}>{a.analysis_type_name || a.analysis_type?.name || `#${a.analysis_type}`}</td>
                      <td><span className={`badge ${meta.cls}`}>{meta.label}</span></td>
                      <td className="text-sm">{a.requested_at ? new Date(a.requested_at).toLocaleDateString("ru-RU") : "—"}</td>
                      <td>{a.result || "—"}</td>
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
