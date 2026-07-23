import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api";

const ROLE_WELCOME = {
  admin: "Полный доступ к управлению системой",
  chief_doctor: "Управление врачами, статистика и контроль качества",
  doctor: "Работа с пациентами, назначение анализов и заключения",
  lab_tech: "Лабораторные исследования и загрузка результатов",
  registrar: "Регистрация пациентов и запись на приём",
  patient: "Просмотр своих данных и результатов анализов",
};

const STAT_CONFIGS = [
  { icon: "👤", label: "Пациенты", key: "patients", color: "#2563eb" },
  { icon: "📅", label: "Приёмы", key: "appointments", color: "#059669" },
  { icon: "🔬", label: "Анализы", key: "analyses", color: "#7c3aed" },
];

export default function Dashboard() {
  const { user, role, roleLabel } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Use small page size to get count without fetching full data
        const [patientsRes, appointmentsRes, analysesRes] = await Promise.allSettled([
          api.get("/patients/", { params: { page: 1, page_size: 1 } }),
          api.get("/appointments/", { params: { page: 1, page_size: 1 } }),
          api.get("/analysis-orders/", { params: { page: 1, page_size: 1 } }),
        ]);

        setStats({
          patients: patientsRes.status === "fulfilled" ? patientsRes.value.data?.count || "—" : "—",
          appointments: appointmentsRes.status === "fulfilled" ? appointmentsRes.value.data?.count || "—" : "—",
          analyses: analysesRes.status === "fulfilled" ? analysesRes.value.data?.count || "—" : "—",
        });
      } catch {
        setError("Не удалось загрузить статистику");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Дашборд</h1>
        <p>Добро пожаловать, {user?.first_name || user?.username}! {ROLE_WELCOME[role] || ""}</p>
      </div>

      <div className="page-content">
        <div style={{ marginBottom: "24px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <span className="badge badge-primary">{roleLabel}</span>
          {user?.email && <span className="badge badge-info">{user.email}</span>}
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: "16px" }}>{error}</div>}

        {loading ? (
          <div className="loading">
            <div className="spinner" />
            Загрузка данных...
          </div>
        ) : (
          <div className="grid-3">
            {STAT_CONFIGS.map((stat) => (
              <div key={stat.key} className="stat-card">
                <div
                  className="stat-card-icon"
                  style={{ backgroundColor: stat.color + "15", color: stat.color }}
                >
                  {stat.icon}
                </div>
                <div className="stat-card-value" style={{ color: stat.color }}>
                  {stats?.[stat.key] || "—"}
                </div>
                <div className="stat-card-label">{stat.label}</div>
              </div>
            ))}
          </div>
        )}

        {role === "doctor" && (
          <div className="card" style={{ marginTop: "24px" }}>
            <div className="card-header">
              <h3 className="card-title">Быстрые действия</h3>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link to="/patients" className="btn btn-primary btn-sm">Все пациенты</Link>
              <Link to="/appointments" className="btn btn-success btn-sm">Расписание</Link>
              <Link to="/analyses" className="btn btn-outline btn-sm">Назначить анализ</Link>
            </div>
          </div>
        )}

        {role === "registrar" && (
          <div className="card" style={{ marginTop: "24px" }}>
            <div className="card-header">
              <h3 className="card-title">Быстрые действия</h3>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link to="/patients/new" className="btn btn-primary btn-sm">Регистрация пациента</Link>
              <Link to="/appointments" className="btn btn-success btn-sm">Создать запись</Link>
              <Link to="/patients" className="btn btn-outline btn-sm">Поиск пациента</Link>
            </div>
          </div>
        )}

        {role === "lab_tech" && (
          <div className="card" style={{ marginTop: "24px" }}>
            <div className="card-header">
              <h3 className="card-title">Быстрые действия</h3>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <Link to="/analyses" className="btn btn-primary btn-sm">Очередь анализов</Link>
            </div>
          </div>
        )}

        {role === "admin" && (
          <div className="grid-2" style={{ marginTop: "24px" }}>
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Управление</h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <Link to="/hospitals" className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start", textAlign: "left" }}>🏥 Больницы</Link>
                <Link to="/departments" className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start", textAlign: "left" }}>🏛️ Отделения</Link>
                <Link to="/staff" className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start", textAlign: "left" }}>👨‍⚕️ Сотрудники</Link>
              </div>
            </div>
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Мониторинг</h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <Link to="/audit" className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start", textAlign: "left" }}>📋 Журнал действий</Link>
                <Link to="/reports" className="btn btn-outline btn-sm" style={{ justifyContent: "flex-start", textAlign: "left" }}>📈 Отчёты</Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
