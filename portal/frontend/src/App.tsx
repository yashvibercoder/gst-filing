import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import GSTINs from "./pages/GSTINs";
import UploadPage from "./pages/Upload";
import Review from "./pages/Review";
import Audit from "./pages/Audit";
import Companies from "./pages/Companies";
import History from "./pages/History";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

function RequireCompany({ children }: { children: React.ReactNode }) {
  const companyId = localStorage.getItem("activeCompanyId");
  if (!companyId) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        {/* Companies page: accessible without login (needed to create the first company) */}
        <Route element={<Layout />}>
          <Route path="/companies" element={<Companies />} />
        </Route>
        {/* All other pages require a selected company */}
        <Route
          element={
            <RequireCompany>
              <Layout />
            </RequireCompany>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/gstins" element={<GSTINs />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/review" element={<Review />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
