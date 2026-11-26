import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { getErrorMessage } from "../api";

export default function PasswordReset({ confirm = false }) {
  const params = useParams();
  const { hash } = useLocation();
  const [hashUid, hashToken] = hash.slice(1).split("/");
  const uid = params.uid ?? hashUid;
  const token = params.token ?? hashToken;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const invalidLink = confirm && (!uid || !token);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (confirm && password !== repeat) {
      setError("Пароли не совпадают.");
      return;
    }
    setSubmitting(true);
    try {
      const endpoint = confirm ? "/api/auth/password-reset/confirm/" : "/api/auth/password-reset/";
      const payload = confirm ? { uidb64: uid, token, new_password: password } : { email };
      const response = await axios.post(endpoint, payload);
      setSuccess(response.data.detail);
      setPassword("");
      setRepeat("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <h1>{confirm ? "Новый пароль" : "Восстановление пароля"}</h1>
        </div>
        {(error || invalidLink) && (
          <div className="alert alert-error" role="alert">{error || "Ссылка для сброса пароля недействительна."}</div>
        )}
        {success && <div className="alert alert-success" role="status">{success}</div>}
        {!success && !invalidLink && (
          <form onSubmit={handleSubmit}>
            {confirm ? (
              <>
                <div className="form-group">
                  <label htmlFor="reset-password">Новый пароль</label>
                  <input className="input" id="reset-password" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} required />
                </div>
                <div className="form-group">
                  <label htmlFor="reset-repeat">Повторите пароль</label>
                  <input className="input" id="reset-repeat" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={repeat} onChange={(event) => setRepeat(event.target.value)} required />
                </div>
              </>
            ) : (
              <div className="form-group">
                <label htmlFor="reset-email">Электронная почта</label>
                <input className="input" id="reset-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
              </div>
            )}
            <button className="btn btn-primary w-full" type="submit" disabled={submitting}>
              {submitting ? "Подождите…" : confirm ? "Сохранить пароль" : "Отправить ссылку"}
            </button>
          </form>
        )}
        <div className="auth-footer">
          {confirm && !success && <p><Link to="/password-reset">Запросить новую ссылку</Link></p>}
          <Link to="/login">Вернуться ко входу</Link>
        </div>
      </div>
    </div>
  );
}
