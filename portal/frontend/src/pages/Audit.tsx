import { useEffect, useState, useRef } from "react";
import { Upload, Play, Trash2, FileText } from "lucide-react";
import {
  uploadAuditTemplates, listAuditTemplates, clearAuditTemplates,
  runAudit, getAuditReport, type AuditRunResult,
} from "../lib/api";

const STATES = [
  "03-Punjab", "06-Haryana", "07-Delhi", "09-Uttar Pradesh",
  "10-Bihar", "18-Assam", "19-West Bengal", "21-Odisha",
  "23-Madhya Pradesh", "24-Gujarat", "27-Maharashtra",
  "29-Karnataka", "33-Tamil Nadu", "36-Telangana",
];

export default function Audit() {
  const [templates, setTemplates] = useState<string[]>([]);
  const [selectedState, setSelectedState] = useState("07");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AuditRunResult | null>(null);
  const [report, setReport] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listAuditTemplates().then(setTemplates).catch(() => {});
    getAuditReport().then(setReport).catch(() => {});
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    await uploadAuditTemplates(Array.from(files));
    const updated = await listAuditTemplates();
    setTemplates(updated);
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleClear = async () => {
    await clearAuditTemplates();
    setTemplates([]);
  };

  const handleRun = async () => {
    setRunning(true);
    setResult(null);
    setReport(null);
    try {
      const res = await runAudit(selectedState);
      setResult(res);
      if (res.has_report) {
        const md = await getAuditReport();
        setReport(md);
      }
    } catch (err) {
      setResult({ status: "error", stdout: "", stderr: String(err), has_report: false });
    }
    setRunning(false);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Audit</h2>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Template Upload */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Template Files</h3>
          <p className="text-xs text-gray-400 mb-3">
            Upload previous month's CSVs for comparison
          </p>
          <div className="flex gap-2 mb-3">
            <label className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded text-xs cursor-pointer hover:bg-blue-700">
              <Upload size={14} /> Upload CSVs
              <input
                ref={fileRef}
                type="file"
                multiple
                accept=".csv"
                onChange={handleUpload}
                className="hidden"
              />
            </label>
            {templates.length > 0 && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1 px-3 py-1.5 text-red-600 border border-red-200 rounded text-xs hover:bg-red-50"
              >
                <Trash2 size={14} /> Clear
              </button>
            )}
          </div>
          {templates.length > 0 ? (
            <div className="space-y-1 max-h-40 overflow-auto">
              {templates.map((t) => (
                <div key={t} className="flex items-center gap-1.5 text-xs text-gray-600">
                  <FileText size={12} className="text-gray-400" /> {t}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-300">No templates uploaded</p>
          )}
        </div>

        {/* Run Audit */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Run Audit</h3>
          <p className="text-xs text-gray-400 mb-3">
            Compare generated output against templates
          </p>
          <div className="space-y-3">
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            >
              {STATES.map((s) => {
                const [code, ...nameParts] = s.split("-");
                return (
                  <option key={code} value={code}>
                    {code} - {nameParts.join("-")}
                  </option>
                );
              })}
            </select>
            <button
              onClick={handleRun}
              disabled={running || templates.length === 0}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play size={16} />
              {running ? "Running..." : "Run Audit"}
            </button>
          </div>
        </div>

        {/* Status */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Status</h3>
          {result ? (
            <div>
              <div className={`inline-block px-2 py-1 rounded text-xs font-medium mb-2 ${
                result.status === "completed"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}>
                {result.status.toUpperCase()}
              </div>
              {result.stderr && (
                <pre className="text-xs text-red-500 mt-2 max-h-32 overflow-auto">
                  {result.stderr}
                </pre>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-300">
              {running ? "Audit in progress..." : "No audit run yet"}
            </p>
          )}
        </div>
      </div>

      {/* Report */}
      {report && (
        <div className="bg-white rounded-lg shadow">
          <div className="bg-gray-50 px-4 py-3 border-b">
            <h3 className="text-sm font-semibold text-gray-700">Audit Report</h3>
          </div>
          <div className="p-4 overflow-auto max-h-[60vh]">
            <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap leading-relaxed">
              {report}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
