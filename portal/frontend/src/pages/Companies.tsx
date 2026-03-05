import { useEffect, useState } from "react";
import {
  listCompanies,
  createCompany,
  updateCompany,
  activateCompany,
  deleteCompany,
  setActiveCompanyId,
  type CompanyRecord,
} from "../lib/api";
import { CheckCircle, Circle, Pencil, Trash2, Plus, X, Check } from "lucide-react";

export default function Companies() {
  const [companies, setCompanies] = useState<CompanyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add form state
  const [showAdd, setShowAdd] = useState(false);
  const [addName, setAddName] = useState("");
  const [addSellerId, setAddSellerId] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Edit state
  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editSellerId, setEditSellerId] = useState("");
  const [editLoading, setEditLoading] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listCompanies();
      setCompanies(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!addName.trim()) return;
    setAddLoading(true);
    try {
      await createCompany(addName.trim(), addSellerId.trim() || undefined);
      setAddName("");
      setAddSellerId("");
      setShowAdd(false);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create company");
    } finally {
      setAddLoading(false);
    }
  };

  const handleEditSave = async (id: number) => {
    setEditLoading(true);
    try {
      await updateCompany(id, {
        name: editName.trim(),
        amazon_seller_id: editSellerId.trim() || undefined,
      });
      setEditId(null);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to update company");
    } finally {
      setEditLoading(false);
    }
  };

  const handleActivate = async (id: number) => {
    try {
      await activateCompany(id);
      const c = companies.find((x) => x.id === id);
      if (c) setActiveCompanyId(c.id, c.name, c.slug ?? c.name.toLowerCase().replace(/\s+/g, "-"));
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to activate company");
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete company "${name}"? This cannot be undone.`)) return;
    try {
      await deleteCompany(id);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to delete company");
    }
  };

  const startEdit = (c: CompanyRecord) => {
    setEditId(c.id);
    setEditName(c.name);
    setEditSellerId(c.amazon_seller_id ?? "");
  };

  const activeCompany = companies.find((c) => c.is_active);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Company Profiles</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage companies. The active company's Amazon Seller ID is used for file matching during processing.
          </p>
        </div>
        <button
          onClick={() => { setShowAdd(true); setError(null); }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Company
        </button>
      </div>

      {/* Active company banner */}
      {activeCompany && (
        <div className="flex items-center gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-sm">
          <CheckCircle size={16} className="text-green-600 flex-shrink-0" />
          <span className="text-green-800">
            <span className="font-semibold">{activeCompany.name}</span> is the active company.
            {activeCompany.amazon_seller_id && (
              <span className="text-green-700"> Amazon Seller ID: <code className="font-mono bg-green-100 px-1 rounded">{activeCompany.amazon_seller_id}</code></span>
            )}
          </span>
        </div>
      )}

      {/* Add company form */}
      {showAdd && (
        <div className="border border-blue-200 bg-blue-50 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-blue-900">New Company</h3>
          <div className="flex gap-3 flex-wrap">
            <div className="flex-1 min-w-48">
              <label className="block text-xs font-medium text-gray-700 mb-1">Company Name *</label>
              <input
                type="text"
                value={addName}
                onChange={(e) => setAddName(e.target.value)}
                placeholder="e.g. Acme Traders"
                className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                autoFocus
              />
            </div>
            <div className="flex-1 min-w-48">
              <label className="block text-xs font-medium text-gray-700 mb-1">Amazon Seller ID</label>
              <input
                type="text"
                value={addSellerId}
                onChange={(e) => setAddSellerId(e.target.value)}
                placeholder="e.g. A3SZBDZ05A1P39"
                className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={addLoading || !addName.trim()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Check size={14} />
              {addLoading ? "Saving…" : "Save"}
            </button>
            <button
              onClick={() => { setShowAdd(false); setAddName(""); setAddSellerId(""); }}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <X size={14} />
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-4 py-2">{error}</div>
      )}

      {/* Companies table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading…</div>
        ) : companies.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No companies yet. Add one to get started.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600 w-8"></th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Company Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Amazon Seller ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {companies.map((c) => (
                <tr key={c.id} className={c.is_active ? "bg-green-50" : "hover:bg-gray-50"}>
                  {/* Active indicator */}
                  <td className="px-4 py-3">
                    {c.is_active ? (
                      <CheckCircle size={16} className="text-green-600" />
                    ) : (
                      <Circle size={16} className="text-gray-300" />
                    )}
                  </td>

                  {/* Name cell (editable) */}
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {editId === c.id ? (
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoFocus
                      />
                    ) : (
                      c.name
                    )}
                  </td>

                  {/* Seller ID cell (editable) */}
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {editId === c.id ? (
                      <input
                        type="text"
                        value={editSellerId}
                        onChange={(e) => setEditSellerId(e.target.value)}
                        placeholder="e.g. A3SZBDZ05A1P39"
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-full font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onKeyDown={(e) => e.key === "Enter" && handleEditSave(c.id)}
                      />
                    ) : (
                      c.amazon_seller_id ? (
                        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{c.amazon_seller_id}</code>
                      ) : (
                        <span className="text-gray-400 italic text-xs">not set</span>
                      )
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-3">
                    {c.is_active ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        Inactive
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {editId === c.id ? (
                        <>
                          <button
                            onClick={() => handleEditSave(c.id)}
                            disabled={editLoading}
                            className="flex items-center gap-1 px-2.5 py-1 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                          >
                            <Check size={12} />
                            Save
                          </button>
                          <button
                            onClick={() => setEditId(null)}
                            className="flex items-center gap-1 px-2.5 py-1 border border-gray-300 rounded text-xs text-gray-600 hover:bg-gray-100 transition-colors"
                          >
                            <X size={12} />
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          {!c.is_active && (
                            <button
                              onClick={() => handleActivate(c.id)}
                              className="px-2.5 py-1 text-xs font-medium text-green-700 border border-green-300 rounded hover:bg-green-50 transition-colors"
                            >
                              Set Active
                            </button>
                          )}
                          <button
                            onClick={() => startEdit(c)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="Edit"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(c.id, c.name)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-gray-400">
        During processing, the active company's Amazon Seller ID is used to match uploaded files (pattern: <code>*&lt;seller-id&gt;*.xlsx</code>). If no company is active or no seller ID is set, the default config pattern is used.
      </p>
    </div>
  );
}
