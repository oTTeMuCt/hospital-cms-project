import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Sidebar() {
  const { user, role, roleLabel, logout } = useAuth();

  const links = {
    admin: [
      { to: "/", icon: "📊", label: "Дашборд" },
      { to: "/hospitals", icon: "🏥", label: "Больницы" },
      { to: "/departments", icon: "🏛️", label: "Отделения" },
      { to: "/staff", icon: "👨‍⚕️", label: "Сотрудники" },
      { to: "/patients", icon: "👤", label: "Пациенты" },
      { to: "/appointments", icon: "📅", label: "Приёмы" },
      { to: "/analyses", icon: "🔬", label: "Анализы" },
      { to: "/reports", icon: "📈", label: "Отчёты" },
      { to: "/audit", icon: "📋", label: "Журнал" },
    ],
    chief_doctor: [
      { to: "/", icon: "📊", label: "Дашборд" },
      { to: "/patients", icon: "👤", label: "Пациенты" },
      { to: "/analyses", icon: "🔬", label: "Результаты" },
      { to: "/reports", icon: "📈", label: "Отчёты" },
    ],
    doctor: [
      { to: "/", icon: "📊", label: "Дашборд" },
      { to: "/patients", icon: "👤", label: "Пациенты" },
      { to: "/appointments", icon: "📅", label: "Расписание" },
      { to: "/analyses", icon: "🔬", label: "Назначения" },
    ],
    lab_tech: [
      { to: "/", icon: "📊", label: "Дашборд" },
      { to: "/analyses", icon: "🔬", label: "Очередь анализов" },
    ],
    registrar: [
      { to: "/", icon: "📊", label: "Дашборд" },
      { to: "/patients", icon: "👤", label: "Пациенты" },
      { to: "/patients/new", icon: "➕", label: "Регистрация" },
      { to: "/appointments", icon: "📅", label: "Запись на приём" },
    ],
    patient: [
      { to: "/", icon: "📊", label: "Мои данные" },
      { to: "/profile", icon: "👤", label: "Профиль" },
      { to: "/my-analyses", icon: "🔬", label: "Мои анализы" },
    ],
  };

  const currentLinks = links[role] || links.patient;

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>HCMS</h1>
        <p>Hospital Central Management</p>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section">
          <div className="sidebar-section-title">Навигация</div>
          {currentLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `sidebar-link${isActive ? " active" : ""}`
              }
            >
              <span className="sidebar-link-icon">{link.icon}</span>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="sidebar-user-name">
            {user?.first_name} {user?.last_name}
          </span>
          <span className="sidebar-user-role">{roleLabel}</span>
        </div>
        <button className="btn btn-danger btn-sm w-full" onClick={logout}>
          <span>🚪 Выйти</span>
        </button>
      </div>
    </aside>
  );
}
