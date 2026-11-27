import { useEffect, useState } from "react";
import api, { getAllPages, getErrorMessage } from "../api";

function serializeCsv(rows) {
  return rows.map((row) => row.map((value) => {
    const text = String(value ?? "");
    const safe = /^[\s]*[=+@-]/.test(text) ? "'" + text : text;
    return '"' + safe.replaceAll('"', '""') + '"';
  }).join(",")).join("\r\n");
}

export default function Reports() {
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  const [message, setMessage] = useState(null);

  const [period, setPeriod] = useState({ start: "", end: "" });
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [patientSearch, setPatientSearch] = useState("");
  const [summary, setSummary] = useState(null);
  const [summaryError, setSummaryError] = useState("");
  const [doctor, setDoctor] = useState("");

  async function loadSummary(event) {
    event?.preventDefault();
    setSummaryError("");
    const params = Object.fromEntries(Object.entries(period).filter(([, value]) => value));
    try {
      const [patients, analyses, daily, doctors, hospitals] = await Promise.all(
        ["patients", "analyses", "daily", "doctors", "hospitals"].map((part) => api.get(`/stats/${part}/`, { params })),
      );
      setSummary({ patients: patients.data, analyses: analyses.data, daily: daily.data, doctors: doctors.data, hospitals: hospitals.data });
    } catch (err) { setSummaryError(getErrorMessage(err)); }
  }

  useEffect(() => { loadSummary(); }, []);

  async function downloadReport(path, filename) {
    setMessage(null);
    try {
      const { data } = await api.get(path, { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setMessage({ type: "error", text: "Не удалось скачать отчёт." }); }
  }

  const exportPatients = async () => {
    setLoadingPatients(true); setMessage(null);
    try {
      const patients = await getAllPages("/patients/", { search: patientSearch });
      const csv = serializeCsv([
        ["ID", "ФИО", "Дата рождения", "Телефон", "ПИНФЛ", "Паспорт", "Email"],
        ...patients.map((p) => [p.id, p.full_name, p.birth_date, p.phone, p.pinfl, p.passport, p.email]),
      ]);
      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `patients_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: "Отчёт по пациентам скачан" });
    } catch { setMessage({ type: "error", text: "Ошибка выгрузки" }); }
    finally { setLoadingPatients(false); }
  };

  const exportAnalyses = async () => {
    setLoadingAnalyses(true); setMessage(null);
    try {
      const orders = await getAllPages("/analysis-orders/", {
        status: analysisStatus || undefined, requested_at__date__gte: period.start || undefined,
        requested_at__date__lte: period.end || undefined,
      });
      const csv = serializeCsv([
        ["ID", "Пациент", "Анализ", "Статус", "Назначен", "Результат"],
        ...orders.map((o) => [o.id, o.patient_name || o.patient?.full_name || o.patient,
          o.analysis_type_name || o.analysis_type?.name || o.analysis_type, o.status,
          o.requested_at?.slice(0, 10), o.result]),
      ]);
      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `analyses_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: "Отчёт по анализам скачан" });
    } catch { setMessage({ type: "error", text: "Ошибка выгрузки" }); }
    finally { setLoadingAnalyses(false); }
  };

  return (
    <div>
      <div className="page-header"><h1>Отчёты</h1><p>Экспорт данных и статистика</p></div>
      <div className="page-content">
        {message && (<div className={`alert ${message.type === "success" ? "alert-success" : "alert-error"}`}>{message.text}</div>)}
        <form className="card" onSubmit={loadSummary}>
          <h2>Период для анализов и приёмов</h2>
          <div className="form-row">
            <label className="form-group">С<input className="input" type="date" value={period.start} onChange={(e) => setPeriod({ ...period, start: e.target.value })} /></label>
            <label className="form-group">По<input className="input" type="date" min={period.start || undefined} value={period.end} onChange={(e) => setPeriod({ ...period, end: e.target.value })} /></label>
          </div>
          <button className="btn btn-primary">Обновить сводку</button>
        </form>
        {summaryError && <p role="alert" className="alert alert-error">{summaryError}</p>}
        {summary && <div className="grid-2">
          <section className="card"><h2>Сводка</h2>
            <p>Пациентов всего: {summary.patients.total}</p><p>Анализов за период: {summary.analyses.total}</p>
            <p>Учреждений: {summary.hospitals.total_hospitals}, отделений: {summary.hospitals.total_departments}</p>
            <h3>Приёмы по дням</h3>
            {summary.daily.length ? <ul>{summary.daily.slice(0, 14).map((day) => <li key={day.date}>{day.date} · {day.count}</li>)}</ul> : <p>Приёмов за период нет.</p>}
          </section>
          <section className="card"><h2>Нагрузка врачей</h2>
            <ul>{summary.doctors.map((item) => <li key={item.doctor_id ?? "unassigned"}>{[item.doctor__last_name, item.doctor__first_name].filter(Boolean).join(" ") || "Без врача"} · {item.appointment_count}</li>)}</ul>
            <label className="form-group">Расписание конкретного врача<select className="input" value={doctor} onChange={(e) => setDoctor(e.target.value)}><option value="">Выберите врача</option>
              {summary.doctors.filter((item) => item.doctor_id).map((item) => <option key={item.doctor_id} value={item.doctor_id}>{item.doctor__last_name} {item.doctor__first_name}</option>)}
            </select></label>
            <button className="btn btn-outline" disabled={!doctor} onClick={() => downloadReport(`/reports/schedule/${doctor}/pdf/`, "schedule.pdf")}>Расписание PDF</button>
          </section>
        </div>}
        <div className="grid-2">
          <div className="card card-hover">
            <div className="stat-card-icon" style={{ backgroundColor: "#2563eb15", color: "#2563eb" }}>👤</div>
            <h3 className="card-title" style={{ marginBottom: "12px" }}>Список пациентов</h3>
            <label className="form-group">Поиск пациентов для CSV<input className="input" value={patientSearch} onChange={(e) => setPatientSearch(e.target.value)} /></label>
            <button className="btn btn-outline" onClick={() => downloadReport("/reports/patients/pdf/", "patients.pdf")}>Все пациенты PDF</button>
            <button className="btn btn-outline" onClick={() => downloadReport("/reports/patients/excel/", "patients.xlsx")}>Все пациенты Excel</button>
            <button className="btn btn-primary" onClick={exportPatients} disabled={loadingPatients}>{loadingPatients ? "Загрузка..." : "Скачать CSV"}</button>
          </div>
          <div className="card card-hover">
            <div className="stat-card-icon" style={{ backgroundColor: "#7c3aed15", color: "#7c3aed" }}>🔬</div>
            <h3 className="card-title" style={{ marginBottom: "12px" }}>Результаты анализов</h3>
            <label className="form-group">Статус для CSV<select className="input" value={analysisStatus} onChange={(e) => setAnalysisStatus(e.target.value)}>
              <option value="">Все статусы</option><option value="created">Создан</option><option value="ordered">Назначен</option>
              <option value="in_progress">В работе</option><option value="completed">Готов</option>
              <option value="verified">Проверен</option><option value="sent">Отправлен</option>
            </select></label>
            <button className="btn btn-outline" onClick={() => downloadReport("/reports/analyses/pdf/", "analyses.pdf")}>Все анализы PDF</button>
            <button className="btn btn-primary" onClick={exportAnalyses} disabled={loadingAnalyses}>{loadingAnalyses ? "Загрузка..." : "Скачать CSV"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
