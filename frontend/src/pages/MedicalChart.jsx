import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { getAllPages, getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";

const fields = {
  complaints: "Жалобы", chronic_conditions: "Хронические заболевания", allergies: "Аллергии",
  vaccinations: "Вакцинации", medications: "Лекарственные назначения", notes: "Заметки врача",
};
const emptyRecord = { appointment: "", diagnoses: "", surgeries: "", ...Object.fromEntries(Object.keys(fields).map((key) => [key, ""])) };
const names = (items) => Array.isArray(items) ? items.map((item) => item?.name || (typeof item === "string" ? item : "")).filter(Boolean).join("\n") : "";
const asItems = (text) => text.split("\n").map((name) => name.trim()).filter(Boolean).map((name) => ({ name }));

function Attachments({ record, canUpload }) {
  const [files, setFiles] = useState([]);
  const [selection, setSelection] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const { id, attachment_content_type: contentType } = record;

  async function show() {
    setError("");
    try {
      setFiles(await getAllPages("/files/", { content_type: contentType, object_id: id }));
      setLoaded(true);
    } catch (err) { setError(getErrorMessage(err)); }
  }

  async function upload(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const body = new FormData();
    body.append("file", selection);
    body.append("name", selection.name);
    body.append("content_type", contentType);
    body.append("object_id", id);
    try {
      await api.post("/files/", body, { headers: { "Content-Type": "multipart/form-data" } });
      event.target.reset();
      setSelection(null);
      await show();
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setBusy(false); }
  }

  async function download(file) {
    try {
      const { data } = await api.get(`/files/${file.id}/download/`, { responseType: "blob" });
      const url = URL.createObjectURL(data);
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setError("Не удалось скачать вложение."); }
  }

  return <>
    <button type="button" className="btn btn-outline btn-sm" onClick={show}>Вложения</button>
    {loaded && (files.length ? <ul>{files.map((file) => <li key={file.id}><button className="btn btn-outline btn-sm" onClick={() => download(file)}>{file.name}</button></li>)}</ul> : <p>Вложений пока нет.</p>)}
    {loaded && canUpload && <form onSubmit={upload}>
      <label>Добавить вложение<input className="input" type="file" accept=".pdf,.jpg,.jpeg,.png,.dcm,.docx" required onChange={(event) => setSelection(event.target.files[0])} /></label>
      <button className="btn btn-primary btn-sm" disabled={!selection || busy}>Загрузить</button>
    </form>}
    {error && <p role="alert">{error}</p>}
  </>;
}

export default function MedicalChart() {
  const { id } = useParams();
  const { user, role } = useAuth();
  const permitted = ["doctor", "admin", "chief_doctor"].includes(role);
  const [patient, setPatient] = useState(null);
  const [records, setRecords] = useState([]);
  const [visits, setVisits] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState(null);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!permitted) return;
    let active = true;
    setPatient(null);
    setForm(null);
    setError("");
    Promise.all([api.get(`/patients/${id}/`), getAllPages("/medical-records/", { patient: id }), getAllPages("/appointments/", { patient: id })])
      .then(([response, history, appointments]) => {
        if (!active) return;
        setPatient(response.data);
        setRecords(history);
        setVisits(appointments);
      }).catch((err) => { if (active) setError(getErrorMessage(err)); });
    return () => { active = false; };
  }, [id, permitted]);

  function edit(record) {
    setEditing(record);
    setError("");
    setForm(record ? {
      ...Object.fromEntries(Object.keys(fields).map((key) => [key, record[key]])),
      appointment: record.appointment || "", diagnoses: names(record.diagnoses), surgeries: names(record.surgeries),
    } : emptyRecord);
  }

  async function save(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const body = { ...form, patient: Number(id), appointment: form.appointment || null };
    for (const key of ["diagnoses", "surgeries"]) {
      if (editing && form[key] === names(editing[key])) delete body[key];
      else {
        const original = Array.isArray(editing?.[key]) ? editing[key] : [];
        body[key] = asItems(form[key]).map((item) => original.find((previous) => previous?.name === item.name) || item);
      }
    }
    try {
      const { data } = editing
        ? await api.patch(`/medical-records/${editing.id}/`, body)
        : await api.post("/medical-records/", body);
      setRecords((items) => [data, ...items.filter((item) => item.id !== data.id)]);
      setForm(null);
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setSaving(false); }
  }

  if (!permitted) return <div className="page-content">У вашей роли нет доступа к медкартам.</div>;

  return <>
    <div className="page-header"><h1>Медкарта</h1>{patient && <p>{patient.full_name}</p>}</div>
    <div className="page-content">
      {error && <p className="alert alert-error" role="alert">{error}</p>}
      {patient && <>
        <div className="card"><h2>История посещений</h2>
          {visits.length ? <ul>{visits.map((visit) => <li key={visit.id}>{new Date(visit.scheduled_at).toLocaleString("ru-RU")} · {visit.status_display} · {visit.reason || "Приём"}</li>)}</ul> : <p>Приёмов пока нет.</p>}
        </div>
        {(!form && (role !== "doctor" || visits.some((visit) => ["confirmed", "completed"].includes(visit.status)) || records.some((record) => record.created_by === user.id))) && <button className="btn btn-primary" onClick={() => edit(null)}>Добавить запись</button>}
        {form && <form className="card" onSubmit={save}>
          <h2>{editing ? "Редактировать запись" : "Запись о посещении"}</h2>
          <label className="form-group">Приём<select className="input" value={form.appointment} onChange={(event) => setForm({ ...form, appointment: event.target.value })}>
            <option value="">Без привязки</option>{visits.map((visit) => <option key={visit.id} value={visit.id}>{new Date(visit.scheduled_at).toLocaleString("ru-RU")} · {visit.reason || "Приём"}</option>)}
          </select></label>
          {Object.entries({ diagnoses: "Диагнозы, каждый с новой строки", surgeries: "Операции, каждая с новой строки", ...fields }).map(([key, label]) => (
            <label key={key} className="form-group">{label}<textarea className="input" rows={2} value={form[key]} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /></label>
          ))}
          <button className="btn btn-primary" disabled={saving}>Сохранить запись</button>
          <button type="button" className="btn btn-outline" onClick={() => setForm(null)}>Отмена</button>
        </form>}
        {!records.length && <p>Записей в медкарте пока нет.</p>}
        {records.map((record) => {
          const canEdit = role !== "doctor" || record.created_by === user.id;
          return <article className="card" key={record.id}>
            <h2>{new Date(record.created_at).toLocaleDateString("ru-RU")} · {record.author_name || "Запись врача"}</h2>
            {Object.entries({ diagnoses: "Диагнозы", surgeries: "Операции", ...fields }).map(([key, label]) => {
              const content = Array.isArray(record[key]) ? names(record[key]) : record[key];
              return content && <p key={key} style={{ whiteSpace: "pre-wrap" }}><strong>{label}</strong> · {content}</p>;
            })}
            {canEdit && <button className="btn btn-outline btn-sm" onClick={() => edit(record)}>Редактировать</button>}
            <Attachments record={record} canUpload={canEdit} />
          </article>;
        })}
      </>}
    </div>
  </>;
}
