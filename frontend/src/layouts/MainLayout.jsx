import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/Sidebar";

export default function MainLayout() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return (
    <div className="loading" style={{ minHeight: "100vh" }}>
      <div className="spinner" />
      Загрузка...
    </div>
  );

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div style={{ minHeight: "100vh" }}>
      <Sidebar />
      <div className="main-area">
        <Outlet />
      </div>
    </div>
  );
}