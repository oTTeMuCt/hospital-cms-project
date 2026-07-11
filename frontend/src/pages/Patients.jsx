import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const params = search ? { search } : {};
        const res = await api.get("/patients/", { params });
        setPatients(res.data.results || res.data);
      } catch {
        setError("Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [search]);

  const handleDelete = async (id) => {
    if (!window.confirm("Удалить пациента?")) return;
    try {
      await api.delete(`/patients/${id}/`);
      setPatients(patients.filter((p) => p.id !== id));
    } catch {
      setError("Ошибка удаления");
    }
  };

  if (loading) return <div className="loading"><div className="spinner" />Загрузка...</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex-between">
          <div>
            <h1>👤 Пациенты</h1>
            <p>Поиск и управление карточками пациентов</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate("/patients/new")}>➕ Регистрация</button>
        </div>
      </div>

      <div className="page-content">
        {error && <div className="error-message">{error}</div>}

        <div className="toolbar">
          <div className="search-box">
            <span className="search-box-icon">🔍</span>
            <input
              className="input"
              placeholder="Поиск по ФИО, телефону, паспорту..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {patients.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">👤</div>
            <h3>{search ? "Ничего не найдено" : "Нет пациентов"}</h3>
            <p>{search ? "Попробуйте изменить поисковый запрос" : "Зарегистрируйте первого пациента"}</p>
            {!search && (
              <button className="btn btn-primary" onClick={() => navigate("/patients/new")}>➕ Регистрация</button>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ФИО</th>
                  <th>Дата рождения</th>
                  <th>Телефон</th>
                  <th>ПИНФЛ</th>
                  <th>Паспорт</th>
                  <th style={{ width: "120px" }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 700 }}>{p.full_name}</td>
                    <td>{p.birth_date || "—"}</td>
                    <td>{p.phone || "—"}</td>
                    <td>{p.pinfl || "—"}</td>
                    <td>{p.passport || "—"}</td>
                    <td>
                      <div className="flex flex-gap">
                        <button className="btn btn-outline btn-sm" onClick={() => setSelectedPatient(p)}>👁️</button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)}>🗑️</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selectedPatient && (
          <div className="modal-overlay" onClick={() => setSelectedPatient(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>👤 {selectedPatient.full_name}</h2>
                <button className="close-btn" onClick={() => setSelectedPatient(null)}>×</button>
              </div>
              <div className="modal-body">
                <div className="grid-2">
                  <div>
                    <p className="text-sm text-muted font-bold">Дата рождения</p>
                    <p className="mb-4">{selectedPatient.birth_date || "—"}</p>
                    <p className="text-sm text-muted font-bold">Пол</p>
                    <p className="mb-4">{selectedPatient.gender === "male" ? "Мужской" : selectedPatient.gender === "female" ? "Женский" : "—"}</p>
                    <p className="text-sm text-muted font-bold">Группа крови</p>
                    <p className="mb-4">{selectedPatient.blood_group || "—"}</p>
                    <p className="text-sm text-muted font-bold">Телефон</p>
                    <p className="mb-4">{selectedPatient.phone || "—"}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted font-bold">ПИНФЛ</p>
                    <p className="mb-4">{selectedPatient.pinfl || "—"}</p>
                    <p className="text-sm text-muted font-bold">Паспорт</p>
                    <p className="mb-4">{selectedPatient.passport || "—"}</p>
                    <p className="text-sm text-muted font-bold">Email</p>
                    <p className="mb-4">{selectedPatient.email || "—"}</p>
                    <p className="text-sm text-muted font-bold">Telegram</p>
                    <p className="mb-4">{selectedPatient.telegram_id ? `✅ ID: ${selectedPatient.telegram_id}` : "❌ Не привязан"}</p>
                  </div>
                </div>
                {selectedPatient.address && (
                  <>
                    <p className="text-sm text-muted font-bold mt-4">Адрес</p>
                    <p>{selectedPatient.address}</p>
                  </>
                )}
                {selectedPatient.emergency_contact && (
                  <>
                    <p className="text-sm text-muted font-bold mt-4">Экстренный контакт</p>
                    <p>{selectedPatient.emergency_contact}</p>
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-outline" onClick={() => setSelectedPatient(null)}>Закрыть</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}