import { useEffect, useState } from "react";
import { Save, CheckCircle } from "lucide-react";
import {
  updateCompany, getActiveCompanyId, listCompanies,
  setActiveCompanyId, type CompanyRecord,
} from "../lib/api";

export default function Settings() {
  const [company, setCompany] = useState<CompanyRecord | null>(null);
  const [name, setName] = useState("");
  const [sellerId, setSellerId] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = getActiveCompanyId();
    if (!id) return;
    listCompanies().then((list) => {
      const c = list.find((x) => x.id === id) ?? null;
      setCompany(c);
      if (c) { setName(c.name); setSellerId(c.amazon_seller_id ?? ""); }
    });
  }, []);

  const handleSave = async () => {
    if (!company) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await updateCompany(company.id, {
        name: name.trim(),
        amazon_seller_id: sellerId.trim() || undefined,
      });
      setCompany(updated);
      // Update localStorage so sidebar reflects new name instantly
      setActiveCompanyId(
        updated.id,
        updated.name,
        updated.slug ?? updated.name.toLowerCase().replace(/\s+/g, "-"),
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
        <p className="text-sm text-gray-500 mt-1">Configure the active company profile</p>
      </div>

      {/* Company Settings */}
      <div className="bg-white rounded-xl shadow p-6 space-y-5">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b border-gray-100 pb-3">
          Company Profile
        </h3>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Company Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. Acme Traders"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Amazon Seller ID</label>
          <input
            type="text"
            value={sellerId}
            onChange={(e) => setSellerId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. A3SZBDZ05A1P39"
          />
          <p className="text-xs text-gray-400">Used to match Amazon sales files automatically</p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={handleSave}
            disabled={saving || !name.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-md transition-colors"
          >
            <Save size={14} />
            {saving ? "Saving…" : "Save Changes"}
          </button>
          {saved && (
            <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
              <CheckCircle size={15} /> Saved!
            </span>
          )}
        </div>
      </div>

      {/* App Info */}
      <div className="bg-white rounded-xl shadow p-6 mt-4 space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide border-b border-gray-100 pb-3">
          About
        </h3>
        <div className="grid grid-cols-2 gap-y-2 text-sm">
          <span className="text-gray-500">App</span>
          <span className="text-gray-800 font-medium">GST Filing</span>
          <span className="text-gray-500">Version</span>
          <span className="text-gray-800">1.0.0</span>
          <span className="text-gray-500">Active Company</span>
          <span className="text-gray-800 font-medium">{company?.name ?? "—"}</span>
          <span className="text-gray-500">Company ID</span>
          <span className="text-gray-800 font-mono text-xs">{company?.id ?? "—"}</span>
          <span className="text-gray-500">Output Folder</span>
          <span className="text-gray-800 font-mono text-xs">output/{company?.slug ?? "—"}/</span>
        </div>
      </div>
    </div>
  );
}
