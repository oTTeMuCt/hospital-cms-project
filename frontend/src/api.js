import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, try to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refreshToken");

      if (refreshToken) {
        try {
          const res = await axios.post("/api/auth/token/refresh/", {
            refresh: refreshToken,
          });
          const newAccess = res.data.access;
          localStorage.setItem("accessToken", newAccess);
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
      } else {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Extract a user-friendly error message from an API error response.
 * Differentiates between 401, 403, 404, 500, and network errors.
 */
export function getErrorMessage(error) {
  if (!error.response) {
    // Network error or timeout
    if (error.code === "ECONNABORTED") {
      return "Сервер не отвечает. Проверьте подключение к интернету и попробуйте снова.";
    }
    return "Не удалось подключиться к серверу. Проверьте подключение к интернету.";
  }

  const { status, data } = error.response;

  // Try to extract detail from various response formats
  let detail = "";
  if (typeof data === "string") {
    detail = data;
  } else if (data?.detail) {
    detail = data.detail;
  } else if (data?.message) {
    detail = data.message;
  } else if (data?.error) {
    detail = data.error;
  } else if (typeof data === "object") {
    // Try to get first error message from validation errors
    const firstKey = Object.keys(data)[0];
    if (firstKey && Array.isArray(data[firstKey])) {
      detail = data[firstKey][0];
    }
  }

  switch (status) {
    case 401:
      return detail || "Требуется авторизация. Пожалуйста, войдите в систему.";
    case 403:
      return detail || "У вас нет прав для выполнения этого действия.";
    case 404:
      return detail || "Запрашиваемый ресурс не найден.";
    case 409:
      return detail || "Конфликт данных. Возможно, запись уже существует.";
    case 429:
      return detail || "Слишком много запросов. Пожалуйста, подождите немного.";
    case 500:
      return detail || "Внутренняя ошибка сервера. Попробуйте позже.";
    case 502:
      return "Сервер временно недоступен. Попробуйте позже.";
    case 503:
      return "Сервис временно недоступен. Ведутся технические работы.";
    default:
      return detail || `Произошла ошибка (код: ${status}). Попробуйте снова.`;
  }
}

export default api;

