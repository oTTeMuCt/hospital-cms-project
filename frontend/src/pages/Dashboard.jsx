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

export default function Dashboard() {
  const { user, role, roleLabel } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [patientsRes, appointmentsRes, analysesRes] = await Promise.allSettled([
          api.get("/patients/"),
          api.get("/appointments/"),
          api.get("/analysis-orders/"),
        ]);

        setStats({
          patients: patientsRes.status === "fulfilled" ? patientsRes.value.data?.count || patientsRes.value.data?.length || "—" : "—",
          appointments: appointmentsRes.status === "fulfilled" ? appointmentsRes.value.data?.count || appointmentsRes.value.data?.length || "—" : "—",
          analyses: analysesRes.status === "fulfilled" ? analysesRes.value.data?.count || analysesRes.value.data?.length || "—" : "—",
        });
      } catch (err) {
        setError("Не удалось загрузить статистику");
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const statCards = [
    { icon: "👤", label: "Пациенты", value: stats?.patients || "—", color: "var(--primary)" },
    { icon: "📅", label: "Приёмы", value: stats?.appointments || "—", color: "var(--success)" },
    { icon: "🔬", label: "Анализы", value: stats?.analyses || "—", color: "var(--purple)" },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>Дашборд</h1>
        <p>
          Добро пожаловать, {user?.first_name || user?.username}! {ROLE_WELCOME[role] || ""}
        </p>
      </div>

      <div className="page-content">
        <div className="mb-4 flex flex-wrap flex-gap">
          <span className="badge badge-primary">{roleLabel}</span>
          {user?.email && <span className="badge badge-info">{user.email}</span>}
        </div>

        {error && <div className="error-message mb-4">{error}</div>}

        {loading ? (
          <div className="loading">
            <div className="spinner" />
            Загрузка данных...
          </div>
        ) : (
          <div className="grid-3">
            {statCards.map((stat) => (
              <div key={stat.label} className="stat-card">
                <div className="stat-card-icon">{stat.icon}</div>
                <div className="stat-card-value" style={{ color: stat.color }}>
                  {stat.value}
                </div>
                <div className="stat-card-label">{stat.label}</div>
              </div>
            ))}
          </div>
        )}

        {role === "doctor" && (
          <div className="card mt-6">
            <div className="card-header">
              <h3 className="card-title">📋 Быстрые действия</h3>
            </div>
            <div className="flex flex-gap flex-wrap">
              <Link to="/patients" className="btn btn-primary btn-sm">👤 Все пациенты</Link>
              <Link to="/appointments" className="btn btn-success btn-sm">📅 Расписание</Link>
              <Link to="/analyses" className="btn btn-outline btn-sm">🔬 Назначить анализ</Link>
            </div>
          </div>
        )}

        {role === "registrar" && (
          <div className="card mt-6">
            <div className="card-header">
              <h3 className="card-title">📋 Быстрые действия</h3>
            </div>
            <div className="flex flex-gap flex-wrap">
              <Link to="/patients/new" className="btn btn-primary btn-sm">➕ Регистрация пациента</Link>
              <Link to="/appointments" className="btn btn-success btn-sm">📅 Создать запись</Link>
              <Link to="/patients" className="btn btn-outline btn-sm">👤 Поиск пациента</Link>
            </div>
          </div>
        )}

        {role === "lab_tech" && (
          <div className="card mt-6">
            <div className="card-header">
              <h3 className="card-title">📋 Быстрые действия</h3>
            </div>
            <div className="flex flex-gap flex-wrap">
              <Link to="/analyses" className="btn btn-primary btn-sm">🔬 Очередь анализов</Link>
            </div>
          </div>
        )}

        {role === "admin" && (
          <div className="grid-2 mt-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">🏥 Управление</h3>
              </div>
              <div className="flex flex-col flex-gap">
                <Link to="/hospitals" className="btn btn-outline btn-sm w-full text-left" style={{ justifyContent: "flex-start" }}>🏥 Больницы</Link>
                <Link to="/departments" className="btn btn-outline btn-sm w-full text-left" style={{ justifyContent: "flex-start" }}>🏛️ Отделения</Link>
                <Link to="/staff" className="btn btn-outline btn-sm w-full text-left" style={{ justifyContent: "flex-start" }}>👨‍⚕️ Сотрудники</Link>
              </div>
            </div>
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">📊 Мониторинг</h3>
              </div>
              <div className="flex flex-col flex-gap">
                <Link to="/audit" className="btn btn-outline btn-sm w-full text-left" style={{ justifyContent: "flex-start" }}>📋 Журнал действий</Link>
                <Link to="/reports" className="btn btn-outline btn-sm w-full text-left" style={{ justifyContent: "flex-start" }}>📈 Отчёты</Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}