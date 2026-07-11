import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, isAuthenticated, loading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("Заполните все поля");
      return;
    }
    setSubmitting(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      const detail = err.response?.data?.detail || "Ошибка входа. Проверьте логин и пароль.";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg)",
        padding: "20px",
      }}
    >
      <div style={{ width: "100%", maxWidth: "420px" }}>
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <h1 style={{ fontSize: "48px", fontWeight: 900, letterSpacing: "-2px", lineHeight: 1 }}>
            HCMS
          </h1>
          <p style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-secondary)", marginTop: "4px", textTransform: "uppercase", letterSpacing: "1px" }}>
            Hospital Central Management System
          </p>
        </div>

        <div className="card" style={{ padding: "32px" }}>
          <h2 style={{ fontSize: "16px", fontWeight: 800, marginBottom: "24px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Вход в систему
          </h2>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Логин</label>
              <input
                id="username"
                className="input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Введите логин"
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Пароль</label>
              <input
                id="password"
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Введите пароль"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={submitting}
              style={{ width: "100%", marginTop: "8px" }}
            >
              {submitting ? "Вход..." : "Войти"}
            </button>
          </form>

          <div style={{ textAlign: "center", marginTop: "20px" }}>
            <span style={{ fontSize: "14px", color: "var(--text-secondary)" }}>
              Нет аккаунта?{" "}
            </span>
            <Link to="/register" style={{ fontWeight: 700, textDecoration: "underline" }}>
              Зарегистрироваться
            </Link>
          </div>
        </div>

        <p style={{ textAlign: "center", marginTop: "24px", fontSize: "12px", color: "var(--text-muted)", fontWeight: 600 }}>
          Система управления медицинскими учреждениями
        </p>
      </div>
    </div>
  );
}