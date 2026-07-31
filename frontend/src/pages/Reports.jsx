import { useState } from "react";
import api from "../api";

export default function Reports() {
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchAllPages = async (url, params = {}) => {
    let aggregated = [];
    let nextUrl = url;
    let query = { ...params };
    while (nextUrl) {
      const res = await api.get(nextUrl, { params: query });
      const data = res.data;
      const pageResults = data.results || data;
      aggregated.push(...pageResults);
      nextUrl = data.next;
      query = {};
    }
    return aggregated;
  };

  const exportPatients = async () => {
    setLoadingPatients(true); setMessage(null);
    try {
      const patients = await fetchAllPages("/patients/");
      const csv = ["ID,ФИО,Дата рождения,Телефон,ПИНФЛ,Паспорт,Email", ...patients.map((p) => [p.id, p.full_name || "", p.birth_date || "", p.phone || "", p.pinfl || "", p.passport || "", p.email || ""].join(","))].join("\n");
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
      const orders = await fetchAllPages("/analysis-orders/");
      const csv = ["ID,Пациент,Анализ,Статус,Назначен,Результат", ...orders.map((o) => [o.id, o.patient_name || o.patient?.full_name || o.patient || "", o.analysis_type_name || o.analysis_type?.name || o.analysis_type || "", o.status || "", o.requested_at?.slice(0, 10) || "", (o.result || "").replace(/,/g, ";")].join(","))].join("\n");
      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `analyses_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: "Отчёт по анализам скачан" });
    } catch { setMessage({ type: "error", text: "Ошибка выгрузки" }); }
    finally { setLoadingAnalyses(false); }
  };

  const downloadReport = async (url, filename) => {
    setLoadingPatients(false); setLoadingAnalyses(false); setMessage(null);
    try {
      const res = await api.get(url, { responseType: "blob" });
      const blob = new Blob([res.data], { type: res.headers["content-type"] });
      const urlObj = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = urlObj; a.download = filename; a.click();
      URL.revokeObjectURL(urlObj);
      setMessage({ type: "success", text: `Отчёт ${filename} скачан` });
    } catch { setMessage({ type: "error", text: "Ошибка выгрузки отчёта" }); }
  };

  return (
    <div>
      <div className="page-header"><h1>Отчёты</h1><p>Экспорт данных и статистика</p></div>
      <div className="page-content">
        {message && (<div className={`alert ${message.type === "success" ? "alert-success" : "alert-error"}`}>{message.text}</div>)}
        <div className="grid-2">
          <div className="card card-hover">
            <div className="stat-card-icon" style={{ backgroundColor: "#2563eb15", color: "#2563eb" }}>👤</div>
            <h3 className="card-title" style={{ marginBottom: "12px" }}>Список пациентов</h3>
            <p className="text-muted text-sm" style={{ marginBottom: "16px" }}>Экспорт в PDF, Excel или CSV</p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={() => downloadReport("/reports/patients/pdf/", `patients_${new Date().toISOString().slice(0,10)}.pdf`)} disabled={loadingPatients}>{loadingPatients ? "Загрузка..." : "PDF"}</button>
              <button className="btn btn-primary" onClick={() => downloadReport("/reports/patients/excel/", `patients_${new Date().toISOString().slice(0,10)}.xlsx`)} disabled={loadingPatients}>{loadingPatients ? "Загрузка..." : "Excel"}</button>
              <button className="btn btn-outline" onClick={exportPatients}>{loadingPatients ? "Загрузка..." : "CSV"}</button>
            </div>
          </div>
          <div className="card card-hover">
            <div className="stat-card-icon" style={{ backgroundColor: "#7c3aed15", color: "#7c3aed" }}>🔬</div>
            <h3 className="card-title" style={{ marginBottom: "12px" }}>Результаты анализов</h3>
            <p className="text-muted text-sm" style={{ marginBottom: "16px" }}>Экспорт в PDF или CSV</p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={() => downloadReport("/reports/analyses/pdf/", `analyses_${new Date().toISOString().slice(0,10)}.pdf`)} disabled={loadingAnalyses}>{loadingAnalyses ? "Загрузка..." : "PDF"}</button>
              <button className="btn btn-outline" onClick={exportAnalyses}>{loadingAnalyses ? "Загрузка..." : "CSV"}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
