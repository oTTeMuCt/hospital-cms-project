import { useEffect, useState } from "react";
import api, { getAllPages, getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";

const roles = { chief_doctor: "Главврач", doctor: "Врач", lab_tech: "Лаборант", registrar: "Регистратор" };
const weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];
const emptyAccount = { username: "", password: "", first_name: "", last_name: "", email: "",
  role: "doctor", position: "", phone: "", hospital: "", department: "" };

function Schedules() {
  const [doctors, setDoctors] = useState([]);
  const [doctor, setDoctor] = useState("");
  const [hours, setHours] = useState([]);
  const [editing, setEditing] = useState(null);
  const [weekday, setWeekday] = useState("0");
  const [startsAt, setStartsAt] = useState("09:00");
  const [endsAt, setEndsAt] = useState("17:00");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/booking-doctors/").then(({ data }) => setDoctors(data)).catch((err) => setError(getErrorMessage(err)));
  }, []);
  useEffect(() => {
    let active = true;
    setHours([]);
    setEditing(null);
    setError("");
    if (doctor) getAllPages("/doctor-work-hours/", { doctor }).then((data) => {
      if (active) setHours(data);
    }).catch((err) => { if (active) setError(getErrorMessage(err)); });
    return () => { active = false; };
  }, [doctor]);

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const payload = { doctor, weekday, starts_at: startsAt, ends_at: endsAt };
    try {
      const { data } = editing
        ? await api.patch(`/doctor-work-hours/${editing}/`, payload)
        : await api.post("/doctor-work-hours/", payload);
      setHours((items) => [...items.filter((item) => item.id !== data.id), data].sort((a, b) => a.weekday - b.weekday));
      setEditing(null);
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setBusy(false); }
  }

  async function remove(item) {
    if (!window.confirm("Удалить рабочий день из расписания?")) return;
    try {
      await api.delete(`/doctor-work-hours/${item.id}/`);
      setHours((items) => items.filter((entry) => entry.id !== item.id));
      if (editing === item.id) setEditing(null);
    } catch (err) { setError(getErrorMessage(err)); }
  }

  return <section className="card">
    <h2>Рабочий график врачей</h2><p>Дни и часы по времени Ташкента. Календарь предлагает свободные интервалы по 30 минут.</p>
    {error && <p role="alert" className="alert alert-error">{error}</p>}
    <label className="form-group">Выберите врача<select className="input" value={doctor} onChange={(e) => setDoctor(e.target.value)} disabled={busy}>
      <option value="">Врач</option>{doctors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></label>
    {doctor && <>
      <ul>{hours.map((item) => <li key={item.id}>
        {weekdays[item.weekday]} · {item.starts_at.slice(0, 5)}–{item.ends_at.slice(0, 5)}
        <button className="btn btn-outline btn-sm" disabled={busy} onClick={() => {
          setEditing(item.id); setWeekday(String(item.weekday)); setStartsAt(item.starts_at.slice(0, 5)); setEndsAt(item.ends_at.slice(0, 5));
        }}>Изменить</button>
        <button className="btn btn-outline btn-sm" disabled={busy} onClick={() => remove(item)}>Удалить день</button>
      </li>)}</ul>
      <form onSubmit={save}>
        <div className="form-row">
          <label className="form-group">День<select className="input" value={weekday} onChange={(e) => setWeekday(e.target.value)}>
            {weekdays.map((day, index) => <option key={day} value={index}>{day}</option>)}
          </select></label>
          <label className="form-group">Начало<input className="input" type="time" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} required /></label>
          <label className="form-group">Окончание<input className="input" type="time" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} required /></label>
        </div>
        <button className="btn btn-primary" disabled={busy}>{editing ? "Сохранить часы" : "Добавить рабочий день"}</button>
        {editing && <button className="btn btn-outline" type="button" onClick={() => setEditing(null)}>Отмена</button>}
      </form>
    </>}
  </section>;
}

