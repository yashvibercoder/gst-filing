import { useEffect, useState } from "react";
import { Download, ChevronDown, ChevronRight, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import {
  listSessions, listStates, getFileData, getDownloadUrl,
  getValidationReport, getStateJson, getJsonDownloadUrl, getSessionSummary,
  getSessionDownloadUrl,
  type SessionRecord, type StateInfo, type FileData, type ValidationReport,
  type SessionSummary,
} from "../lib/api";

type Tab = "csv" | "json" | "validation" | "summary";

export default function Review() {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [states, setStates] = useState<StateInfo[]>([]);
  const [expandedState, setExpandedState] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ state: string; file: string } | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("csv");
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [stateJson, setStateJson] = useState<Record<string, unknown> | null>(null);
  const [jsonLoading, setJsonLoading] = useState(false);
  const [validationFilter, setValidationFilter] = useState<string>("all");
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSessions()
      .then((s) => {
        setSessions(s);
        const completed = s.find((x) => x.status === "completed");
        if (completed) setSelectedSession(completed.id);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedSession) {
      listStates(selectedSession).then(setStates);
      getValidationReport(selectedSession).then(setValidation).catch(() => setValidation(null));
      setSummary(null);
    }
  }, [selectedSession]);

  const handleSummaryTab = async () => {
    setActiveTab("summary");
    if (!summary && selectedSession) {
      setSummaryLoading(true);
      getSessionSummary(selectedSession).then(setSummary).catch(() => setSummary(null)).finally(() => setSummaryLoading(false));
    }
  };

  const handleFileClick = async (stateCode: string, filename: string) => {
    if (!selectedSession) return;
    setSelectedFile({ state: stateCode, file: filename });
    setFileData(null);
    setActiveTab("csv");
    const data = await getFileData(selectedSession, stateCode, filename);
    setFileData(data);
  };

  const handleJsonPreview = async (stateCode: string) => {
    if (!selectedSession) return;
    setSelectedFile({ state: stateCode, file: "gstr1.json" });
    setActiveTab("json");
    setJsonLoading(true);
    try {
      const data = await getStateJson(selectedSession, stateCode);
      setStateJson(data);
    } catch {
      setStateJson(null);
    }
    setJsonLoading(false);
  };

  if (loading) return <div className="text-gray-500">Loading...</div>;

  if (sessions.length === 0) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Review Output</h2>
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400">
          No processing runs yet. Go to Upload to generate returns.
        </div>
      </div>
    );
  }

  const filteredChecks = validation?.checks.filter(
    (c) => validationFilter === "all" || c.status === validationFilter.toUpperCase()
  ) ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Review Output</h2>
        <div className="flex items-center gap-2">
          <select
            value={selectedSession || ""}
            onChange={(e) => setSelectedSession(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            {sessions
              .filter((s) => s.status === "completed")
              .map((s) => (
                <option key={s.id} value={s.id}>
                  Run #{s.id} — {s.states_count} states, {s.files_count} files
                </option>
              ))}
          </select>
          {selectedSession && (
            <a
              href={getSessionDownloadUrl(selectedSession)}
              download
              className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
            >
              <Download size={15} />
              Download All
            </a>
          )}
        </div>
      </div>

      {/* Validation Summary Bar */}
      {validation && (
        <div className="flex gap-3 mb-4">
          <button
            onClick={() => { setActiveTab("validation"); setValidationFilter("all"); }}
            className="flex items-center gap-2 bg-white rounded-lg shadow px-4 py-2.5 hover:bg-gray-50"
          >
            <span className="text-sm font-medium text-gray-600">Validation:</span>
          </button>
          <button
            onClick={() => { setActiveTab("validation"); setValidationFilter("pass"); }}
            className="flex items-center gap-1.5 bg-green-50 text-green-700 rounded-lg px-3 py-2.5 text-sm font-semibold hover:bg-green-100"
          >
            <CheckCircle size={16} />
            {validation.summary.pass} PASS
          </button>
          {validation.summary.fail > 0 && (
            <button
              onClick={() => { setActiveTab("validation"); setValidationFilter("fail"); }}
              className="flex items-center gap-1.5 bg-red-50 text-red-700 rounded-lg px-3 py-2.5 text-sm font-semibold hover:bg-red-100"
            >
              <XCircle size={16} />
              {validation.summary.fail} FAIL
            </button>
          )}
          {validation.summary.warn > 0 && (
            <button
              onClick={() => { setActiveTab("validation"); setValidationFilter("warn"); }}
              className="flex items-center gap-1.5 bg-yellow-50 text-yellow-700 rounded-lg px-3 py-2.5 text-sm font-semibold hover:bg-yellow-100"
            >
              <AlertTriangle size={16} />
              {validation.summary.warn} WARN
            </button>
          )}
        </div>
      )}

      <div className="flex gap-4">
        {/* State list */}
        <div className="w-64 bg-white rounded-lg shadow overflow-hidden flex-shrink-0">
          <div className="bg-gray-50 px-4 py-3 text-sm font-semibold text-gray-600 border-b">
            States ({states.length})
          </div>
          <div className="divide-y divide-gray-100 max-h-[70vh] overflow-auto">
            {states.map((s) => (
              <div key={s.code}>
                <button
                  onClick={() => setExpandedState(expandedState === s.code ? null : s.code)}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left hover:bg-gray-50"
                >
                  {expandedState === s.code ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <span className="font-mono text-gray-500">{s.code}</span>
                  <span className="truncate">{s.name}</span>
                  <span className="ml-auto text-xs text-gray-400">{s.files.length + s.json_files.length}</span>
                </button>
                {expandedState === s.code && (
                  <div className="bg-gray-50 px-4 pb-2 space-y-1">
                    {s.files.map((f) => (
                      <button
                        key={f}
                        onClick={() => handleFileClick(s.code, f)}
                        className={`w-full text-left text-xs px-2 py-1.5 rounded ${
                          selectedFile?.state === s.code && selectedFile?.file === f && activeTab === "csv"
                            ? "bg-blue-100 text-blue-700"
                            : "hover:bg-gray-200 text-gray-600"
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                    {s.json_files.map((f) => (
                      <button
                        key={f}
                        onClick={() => handleJsonPreview(s.code)}
                        className={`w-full text-left text-xs px-2 py-1.5 rounded ${
                          selectedFile?.state === s.code && activeTab === "json"
                            ? "bg-purple-100 text-purple-700"
                            : "hover:bg-gray-200 text-purple-600"
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Main content panel */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
          {/* Tab bar */}
          <div className="bg-gray-50 border-b flex items-center gap-0">
            <button
              onClick={() => setActiveTab("csv")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${
                activeTab === "csv"
                  ? "border-blue-500 text-blue-700 bg-white"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              CSV Data
            </button>
            <button
              onClick={() => setActiveTab("json")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${
                activeTab === "json"
                  ? "border-purple-500 text-purple-700 bg-white"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              JSON Preview
            </button>
            <button
              onClick={() => setActiveTab("validation")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${
                activeTab === "validation"
                  ? "border-green-500 text-green-700 bg-white"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              Validation Details
            </button>
            <button
              onClick={handleSummaryTab}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${
                activeTab === "summary"
                  ? "border-indigo-500 text-indigo-700 bg-white"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              GST Summary
            </button>
          </div>

          {/* CSV Tab */}
          {activeTab === "csv" && (
            <>
              {selectedFile && fileData ? (
                <>
                  <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-b">
                    <div>
                      <span className="text-sm font-semibold text-gray-700">
                        {selectedFile.state} / {selectedFile.file}
                      </span>
                      <span className="text-xs text-gray-400 ml-3">{fileData.total} rows</span>
                    </div>
                    {selectedSession && (
                      <a
                        href={getDownloadUrl(selectedSession, selectedFile.state, selectedFile.file)}
                        className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                      >
                        <Download size={14} /> Download CSV
                      </a>
                    )}
                  </div>
                  <div className="overflow-auto max-h-[60vh]">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-2 py-2 text-left text-gray-500 font-medium">#</th>
                          {fileData.columns.map((c) => (
                            <th key={c} className="px-2 py-2 text-left text-gray-500 font-medium whitespace-nowrap">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {fileData.rows.map((row, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-2 py-1.5 text-gray-400">{i + 1}</td>
                            {fileData.columns.map((c) => (
                              <td key={c} className="px-2 py-1.5 whitespace-nowrap">
                                {row[c] || ""}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-gray-400">
                  {selectedFile ? "Loading..." : "Select a state and file to preview"}
                </div>
              )}
            </>
          )}

          {/* JSON Tab */}
          {activeTab === "json" && (
            <>
              {selectedFile && stateJson ? (
                <>
                  <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-b">
                    <div>
                      <span className="text-sm font-semibold text-gray-700">
                        {selectedFile.state} / gstr1.json
                      </span>
                      <span className="text-xs text-gray-400 ml-3">
                        GSTIN: {(stateJson as Record<string, string>).gstin} | FP: {(stateJson as Record<string, string>).fp}
                      </span>
                    </div>
                    {selectedSession && selectedFile && (
                      <a
                        href={getJsonDownloadUrl(selectedSession, selectedFile.state)}
                        className="flex items-center gap-1 text-xs text-purple-600 hover:underline"
                      >
                        <Download size={14} /> Download JSON
                      </a>
                    )}
                  </div>
                  <div className="overflow-auto max-h-[60vh] p-4">
                    <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(stateJson, null, 2)}
                    </pre>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-gray-400">
                  {jsonLoading ? "Loading JSON..." : "Select a state's gstr1.json to preview"}
                </div>
              )}
            </>
          )}

          {/* Summary Tab */}
          {activeTab === "summary" && (
            <>
              {summaryLoading ? (
                <div className="p-8 text-center text-gray-400">Loading summary...</div>
              ) : summary ? (
                <div className="overflow-auto max-h-[65vh] p-4 space-y-6">
                  {summary.states.map((state) => {
                    const totalCgst = state.sections.reduce((s, x) => s + x.cgst, 0);
                    const totalSgst = state.sections.reduce((s, x) => s + x.sgst, 0);
                    const totalIgst = state.sections.reduce((s, x) => s + x.igst, 0);
                    const totalCess = state.sections.reduce((s, x) => s + x.cess, 0);
                    const fmt = (n: number) => n > 0 ? n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
                    return (
                      <div key={state.code} className="border border-gray-200 rounded-lg overflow-hidden">
                        <div className="bg-indigo-50 px-4 py-2 flex items-center gap-2">
                          <span className="font-mono text-indigo-700 font-semibold text-sm">{state.code}</span>
                          <span className="text-gray-700 font-medium text-sm">{state.name}</span>
                          <span className="ml-auto text-xs text-gray-400">{state.sections.length} sections</span>
                        </div>
                        <table className="w-full text-xs">
                          <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                              <th className="px-3 py-2 text-left text-gray-500 font-medium">Section Name</th>
                              <th className="px-3 py-2 text-right text-gray-500 font-medium">No. of Records</th>
                              <th className="px-3 py-2 text-right text-gray-500 font-medium">Central Tax (₹)</th>
                              <th className="px-3 py-2 text-right text-gray-500 font-medium">State/UT Tax (₹)</th>
                              <th className="px-3 py-2 text-right text-gray-500 font-medium">Integrated Tax (₹)</th>
                              <th className="px-3 py-2 text-right text-gray-500 font-medium">CESS (₹)</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {state.sections.map((sec) => (
                              <tr key={sec.key} className="hover:bg-gray-50">
                                <td className="px-3 py-2">
                                  <div className="font-medium text-gray-700">{sec.label}</div>
                                  <div className="text-gray-400 text-xs">Section {sec.section_code}</div>
                                </td>
                                <td className="px-3 py-2 text-right font-mono text-gray-700">{sec.rows}</td>
                                <td className="px-3 py-2 text-right font-mono text-gray-600">{fmt(sec.cgst)}</td>
                                <td className="px-3 py-2 text-right font-mono text-gray-600">{fmt(sec.sgst)}</td>
                                <td className="px-3 py-2 text-right font-mono text-gray-600">{fmt(sec.igst)}</td>
                                <td className="px-3 py-2 text-right font-mono text-gray-600">{fmt(sec.cess)}</td>
                              </tr>
                            ))}
                            <tr className="bg-indigo-50 font-semibold border-t-2 border-indigo-200">
                              <td className="px-3 py-2 text-indigo-700">Total</td>
                              <td className="px-3 py-2 text-right font-mono text-indigo-700">
                                {state.sections.reduce((s, x) => s + x.rows, 0)}
                              </td>
                              <td className="px-3 py-2 text-right font-mono text-indigo-700">{fmt(totalCgst)}</td>
                              <td className="px-3 py-2 text-right font-mono text-indigo-700">{fmt(totalSgst)}</td>
                              <td className="px-3 py-2 text-right font-mono text-indigo-700">{fmt(totalIgst)}</td>
                              <td className="px-3 py-2 text-right font-mono text-indigo-700">{fmt(totalCess)}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-400">No summary available</div>
              )}
            </>
          )}

          {/* Validation Tab */}
          {activeTab === "validation" && (
            <>
              {validation ? (
                <>
                  <div className="bg-gray-50 px-4 py-3 flex items-center gap-3 border-b">
                    <span className="text-sm font-semibold text-gray-700">Filter:</span>
                    {["all", "pass", "fail", "warn"].map((f) => (
                      <button
                        key={f}
                        onClick={() => setValidationFilter(f)}
                        className={`px-2.5 py-1 rounded text-xs font-medium ${
                          validationFilter === f
                            ? "bg-gray-200 text-gray-800"
                            : "text-gray-500 hover:bg-gray-100"
                        }`}
                      >
                        {f.toUpperCase()}
                        {f === "all" ? ` (${validation.checks.length})` :
                         f === "pass" ? ` (${validation.summary.pass})` :
                         f === "fail" ? ` (${validation.summary.fail})` :
                         ` (${validation.summary.warn})`}
                      </button>
                    ))}
                  </div>
                  <div className="overflow-auto max-h-[60vh]">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-gray-500 font-medium">Status</th>
                          <th className="px-3 py-2 text-left text-gray-500 font-medium">Check</th>
                          <th className="px-3 py-2 text-left text-gray-500 font-medium">State</th>
                          <th className="px-3 py-2 text-left text-gray-500 font-medium">Details</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {filteredChecks.map((c, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-3 py-2">
                              {c.status === "PASS" ? (
                                <span className="inline-flex items-center gap-1 text-green-600"><CheckCircle size={14} /> PASS</span>
                              ) : c.status === "FAIL" ? (
                                <span className="inline-flex items-center gap-1 text-red-600"><XCircle size={14} /> FAIL</span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-yellow-600"><AlertTriangle size={14} /> WARN</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-gray-700">{c.check}</td>
                            <td className="px-3 py-2 font-mono text-gray-500">{c.state}</td>
                            <td className="px-3 py-2 text-gray-600 max-w-md truncate">{c.details}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-gray-400">
                  No validation report available
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
