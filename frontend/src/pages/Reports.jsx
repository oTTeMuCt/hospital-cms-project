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
    setLoadingPatients(true);
    setMessage(null);
    try {
      const patients = await fetchAllPages("/patients/");
      const csv = [
        "ID,ФИО,Дата рождения,Телефон,ПИНФЛ,Паспорт,Email",
        ...patients.map((p) =>
          [p.id, p.full_name || "", p.birth_date || "", p.phone || "", p.pinfl || "", p.passport || "", p.email || ""].join(",")
        ),
      ].join("\n");

      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `patients_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: "✅ Отчёт по пациентам скачан" });
    } catch {
      setMessage({ type: "error", text: "Ошибка выгрузки" });
    } finally {
      setLoadingPatients(false);
    }
  };

  const exportAnalyses = async () => {
    setLoadingAnalyses(true);
    setMessage(null);
    try {
      const orders = await fetchAllPages("/analysis-orders/");
      const csv = [
        "ID,Пациент,Анализ,Статус,Назначен,Результат",
        ...orders.map((o) =>
          [
            o.id,
            o.patient_name || o.patient?.full_name || o.patient || "",
            o.analysis_type_name || o.analysis_type?.name || o.analysis_type || "",
            o.status || "",
            o.requested_at?.slice(0, 10) || "",
            (o.result || "").replace(/,/g, ";"),
          ].join(",")
        ),
      ].join("\n");

      const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analyses_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      setMessage({ type: "success", text: "✅ Отчёт по анализам скачан" });
    } catch {
      setMessage({ type: "error", text: "Ошибка выгрузки" });
    } finally {
      setLoadingAnalyses(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>📈 Отчёты</h1>
        <p>Экспорт данных и статистика</p>
      </div>

      <div className="page-content">
        {message && (
          <div className={message.type === "success" ? "success-message" : "error-message"}>
            {message.text}
          </div>
        )}

        <div className="grid-2">
          <div className="card card-hover">
            <div className="stat-card-icon">👤</div>
            <h3 className="card-title mb-4">Список пациентов</h3>
            <p className="text-muted text-sm mb-4">Экспорт всех зарегистрированных пациентов в CSV</p>
            <button className="btn btn-primary" onClick={exportPatients} disabled={loadingPatients}>
              {loadingPatients ? "Загрузка..." : "📥 Скачать CSV"}
            </button>
          </div>

          <div className="card card-hover">
            <div className="stat-card-icon">🔬</div>
            <h3 className="card-title mb-4">Результаты анализов</h3>
            <p className="text-muted text-sm mb-4">Экспорт всех назначенных анализов в CSV</p>
            <button className="btn btn-primary" onClick={exportAnalyses} disabled={loadingAnalyses}>
              {loadingAnalyses ? "Загрузка..." : "📥 Скачать CSV"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}