export default function Staff() {
  const { role } = useAuth();
  const canManage = ["admin", "chief_doctor"].includes(role);
  const [staff, setStaff] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState(null);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (!canManage) return;
    Promise.all([getAllPages("/staff/"), getAllPages("/hospitals/"), getAllPages("/departments/")]).then(([people, places, units]) => {
      setStaff(people); setHospitals(places); setDepartments(units);
    }).catch((err) => setError(getErrorMessage(err)));
  }, [canManage]);

  async function save(event) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = { ...form, hospital: form.hospital || null, department: form.department || null };
      const { data } = editing
        ? await api.patch(`/staff/${editing}/`, payload)
        : await api.post("/staff/create-account/", payload);
      setStaff((items) => [...items.filter((item) => item.id !== data.id), data]);
      setForm(null);
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setSaving(false); }
  }

  if (!canManage) return <div className="page-content">У вашей роли нет доступа к этому разделу.</div>;
  return <>
    <div className="page-header"><h1>Сотрудники</h1></div>
    <div className="page-content">
      {error && <p role="alert" className="alert alert-error">{error}</p>}
      {role === "admin" && !form && <button className="btn btn-primary" onClick={() => {setEditing(null); setForm(emptyAccount);}}>Добавить сотрудника</button>}
      {form && <form className="card" onSubmit={save}>
        <h2>{editing ? "Карточка сотрудника" : "Новый сотрудник"}</h2>
        {!editing && <>
          <div className="form-row">
            {Object.entries({ username: "Логин", first_name: "Имя", last_name: "Фамилия", email: "Почта" }).map(([field, label]) => <label key={field} className="form-group">{label}
              <input className="input" type={field === "email" ? "email" : "text"} value={form[field]} required={field !== "email"} onChange={(e) => setForm({ ...form, [field]: e.target.value })} />
            </label>)}
          </div>
          <div className="form-row">
            <label className="form-group">Пароль<input className="input" type="password" autoComplete="new-password" minLength={8} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
            <label className="form-group">Роль<select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {Object.entries(roles).map(([key, name]) => <option key={key} value={key}>{name}</option>)}
            </select></label>
          </div>
        </>}
        <div className="form-row">
          <label className="form-group">Должность<input className="input" value={form.position} required onChange={(e) => setForm({ ...form, position: e.target.value })} /></label>
          <label className="form-group">Телефон<input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
        </div>
        <div className="form-row">
          <label className="form-group">Больница<select className="input" value={form.hospital} onChange={(e) => setForm({ ...form, hospital: e.target.value, department: "" })}>
            <option value="">Не выбрана</option>{hospitals.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label className="form-group">Отделение<select className="input" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}>
            <option value="">Не выбрано</option>{departments.filter((item) => String(item.hospital) === String(form.hospital)).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
        </div>
        <button className="btn btn-primary" disabled={saving}>Сохранить сотрудника</button>
        <button className="btn btn-outline" type="button" onClick={() => setForm(null)}>Отмена</button>
      </form>}
      <div className="table-wrap"><table>
        <thead><tr><th>Сотрудник</th><th>Роль</th><th>Должность</th><th>Больница</th><th>Отделение</th><th>Телефон</th><th>Действия</th></tr></thead>
        <tbody>{staff.map((item) => <tr key={item.id}>
          <td>{item.user_full_name}</td><td>{roles[item.role] || item.role}</td><td>{item.position}</td>
          <td>{hospitals.find((place) => place.id === item.hospital)?.name || "—"}</td><td>{departments.find((unit) => unit.id === item.department)?.name || "—"}</td><td>{item.phone || "—"}</td>
          <td><button className="btn btn-outline btn-sm" onClick={() => {
            setEditing(item.id);
            setForm({ position: item.position, phone: item.phone, hospital: item.hospital || "", department: item.department || "" });
          }}>Редактировать</button></td>
        </tr>)}</tbody>
      </table></div>
      <Schedules />
    </div>
  </>;
}
