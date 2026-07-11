import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import MainLayout from "./layouts/MainLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Hospitals from "./pages/Hospitals";
import Departments from "./pages/Departments";
import Staff from "./pages/Staff";
import Patients from "./pages/Patients";
import PatientForm from "./pages/PatientForm";
import Appointments from "./pages/Appointments";
import Analyses from "./pages/Analyses";
import AuditLog from "./pages/AuditLog";
import Reports from "./pages/Reports";
import MyAnalyses from "./pages/MyAnalyses";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="hospitals" element={<Hospitals />} />
          <Route path="departments" element={<Departments />} />
          <Route path="staff" element={<Staff />} />
          <Route path="patients" element={<Patients />} />
          <Route path="patients/new" element={<PatientForm />} />
          <Route path="appointments" element={<Appointments />} />
          <Route path="analyses" element={<Analyses />} />
          <Route path="audit" element={<AuditLog />} />
          <Route path="reports" element={<Reports />} />
          <Route path="my-analyses" element={<MyAnalyses />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}