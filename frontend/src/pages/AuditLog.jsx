import { useState, useEffect } from "react";
import api from "../api";

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get("/audit-logs/");
        setLogs(res.data.results || res.data);
      } catch {
        setError("Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>📋 Журнал действий</h1>
        <p>Аудит всех действий пользователей в системе</p>
      </div>
      <div className="page-content">
        {error && <div className="error-message">{error}</div>}
        {logs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📋</div>
            <h3>Журнал пуст</h3>
            <p>Действия пользователей будут отображаться здесь</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Дата и время</th>
                  <th>Пользователь</th>
                  <th>Действие</th>
                  <th>IP-адрес</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-sm">{log.created_at ? new Date(log.created_at).toLocaleString("ru-RU") : "—"}</td>
                    <td style={{ fontWeight: 600 }}>{log.user_name || log.user || "Аноним"}</td>
                    <td>{log.action}</td>
                    <td className="text-sm text-muted">{log.ip_address || "—"}</td>
                    <td>
                      <span className={`badge ${log.succeeded ? "badge-success" : "badge-danger"}`}>
                        {log.succeeded ? "✅ Успешно" : "❌ Ошибка"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}