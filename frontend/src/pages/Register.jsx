import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";

const ROLE_OPTIONS = [
  { value: "patient", label: "Пациент" },
  { value: "doctor", label: "Врач" },
  { value: "lab_tech", label: "Лаборант" },
  { value: "registrar", label: "Регистратор" },
];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    first_name: "",
    last_name: "",
    middle_name: "",
    role: "patient",
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.username.trim() || !form.password.trim()) {
      setError("Логин и пароль обязательны");
      return;
    }
    if (form.password !== form.password2) {
      setError("Пароли не совпадают");
      return;
    }
    if (form.password.length < 8) {
      setError("Пароль должен быть не менее 8 символов");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        middle_name: form.middle_name.trim(),
        role: form.role,
      };
      await api.post("/auth/register/", payload);
      const isPatient = form.role === "patient";
      if (isPatient) {
        setSuccess(`Пользователь "${form.username}" успешно создан! Теперь заполните данные пациента.`);
        sessionStorage.setItem("newPatientUser", form.username);
        setTimeout(() => navigate("/patients/new"), 1500);
      } else {
        setSuccess(`Пользователь "${form.username}" успешно создан! Перенаправление на страницу входа...`);
        setTimeout(() => navigate("/login"), 2000);
      }
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const messages = Object.entries(data)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val[0] : val}`)
          .join("; ");
        setError(messages);
      } else {
        setError("Ошибка регистрации. Возможно, логин уже занят.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div style={{ width: "100%", maxWidth: "520px" }}>
        <div className="auth-card">
          <div className="auth-header">
            <h1>HCMS</h1>
            <p>Регистрация нового пользователя</p>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Фамилия</label>
                <input className="input" name="last_name" value={form.last_name} onChange={handleChange} placeholder="Иванов" />
              </div>
              <div className="form-group">
                <label>Имя</label>
                <input className="input" name="first_name" value={form.first_name} onChange={handleChange} placeholder="Иван" />
              </div>
            </div>

            <div className="form-group">
              <label>Отчество</label>
              <input className="input" name="middle_name" value={form.middle_name} onChange={handleChange} placeholder="Иванович" />
            </div>

            <div className="form-group">
              <label>Логин *</label>
              <input className="input" name="username" value={form.username} onChange={handleChange} placeholder="Введите логин" required autoFocus />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input className="input" type="email" name="email" value={form.email} onChange={handleChange} placeholder="email@example.com" />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Пароль *</label>
                <input className="input" type="password" name="password" value={form.password} onChange={handleChange} placeholder="Не менее 8 символов" required />
              </div>
              <div className="form-group">
                <label>Повторите пароль *</label>
                <input className="input" type="password" name="password2" value={form.password2} onChange={handleChange} placeholder="Повторите пароль" required />
              </div>
            </div>

            <div className="form-group">
              <label>Роль</label>
              <select className="input" name="role" value={form.role} onChange={handleChange}>
                {ROLE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <p className="form-hint">Роль "Администратор" и "Главный врач" назначаются только администратором системы</p>
            </div>

            <button type="submit" className="btn btn-primary btn-lg w-full" disabled={submitting} style={{ marginTop: "8px" }}>
              {submitting ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>

          <div className="auth-footer">
            Уже есть аккаунт?{" "}
            <Link to="/login">Войти</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
