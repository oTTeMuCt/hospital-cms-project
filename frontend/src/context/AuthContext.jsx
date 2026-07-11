import { createContext, useContext, useState, useEffect, useCallback } from "react";
import api from "../api";

const AuthContext = createContext(null);

const ROLE_LABELS = {
  admin: "Администратор",
  chief_doctor: "Главный врач",
  doctor: "Врач",
  lab_tech: "Лаборант",
  registrar: "Регистратор",
  patient: "Пациент",
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.clear();
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username, password) => {
    const res = await api.post("/auth/token/", { username, password });
    const { access, refresh } = res.data;

    localStorage.setItem("accessToken", access);
    localStorage.setItem("refreshToken", refresh);

    // Fetch user info
    const meRes = await api.get("/auth/me/");
    const userData = meRes.data;
    localStorage.setItem("user", JSON.stringify(userData));
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  const isAuthenticated = !!user;
  const role = user?.role || null;
  const roleLabel = ROLE_LABELS[role] || role;

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated, loading, role, roleLabel }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}