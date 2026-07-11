import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api";

export default function PatientForm() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    birth_date: "",
    gender: "",
    blood_group: "",
    pinfl: "",
    passport: "",
    phone: "",
    email: "",
    address: "",
    emergency_contact: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Если есть username нового пациента из регистрации — подставляем ФИО из User
  useEffect(() => {
    const newUser = sessionStorage.getItem("newPatientUser");
    if (newUser) {
      setForm((prev) => ({
        ...prev,
        full_name: `${user?.last_name || ""} ${user?.first_name || ""} ${user?.middle_name || ""}`.trim() || newUser,
        phone: user?.email || "",
        email: user?.email || "",
      }));
    }
  }, [user]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.full_name.trim()) {
      setError("ФИО обязательно для заполнения");
      return;
    }

    setSaving(true);
    try {
      const payload = { ...form };
      // Если есть новый пациент из регистрации — привязываем
      const newUser = sessionStorage.getItem("newPatientUser");
      if (newUser) {
        // Ищем user_id по username (регистратор создал пользователя, теперь создаём карточку)
        try {
          const usersRes = await api.get("/users/");
          const users = usersRes.data.results || usersRes.data;
          const matchedUser = users.find((u) => u.username === newUser);
          if (matchedUser) {
            payload.user = matchedUser.id;
          }
        } catch {
          // Если не нашли — ничего страшного, пациент создастся без user
        }
      }
      // Если авторизован пациент и не указан user
      if (!payload.user && user?.role === "patient") {
        payload.user = user.id;
      }

      const res = await api.post("/patients/", payload);
      setSuccess(`Пациент "${res.data.full_name}" успешно зарегистрирован!`);
      sessionStorage.removeItem("newPatientUser");

      setForm({
        full_name: "",
        birth_date: "",
        gender: "",
        blood_group: "",
        pinfl: "",
        passport: "",
        phone: "",
        email: "",
        address: "",
        emergency_contact: "",
      });

      // Если пациент сам себя регистрирует — идём на дашборд
      if (user?.role === "patient" || newUser) {
        setTimeout(() => navigate("/"), 1500);
      } else {
        setTimeout(() => navigate("/patients"), 1500);
      }
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const messages = Object.entries(data)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val[0] : val}`)
          .join("; ");
        setError(messages);
      } else {
        setError("Ошибка при сохранении");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>➕ Регистрация пациента</h1>
        <p>Заполните форму для создания карточки пациента</p>
      </div>

      <div className="page-content" style={{ maxWidth: "800px" }}>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>ФИО *</label>
              <input className="input" name="full_name" value={form.full_name} onChange={handleChange} placeholder="Иванов Иван Иванович" required />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Дата рождения</label>
                <input className="input" type="date" name="birth_date" value={form.birth_date} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Пол</label>
                <select className="input" name="gender" value={form.gender} onChange={handleChange}>
                  <option value="">Не указан</option>
                  <option value="male">Мужской</option>
                  <option value="female">Женский</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>ПИНФЛ</label>
                <input className="input" name="pinfl" value={form.pinfl} onChange={handleChange} placeholder="14 цифр" maxLength={14} />
              </div>
              <div className="form-group">
                <label>Паспорт</label>
                <input className="input" name="passport" value={form.passport} onChange={handleChange} placeholder="AB1234567" />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Телефон</label>
                <input className="input" type="tel" name="phone" value={form.phone} onChange={handleChange} placeholder="+998 XX XXX XX XX" />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input className="input" type="email" name="email" value={form.email} onChange={handleChange} placeholder="email@example.com" />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Группа крови</label>
                <select className="input" name="blood_group" value={form.blood_group} onChange={handleChange}>
                  <option value="">Не указана</option>
                  <option value="I+">I+</option>
                  <option value="I-">I-</option>
                  <option value="II+">II+</option>
                  <option value="II-">II-</option>
                  <option value="III+">III+</option>
                  <option value="III-">III-</option>
                  <option value="IV+">IV+</option>
                  <option value="IV-">IV-</option>
                </select>
              </div>
              <div className="form-group">
                <label>Экстренный контакт</label>
                <input className="input" name="emergency_contact" value={form.emergency_contact} onChange={handleChange} placeholder="ФИО и телефон" />
              </div>
            </div>

            <div className="form-group">
              <label>Адрес регистрации</label>
              <input className="input" name="address" value={form.address} onChange={handleChange} placeholder="Город, улица, дом" />
            </div>

            <div className="flex flex-gap mt-4">
              <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
                {saving ? "Сохранение..." : "💾 Зарегистрировать"}
              </button>
              <button type="button" className="btn btn-outline btn-lg" onClick={() => navigate("/patients")}>
                Отмена
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}