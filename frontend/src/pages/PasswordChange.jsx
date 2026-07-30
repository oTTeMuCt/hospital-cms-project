import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function PasswordChange() {
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (form.new_password !== form.confirm_password) {
      setError("Новый пароль и подтверждение не совпадают.");
      return;
    }
    if (form.new_password.length < 8) {
      setError("Новый пароль должен содержать минимум 8 символов.");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/auth/password-change/", {
        old_password: form.old_password,
        new_password: form.new_password,
      });
      setSuccess("Пароль успешно изменён.");
      setForm({ old_password: "", new_password: "", confirm_password: "" });
      setTimeout(() => navigate("/"), 2000);
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const msgs = Object.entries(data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
          .join("; ");
        setError(msgs);
      } else {
        setError("Ошибка при смене пароля.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-content" style={{ maxWidth: "500px", margin: "0 auto" }}>
      <div className="page-header">
        <h1>Смена пароля</h1>
        <p>Введите текущий и новый пароль</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit} className="card" style={{ padding: "24px" }}>
        <div className="form-group">
          <label htmlFor="old_password">Текущий пароль *</label>
          <input
            id="old_password"
            className="input"
            type="password"
            value={form.old_password}
            onChange={(e) => setForm({ ...form, old_password: e.target.value })}
            required
            placeholder="Введите текущий пароль"
          />
        </div>

        <div className="form-group">
          <label htmlFor="new_password">Новый пароль *</label>
          <input
            id="new_password"
            className="input"
            type="password"
            value={form.new_password}
            onChange={(e) => setForm({ ...form, new_password: e.target.value })}
            required
            minLength={8}
            placeholder="Минимум 8 символов"
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirm_password">Подтвердите новый пароль *</label>
          <input
            id="confirm_password"
            className="input"
            type="password"
            value={form.confirm_password}
            onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            required
            placeholder="Повторите новый пароль"
          />
        </div>

        <button type="submit" className="btn btn-primary btn-lg w-full" disabled={submitting} style={{ marginTop: "8px" }}>
          {submitting ? "Сохранение..." : "Сменить пароль"}
        </button>
      </form>
    </div>
  );
}