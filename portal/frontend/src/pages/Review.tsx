import { useEffect, useState } from "react";
import { Download, ChevronDown, ChevronRight } from "lucide-react";
import {
  listSessions, listStates, getFileData, getDownloadUrl,
  type SessionRecord, type StateInfo, type FileData,
} from "../lib/api";

export default function Review() {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [states, setStates] = useState<StateInfo[]>([]);
  const [expandedState, setExpandedState] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ state: string; file: string } | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
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
    }
  }, [selectedSession]);

  const handleFileClick = async (stateCode: string, filename: string) => {
    if (!selectedSession) return;
    setSelectedFile({ state: stateCode, file: filename });
    setFileData(null);
    const data = await getFileData(selectedSession, stateCode, filename);
    setFileData(data);
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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Review Output</h2>
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
      </div>

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
                  <span className="ml-auto text-xs text-gray-400">{s.files.length}</span>
                </button>
                {expandedState === s.code && (
                  <div className="bg-gray-50 px-4 pb-2 space-y-1">
                    {s.files.map((f) => (
                      <button
                        key={f}
                        onClick={() => handleFileClick(s.code, f)}
                        className={`w-full text-left text-xs px-2 py-1.5 rounded ${
                          selectedFile?.state === s.code && selectedFile?.file === f
                            ? "bg-blue-100 text-blue-700"
                            : "hover:bg-gray-200 text-gray-600"
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

        {/* File data table */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
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
              <div className="overflow-auto max-h-[65vh]">
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
        </div>
      </div>
    </div>
  );
}
