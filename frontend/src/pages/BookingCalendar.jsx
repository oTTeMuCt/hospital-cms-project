import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api, { getAllPages, getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";

const clinicTime = new Intl.DateTimeFormat("ru-RU", { timeZone: "Asia/Tashkent", hour: "2-digit", minute: "2-digit" });
const clinicDateTime = new Intl.DateTimeFormat("ru-RU", { timeZone: "Asia/Tashkent", dateStyle: "short", timeStyle: "short" });
const canReschedule = (role) => ["admin", "chief_doctor", "registrar"].includes(role);
const activeStatuses = ["pending", "confirmed"];

export default function BookingCalendar() {
  const { user, role } = useAuth();
  const [params, setParams] = useSearchParams();
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [doctor, setDoctor] = useState("");
  const [patient, setPatient] = useState("");
  const [date, setDate] = useState(() => new Date().toLocaleDateString("sv-SE", { timeZone: "Asia/Tashkent" }));
  const [slot, setSlot] = useState("");
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const isPatient = role === "patient";
  const allowed = isPatient || canReschedule(role) || role === "doctor";
  const movingId = canReschedule(role) ? params.get("move") : null;
  const moving = appointments.find((item) => String(item.id) === movingId && activeStatuses.includes(item.status));

  useEffect(() => {
    if (!allowed) return;
    let active = true;
    Promise.all([
      api.get("/booking-doctors/"),
      isPatient ? api.get("/patients/me/") : getAllPages("/patients/"),
      getAllPages("/appointments/"),
    ]).then(([doctorResponse, patientResponse, visits]) => {
      if (!active) return;
      setDoctors(doctorResponse.data);
      setPatients(isPatient ? [patientResponse.data] : patientResponse);
      setAppointments(visits);
      if (isPatient) setPatient(String(patientResponse.data.id));
      if (role === "doctor") setDoctor(String(user.id));
    }).catch((err) => { if (active) setError(getErrorMessage(err)); });
    return () => { active = false; };
  }, [allowed, isPatient, role, user.id]);

  useEffect(() => {
    if (moving) {
      setDoctor(String(moving.doctor || ""));
      setPatient(String(moving.patient));
    }
  }, [moving]);

  useEffect(() => {
    let active = true;
    setSlot("");
    setSlots([]);
    setLoadingSlots(Boolean(doctor && date));
    if (doctor && date) api.get("/available-slots/", { params: { doctor, date } })
      .then(({ data }) => { if (active) setSlots(data); })
      .catch((err) => { if (active) setError(getErrorMessage(err)); })
      .finally(() => { if (active) setLoadingSlots(false); });
    return () => { active = false; };
  }, [doctor, date, appointments]);

  async function book(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setSaving(true);
    const chosen = slots.find((item) => item.start === slot);
    try {
      if (!chosen || (movingId && !moving)) return;
      const timing = { doctor, scheduled_at: chosen.start, end_time: chosen.end };
      const { data } = moving
        ? await api.patch(`/appointments/${moving.id}/`, timing)
        : await api.post("/appointments/", { ...timing, patient, reason });
      setAppointments((current) => [data, ...current.filter((item) => item.id !== data.id)]);
      setMessage(moving ? "Приём перенесён." : "Запись создана и ожидает подтверждения.");
      setReason("");
      if (moving) setParams({});
    } catch (err) {
      const data = err.response?.data;
      setError(Array.isArray(data) ? data.join(" ") : getErrorMessage(err));
    } finally { setSaving(false); }
  }

  async function cancel(appointment) {
    if (!window.confirm("Отменить эту запись?")) return;
    setError("");
    setMessage("");
    try {
      const { data } = await api.patch(`/appointments/${appointment.id}/`, { status: "cancelled" });
      setAppointments((current) => current.map((item) => item.id === data.id ? data : item));
      setMessage("Запись отменена.");
    } catch (err) { setError(getErrorMessage(err)); }
  }

  if (!allowed) return <div className="page-content">У вашей роли нет доступа к записи на приём.</div>;

  const visible = isPatient ? appointments : appointments.filter((item) => {
    const day = new Date(item.scheduled_at).toLocaleDateString("sv-SE", { timeZone: "Asia/Tashkent" });
    return day === date && (!doctor || Number(doctor) === item.doctor);
  });
  return <>
    <div className="page-header"><h1>{isPatient ? "Мои приёмы" : "Календарь приёмов"}</h1><p>Время клиники · Ташкент</p></div>
    <div className="page-content">
      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {message && <p className="alert alert-success" role="status">{message}</p>}
      <form className="card" onSubmit={book}>
        <h2>{moving ? "Перенести приём" : "Выбрать свободное время"}</h2>
        {movingId && !moving && <p>Эта запись недоступна для переноса.</p>}
        <div className="form-row">
          {!isPatient && <label className="form-group">Пациент<select className="input" value={patient} onChange={(e) => setPatient(e.target.value)} disabled={Boolean(moving)} required>
            <option value="">Выберите пациента</option>{patients.map((item) => <option key={item.id} value={item.id}>{item.full_name}</option>)}
          </select></label>}
          <label className="form-group">Врач<select className="input" value={doctor} onChange={(e) => {setError(""); setDoctor(e.target.value);}} required disabled={role === "doctor"}>
            <option value="">Выберите врача</option>{doctors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label className="form-group">Дата<input className="input" type="date" value={date} onChange={(e) => {setError(""); setDate(e.target.value);}} required /></label>
          <label className="form-group">Время<select className="input" value={slot} onChange={(e) => setSlot(e.target.value)} required>
            <option value="">Выберите время</option>{slots.map((item) => <option key={item.start} value={item.start}>{clinicTime.format(new Date(item.start))}</option>)}
          </select></label>
        </div>
        {doctor && date && !slots.length && <p>{loadingSlots ? "Загрузка свободного времени…" : "На эту дату свободного времени нет или график врача не задан."}</p>}
        {!moving && <label className="form-group">Причина обращения<input className="input" maxLength={512} value={reason} onChange={(e) => setReason(e.target.value)} /></label>}
        <button className="btn btn-primary" disabled={saving || !slot || !patient || Boolean(movingId && !moving)}>{moving ? "Подтвердить перенос" : "Записаться"}</button>
        {movingId && <button className="btn btn-outline" type="button" onClick={() => setParams({})}>Отмена переноса</button>}
      </form>
      <div className="card"><h2>{isPatient ? "Мои записи" : "Записи на выбранную дату"}</h2>
        {!visible.length && <p>Записей нет.</p>}
        <ul>{visible.map((item) => <li key={item.id}>
          {clinicDateTime.format(new Date(item.scheduled_at))} · {isPatient ? item.doctor_name || "Врач не назначен" : item.patient_name} · {item.status_display}
          {isPatient && activeStatuses.includes(item.status) && <button className="btn btn-outline btn-sm" onClick={() => cancel(item)}>Отменить</button>}
          {canReschedule(role) && activeStatuses.includes(item.status) && <Link className="btn btn-outline btn-sm" to={`?move=${item.id}`}>Перенести</Link>}
        </li>)}</ul>
      </div>
    </div>
  </>;
}
