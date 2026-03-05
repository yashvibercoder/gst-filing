import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Building2,
  Upload,
  Eye,
  ClipboardCheck,
  History,
  Settings,
  Briefcase,
  LogOut,
  FileCheck2,
} from "lucide-react";
import { clearActiveCompany, getActiveCompanyFromStorage } from "../lib/api";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/companies", label: "Companies", icon: Briefcase },
  { to: "/gstins", label: "GSTINs", icon: Building2 },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/review", label: "Review", icon: Eye },
  { to: "/audit", label: "Audit", icon: ClipboardCheck },
  { to: "/history", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const [activeCompany, setActiveCompany] = useState(getActiveCompanyFromStorage);
  const navigate = useNavigate();

  useEffect(() => {
    const refresh = () => setActiveCompany(getActiveCompanyFromStorage());
    window.addEventListener("companyChanged", refresh);
    return () => window.removeEventListener("companyChanged", refresh);
  }, []);

  function handleSwitch() {
    clearActiveCompany();
    navigate("/login");
  }

  return (
    <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-700 flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <FileCheck2 size={16} className="text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white leading-tight">GST Filing</h1>
          <p className="text-xs text-gray-500 leading-tight">Return Automation</p>
        </div>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map(({ to, label, icon: Icon, disabled = false }: { to: string; label: string; icon: React.ElementType; disabled?: boolean }) => (
          <NavLink
            key={to}
            to={disabled ? "#" : to}
            onClick={disabled ? (e) => e.preventDefault() : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                disabled
                  ? "text-gray-600 cursor-not-allowed"
                  : isActive
                  ? "bg-gray-800 text-white"
                  : "hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-gray-700 space-y-2">
        {activeCompany ? (
          <div className="text-xs">
            <span className="text-gray-500">Active company</span>
            <p className="text-gray-300 font-medium truncate" title={activeCompany.name}>
              {activeCompany.name}
            </p>
          </div>
        ) : (
          <p className="text-xs text-gray-600 italic">No active company</p>
        )}
        <button
          onClick={handleSwitch}
          className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 transition-colors w-full"
        >
          <LogOut size={13} />
          Switch Company
        </button>
        <p className="text-xs text-gray-600">v1.0.0</p>
      </div>
    </aside>
  );
}
