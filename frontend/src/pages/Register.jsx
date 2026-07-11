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
      const res = await api.post("/auth/register/", payload);
      const isPatient = form.role === "patient";
      if (isPatient) {
        setSuccess(`Пользователь "${form.username}" успешно создан! Теперь заполните данные пациента.`);
        // Сохраняем username в sessionStorage, чтобы PatientForm знал, для кого создавать
        sessionStorage.setItem("newPatientUser", form.username);
        setTimeout(() => navigate("/patients/new"), 1500);
      } else {
        setSuccess(`Пользователь "${form.username}" успешно создан! Сейчас вы будете перенаправлены на страницу входа.`);
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
      <div style={{ width: "100%", maxWidth: "480px" }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1 style={{ fontSize: "40px", fontWeight: 900, letterSpacing: "-2px", lineHeight: 1 }}>
            HCMS
          </h1>
          <p style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-secondary)", marginTop: "4px", textTransform: "uppercase", letterSpacing: "1px" }}>
            Регистрация нового пользователя
          </p>
        </div>

        <div className="card" style={{ padding: "32px" }}>
          <h2 style={{ fontSize: "16px", fontWeight: 800, marginBottom: "24px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Создать учётную запись
          </h2>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

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
              <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                Роль "Администратор" и "Главный врач" назначаются только администратором системы
              </p>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" disabled={submitting} style={{ width: "100%", marginTop: "8px" }}>
              {submitting ? "Регистрация..." : "📝 Зарегистрироваться"}
            </button>
          </form>

          <div style={{ textAlign: "center", marginTop: "20px" }}>
            <span style={{ fontSize: "14px", color: "var(--text-secondary)" }}>
              Уже есть аккаунт?{" "}
            </span>
            <Link to="/login" style={{ fontWeight: 700, textDecoration: "underline" }}>
              Войти
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}