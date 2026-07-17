import { useState, useEffect } from "react";
import api from "../api";

export default function Staff() {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await api.get("/staff/");
        setStaff(res.data.results || res.data);
      } catch { setError("Ошибка загрузки"); }
      finally { setLoading(false); }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Сотрудники</h1>
        <p>Управление персоналом медицинских учреждений</p>
      </div>
      <div className="page-content">
        {error && <div className="alert alert-error">{error}</div>}
        {staff.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">👨‍⚕️</div>
            <h3>Нет сотрудников</h3>
            <p>Добавьте сотрудников через панель администратора</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>ФИО</th><th>Должность</th><th>Больница</th><th>Отделение</th><th>Телефон</th></tr></thead>
              <tbody>
                {staff.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>
                      {s.user_full_name || s.user_name || s.user?.full_name_display || `${s.user?.first_name || ""} ${s.user?.last_name || ""}`.trim() || `#${s.user}`}
                    </td>
                    <td>{s.position || "—"}</td>
                    <td>{s.hospital?.name || s.hospital_name || `#${s.hospital}` || "—"}</td>
                    <td>{s.department?.name || s.department_name || `#${s.department}` || "—"}</td>
                    <td>{s.phone || "—"}</td>
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
