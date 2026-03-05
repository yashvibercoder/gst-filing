import { useEffect, useState } from "react";
import { Plus, Trash2, Eye, EyeOff, Save } from "lucide-react";
import { listGSTINs, addGSTIN, toggleGSTIN, deleteGSTIN, updateGSTIN, type GSTINRecord } from "../lib/api";

export default function GSTINs() {
  const [gstins, setGstins] = useState<GSTINRecord[]>([]);
  const [newGstin, setNewGstin] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [showPasswords, setShowPasswords] = useState<Record<number, boolean>>({});
  const [editing, setEditing] = useState<Record<number, { username: string; password: string }>>({});

  const reload = () => listGSTINs().then(setGstins).catch(() => {});

  useEffect(() => {
    reload().finally(() => setLoading(false));
  }, []);

  const handleAdd = async () => {
    setError("");
    const val = newGstin.trim().toUpperCase();
    if (val.length !== 15) {
      setError("GSTIN must be 15 characters");
      return;
    }
    try {
      await addGSTIN(val, newUsername.trim() || undefined, newPassword || undefined);
      setNewGstin("");
      setNewUsername("");
      setNewPassword("");
      reload();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleToggle = async (g: GSTINRecord) => {
    await toggleGSTIN(g.id, !g.is_active);
    reload();
  };

  const handleDelete = async (g: GSTINRecord) => {
    if (!confirm(`Delete ${g.gstin}?`)) return;
    await deleteGSTIN(g.id);
    reload();
  };

  const startEdit = (g: GSTINRecord) => {
    setEditing((prev) => ({
      ...prev,
      [g.id]: { username: g.portal_username || "", password: g.portal_password || "" },
    }));
  };

  const cancelEdit = (id: number) => {
    setEditing((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const saveCredentials = async (g: GSTINRecord) => {
    const edit = editing[g.id];
    if (!edit) return;
    await updateGSTIN(g.id, {
      portal_username: edit.username,
      portal_password: edit.password,
    });
    cancelEdit(g.id);
    reload();
  };

  const togglePasswordVisibility = (id: number) => {
    setShowPasswords((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (loading) return <div className="text-gray-500">Loading...</div>;

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">GSTIN Management</h2>

      {/* Add form */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-3 items-center mb-3">
          <input
            type="text"
            value={newGstin}
            onChange={(e) => setNewGstin(e.target.value.toUpperCase())}
            placeholder="Enter 15-character GSTIN"
            maxLength={15}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <button
            onClick={handleAdd}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 flex items-center gap-1"
          >
            <Plus size={16} /> Add
          </button>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            placeholder="Portal User ID (optional)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Portal Password (optional)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3">GSTIN</th>
              <th className="text-left px-4 py-3">State</th>
              <th className="text-left px-4 py-3">Portal User ID</th>
              <th className="text-left px-4 py-3">Password</th>
              <th className="text-center px-4 py-3">Active</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {gstins.map((g) => {
              const isEditing = g.id in editing;
              const edit = editing[g.id];
              const showPw = showPasswords[g.id];

              return (
                <tr key={g.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono">{g.gstin}</td>
                  <td className="px-4 py-3">{g.state_code}-{g.state_name}</td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <input
                        type="text"
                        value={edit.username}
                        onChange={(e) =>
                          setEditing((prev) => ({
                            ...prev,
                            [g.id]: { ...prev[g.id], username: e.target.value },
                          }))
                        }
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                        placeholder="User ID"
                      />
                    ) : (
                      <span
                        className={`cursor-pointer ${g.portal_username ? "text-gray-800" : "text-gray-400 italic"}`}
                        onClick={() => startEdit(g)}
                      >
                        {g.portal_username || "Click to add"}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <div className="flex items-center gap-1">
                        <input
                          type={showPw ? "text" : "password"}
                          value={edit.password}
                          onChange={(e) =>
                            setEditing((prev) => ({
                              ...prev,
                              [g.id]: { ...prev[g.id], password: e.target.value },
                            }))
                          }
                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="Password"
                        />
                        <button onClick={() => togglePasswordVisibility(g.id)} className="text-gray-400 hover:text-gray-600">
                          {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <span
                          className={`cursor-pointer ${g.portal_password ? "text-gray-800" : "text-gray-400 italic"}`}
                          onClick={() => startEdit(g)}
                        >
                          {g.portal_password ? (showPw ? g.portal_password : "••••••••") : "Click to add"}
                        </span>
                        {g.portal_password && (
                          <button onClick={() => togglePasswordVisibility(g.id)} className="text-gray-400 hover:text-gray-600">
                            {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => handleToggle(g)}
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        g.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {g.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {isEditing && (
                        <>
                          <button
                            onClick={() => saveCredentials(g)}
                            className="text-green-500 hover:text-green-700"
                            title="Save credentials"
                          >
                            <Save size={16} />
                          </button>
                          <button
                            onClick={() => cancelEdit(g.id)}
                            className="text-gray-400 hover:text-gray-600 text-xs"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(g)}
                        className="text-red-400 hover:text-red-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {gstins.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  No GSTINs registered. Add one above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
