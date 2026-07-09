import { useAuth } from "../context/AuthContext";

const stats = [
  { label: "Пациенты", value: "—", color: "var(--primary)" },
  { label: "Приёмы", value: "—", color: "var(--success)" },
  { label: "Анализы", value: "—", color: "#9B5DE5" },
];

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="container" style={{ maxWidth: "960px" }}>
      <h1
        style={{
          fontSize: "32px",
          fontWeight: 900,
          marginBottom: "8px",
          letterSpacing: "-0.5px",
        }}
      >
        Дашборд
      </h1>
      <p style={{ fontSize: "16px", color: "#666", marginBottom: "32px", fontWeight: 600 }}>
        Добро пожаловать{user?.full_name ? `, ${user.full_name}` : ""} в Hospital CMS
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "24px",
        }}
      >
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="card"
            style={{ textAlign: "center", borderTop: `6px solid ${stat.color}` }}
          >
            <div
              style={{
                fontSize: "48px",
                fontWeight: 900,
                color: stat.color,
                lineHeight: 1,
                marginBottom: "8px",
              }}
            >
              {stat.value}
            </div>
            <div style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase" }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
