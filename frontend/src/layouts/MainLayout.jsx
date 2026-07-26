import { useState, useEffect, useCallback } from "react";
import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/Sidebar";

export default function MainLayout() {
  const { isAuthenticated, loading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 992);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  // Close sidebar on ESC key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") closeSidebar();
    };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [closeSidebar]);

  if (loading) return (
    <div className="loading" style={{ minHeight: "100vh" }}>
      <div className="spinner" />
      Загрузка...
    </div>
  );

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* Mobile header with hamburger */}
      {isMobile && (
        <header className="mobile-header">
          <button
            className="hamburger-btn"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? "Close menu" : "Open menu"}
            aria-expanded={sidebarOpen}
          >
            <span className={`hamburger-line${sidebarOpen ? " open" : ""}`} />
          </button>
          <span className="mobile-header-title">HCMS</span>
          <div style={{ width: 44 }} />
        </header>
      )}

      {/* Backdrop overlay */}
      {sidebarOpen && <div className="sidebar-backdrop" onClick={closeSidebar} />}

      <Sidebar mobileOpen={sidebarOpen} onClose={closeSidebar} isMobile={isMobile} />

      <div className={`main-area${isMobile ? " mobile" : ""}`}>
        <Outlet />
      </div>
    </div>
  );
}