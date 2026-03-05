import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Download, Eye, CheckCircle, XCircle, Loader2, Clock } from "lucide-react";
import { listSessions, getSessionDownloadUrl, type SessionRecord } from "../lib/api";

const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function StatusBadge({ status }: { status: string }) {
  if (status === "completed")
    return <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full"><CheckCircle size={11} />Completed</span>;
  if (status === "failed")
    return <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full"><XCircle size={11} />Failed</span>;
  return <span className="inline-flex items-center gap-1 text-xs font-medium text-yellow-700 bg-yellow-50 border border-yellow-200 px-2 py-0.5 rounded-full"><Loader2 size={11} className="animate-spin" />Processing</span>;
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
    + "  " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function duration(start: string, end: string | null) {
  if (!end) return "—";
  const secs = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

export default function History() {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return <div className="text-gray-400 text-sm">Loading...</div>;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">History</h2>
        <p className="text-sm text-gray-500 mt-1">All past processing runs for this company</p>
      </div>

      {sessions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-10 text-center text-gray-400">
          No runs yet. Go to <span className="font-medium text-blue-600 cursor-pointer" onClick={() => navigate("/upload")}>Upload</span> to generate your first return.
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Run</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Period</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">States</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Files</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Started</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Duration</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sessions.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-gray-500 text-xs">#{s.id}</td>
                  <td className="px-5 py-3.5 font-semibold text-gray-800">
                    {MONTHS[s.month]} {s.year}
                  </td>
                  <td className="px-5 py-3.5"><StatusBadge status={s.status} /></td>
                  <td className="px-5 py-3.5 text-right text-gray-700">{s.states_count ?? "—"}</td>
                  <td className="px-5 py-3.5 text-right text-gray-700">{s.files_count ?? "—"}</td>
                  <td className="px-5 py-3.5 text-gray-500 text-xs whitespace-nowrap">
                    <span className="inline-flex items-center gap-1"><Clock size={11} />{formatDate(s.created_at)}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right text-gray-500 text-xs">
                    {duration(s.created_at, s.completed_at)}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center justify-end gap-2">
                      {s.status === "completed" && (
                        <>
                          <button
                            onClick={() => navigate("/review")}
                            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                            title="View in Review"
                          >
                            <Eye size={13} /> View
                          </button>
                          <a
                            href={getSessionDownloadUrl(s.id)}
                            download
                            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                            title="Download ZIP"
                          >
                            <Download size={13} /> ZIP
                          </a>
                        </>
                      )}
                      {s.error_message && (
                        <span className="text-xs text-red-500 max-w-xs truncate" title={s.error_message}>
                          {s.error_message}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
