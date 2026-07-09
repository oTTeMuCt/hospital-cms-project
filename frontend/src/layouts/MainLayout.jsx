import { Outlet, Link, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function MainLayout() {
  const { user, isAuthenticated, logout, loading } = useAuth();

  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <nav
        style={{
          borderBottom: "3px solid #000",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <Link
            to="/"
            style={{ fontSize: "24px", fontWeight: 900, letterSpacing: "-0.5px" }}
          >
            HCMS
          </Link>
          <Link to="/" style={{ fontWeight: 600, fontSize: "14px", textTransform: "uppercase" }}>
            Дашборд
          </Link>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span style={{ fontWeight: 600, fontSize: "14px" }}>
            {user?.username || user?.full_name || "Пользователь"}
          </span>
          <button className="btn btn-danger" onClick={logout} style={{ padding: "6px 14px", fontSize: "12px" }}>
            Выйти
          </button>
        </div>
      </nav>
      <main style={{ flex: 1, padding: "32px 24px" }}>
        <Outlet />
      </main>
    </div>
  );
}
