import { useEffect, useState } from "react";
import api, { getAllPages, getErrorMessage } from "../api";
import { useAuth } from "../context/AuthContext";

const emptyType = { name: "", code: "", price: "0", currency: "UZS", turnaround_days: "1", description: "" };
const emptyField = { field_name: "", field_key: "", field_type: "text", unit: "", is_required: true, options: "" };

export default function AnalysisCatalog() {
  const { role } = useAuth();
  const allowed = ["admin", "chief_doctor"].includes(role);
  const [types, setTypes] = useState([]);
  const [form, setForm] = useState(emptyType);
  const [fields, setFields] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (allowed) getAllPages("/analysis-types/").then(setTypes).catch((err) => setError(getErrorMessage(err)));
  }, [allowed]);

  function modifyField(index, key, value) {
    setFields((current) => current.map((field, position) => position === index ? { ...field, [key]: value } : field));
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const { data } = await api.post("/analysis-types/", {
        ...form, fields: fields.map((field, index) => ({
          ...field, sort_order: index,
          options: field.field_type === "choice" ? field.options.split("\n").map((value) => value.trim()).filter(Boolean) : null,
        })),
      });
      setTypes((current) => [...current, data]);
      setForm(emptyType);
      setFields([]);
      setMessage(`${data.name} доступен для назначения пациентам.`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (!allowed) return <div className="page-content">Каталог редактируют главврач и администратор.</div>;

  return <>
    <div className="page-header"><h1>Виды анализов</h1></div>
    <div className="page-content">
      {error && <p role="alert" className="alert alert-error">{error}</p>}
      {message && <p role="status" className="alert alert-success">{message}</p>}
      <form className="card" onSubmit={submit}>
        <h2>Добавить вид анализа</h2>
        <div className="form-row">
          <label className="form-group">Название<input className="input" required maxLength={255} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
          <label className="form-group">Код<input className="input" required maxLength={64} value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} /></label>
        </div>
        <div className="form-row">
          <label className="form-group">Стоимость<input className="input" type="number" min="0" step="0.01" required value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></label>
          <label className="form-group">Валюта<input className="input" required maxLength={8} value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></label>
          <label className="form-group">Срок в днях<input className="input" type="number" min="0" required value={form.turnaround_days} onChange={(e) => setForm({ ...form, turnaround_days: e.target.value })} /></label>
        </div>
        <label className="form-group">Описание<textarea className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        {fields.map((field, index) => <fieldset className="card" key={index}>
          <legend>Показатель</legend>
          <div className="form-row">
            <label className="form-group">Название показателя<input className="input" required value={field.field_name} onChange={(e) => modifyField(index, "field_name", e.target.value)} /></label>
            <label className="form-group">Ключ латиницей<input className="input" required pattern="[a-zA-Z0-9_-]+" value={field.field_key} onChange={(e) => modifyField(index, "field_key", e.target.value)} /></label>
            <label className="form-group">Тип<select className="input" value={field.field_type} onChange={(e) => modifyField(index, "field_type", e.target.value)}>
              <option value="text">Текст</option><option value="numeric">Число</option><option value="choice">Список</option>
            </select></label>
          </div>
          {field.field_type === "numeric" && <div className="form-row">
            <label className="form-group">Единица измерения<input className="input" value={field.unit} onChange={(e) => modifyField(index, "unit", e.target.value)} /></label>
            <label className="form-group">Нижняя граница<input className="input" type="number" step="any" value={field.reference_range_min ?? ""} onChange={(e) => modifyField(index, "reference_range_min", e.target.value === "" ? null : Number(e.target.value))} /></label>
            <label className="form-group">Верхняя граница<input className="input" type="number" step="any" value={field.reference_range_max ?? ""} onChange={(e) => modifyField(index, "reference_range_max", e.target.value === "" ? null : Number(e.target.value))} /></label>
          </div>}
          {field.field_type === "choice" && <label className="form-group">Варианты, каждый с новой строки<textarea className="input" required value={field.options} onChange={(e) => modifyField(index, "options", e.target.value)} /></label>}
          <label><input type="checkbox" checked={field.is_required} onChange={(e) => modifyField(index, "is_required", e.target.checked)} /> Обязательный</label>
          <button type="button" className="btn btn-outline" onClick={() => setFields((current) => current.filter((_, position) => position !== index))}>Удалить показатель</button>
        </fieldset>)}
        <div className="flex-gap">
          <button type="button" className="btn btn-outline" onClick={() => setFields((current) => [...current, { ...emptyField }])}>Добавить показатель</button>
          <button className="btn btn-primary" disabled={saving}>Сохранить вид анализа</button>
        </div>
      </form>
      <div className="card"><h2>Каталог</h2><ul>{types.map((type) => <li key={type.id}>{type.name} · {type.code} · {type.price} {type.currency}</li>)}</ul></div>
    </div>
  </>;
}
