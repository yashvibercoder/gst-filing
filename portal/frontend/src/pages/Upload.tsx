import { useEffect, useState, useCallback } from "react";
import { Upload as UploadIcon, Trash2, Play, CheckCircle, XCircle, Loader, Info } from "lucide-react";
import {
  listUploads, uploadFile, deleteUpload, updateUploadPlatform, runProcessing, listGSTINs,
  type UploadRecord, type SessionRecord, type GSTINRecord,
} from "../lib/api";

const PLATFORMS = ["amazon", "flipkart", "meesho", "einvoice"] as const;

const MONTH_NAMES = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function UploadPage() {
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<SessionRecord | null>(null);
  const [error, setError] = useState("");
  const [gstins, setGstins] = useState<GSTINRecord[]>([]);

  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());

  const reload = () => listUploads().then(setUploads).catch(() => {});

  useEffect(() => {
    reload();
    listGSTINs().then(setGstins).catch(() => {});
  }, []);

  const activeGstins = gstins.filter((g) => g.is_active);
  const inactiveGstins = gstins.filter((g) => !g.is_active);

  const handleFiles = async (files: FileList | null) => {
    if (!files) return;
    setUploading(true);
    setError("");
    try {
      for (const file of Array.from(files)) {
        await uploadFile(file);
      }
      reload();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  const handleDelete = async (u: UploadRecord) => {
    await deleteUpload(u.id);
    reload();
  };

  const handleSetPlatform = async (id: number, platform: string) => {
    await updateUploadPlatform(id, platform);
    reload();
  };

  const handleProcess = async () => {
    setProcessing(true);
    setError("");
    setResult(null);
    try {
      const session = await runProcessing(month, year);
      setResult(session);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setProcessing(false);
    }
  };

  const platformColor: Record<string, string> = {
    flipkart: "bg-yellow-100 text-yellow-800",
    amazon: "bg-orange-100 text-orange-800",
    meesho: "bg-pink-100 text-pink-800",
    einvoice: "bg-blue-100 text-blue-800",
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload & Process</h2>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors mb-6 ${
          dragOver ? "border-blue-400 bg-blue-50" : "border-gray-300 bg-white"
        }`}
      >
        <UploadIcon size={32} className="mx-auto text-gray-400 mb-3" />
        <p className="text-gray-600 mb-2">
          Drag & drop Excel files here, or{" "}
          <label className="text-blue-600 cursor-pointer hover:underline">
            browse
            <input
              type="file"
              multiple
              accept=".xlsx,.xls"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </label>
        </p>
        <p className="text-xs text-gray-400">
          Flipkart, Amazon, Meesho, E-Invoice (.xlsx)
        </p>
        {uploading && <p className="text-blue-500 text-sm mt-2">Uploading...</p>}
      </div>

      {/* Uploaded files */}
      {uploads.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden mb-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-4 py-3">File</th>
                <th className="text-left px-4 py-3">Platform</th>
                <th className="text-right px-4 py-3">Size</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {uploads.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{u.original_filename}</td>
                  <td className="px-4 py-3">
                    {u.platform ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${platformColor[u.platform] || "bg-gray-100 text-gray-600"}`}>
                        {u.platform}
                      </span>
                    ) : (
                      <select
                        defaultValue=""
                        onChange={(e) => { if (e.target.value) handleSetPlatform(u.id, e.target.value); }}
                        className="text-xs border border-amber-300 rounded px-1.5 py-0.5 bg-amber-50 text-amber-800 cursor-pointer focus:outline-none focus:ring-1 focus:ring-amber-400"
                      >
                        <option value="" disabled>tag platform…</option>
                        {PLATFORMS.map((p) => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-500">
                    {(u.file_size / 1024).toFixed(0)} KB
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(u)} className="text-red-400 hover:text-red-600">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Active states info */}
      {gstins.length > 0 && (
        <div className={`rounded-lg p-3 mb-6 flex items-start gap-2 text-sm ${
          activeGstins.length > 0 ? "bg-blue-50 text-blue-800" : "bg-amber-50 text-amber-800"
        }`}>
          <Info size={16} className="mt-0.5 shrink-0" />
          <div>
            {activeGstins.length > 0 ? (
              <>
                <span className="font-medium">Selective processing:</span>{" "}
                {activeGstins.length} active state{activeGstins.length !== 1 ? "s" : ""} will be processed
                ({activeGstins.map((g) => `${g.state_code}-${g.state_name}`).join(", ")})
                {inactiveGstins.length > 0 && (
                  <span className="text-blue-600">
                    {" "}| {inactiveGstins.length} inactive (skipped)
                  </span>
                )}
              </>
            ) : (
              <>
                <span className="font-medium">All GSTINs inactive.</span>{" "}
                No states will be processed. Activate at least one GSTIN in the management tab.
              </>
            )}
          </div>
        </div>
      )}

      {/* Process controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-600 mb-3">Run Pipeline</h3>
        <div className="flex items-center gap-4">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {MONTH_NAMES.slice(1).map((m, i) => (
              <option key={i + 1} value={i + 1}>{m}</option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
          <button
            onClick={handleProcess}
            disabled={processing || (gstins.length > 0 && activeGstins.length === 0)}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
          >
            {processing ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
            {processing ? "Processing..." : "Generate Returns"}
          </button>
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 text-red-600 text-sm">
            <XCircle size={16} /> {error}
          </div>
        )}

        {result && (
          <div className={`mt-3 flex items-center gap-2 text-sm ${result.status === "completed" ? "text-green-600" : "text-red-600"}`}>
            {result.status === "completed" ? <CheckCircle size={16} /> : <XCircle size={16} />}
            {result.status === "completed"
              ? `Completed: ${result.states_count} states, ${result.files_count} files`
              : `Failed: ${result.error_message}`}
          </div>
        )}
      </div>
    </div>
  );
}
