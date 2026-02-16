import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Building2,
  Upload,
  Eye,
  History,
  Settings,
} from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/gstins", label: "GSTINs", icon: Building2 },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/review", label: "Review", icon: Eye },
  { to: "/history", label: "History", icon: History, disabled: true },
  { to: "/settings", label: "Settings", icon: Settings, disabled: true },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col min-h-screen">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-lg font-bold text-white">GST Portal</h1>
        <p className="text-xs text-gray-500 mt-0.5">Filing Automation</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map(({ to, label, icon: Icon, disabled }) => (
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
      <div className="p-4 border-t border-gray-700 text-xs text-gray-600">
        v1.0.0
      </div>
    </aside>
  );
}
