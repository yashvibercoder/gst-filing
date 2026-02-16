import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Building2, FileUp, Play } from "lucide-react";
import { listGSTINs, listUploads, listSessions, type GSTINRecord, type UploadRecord, type SessionRecord } from "../lib/api";

export default function Dashboard() {
  const navigate = useNavigate();
  const [gstins, setGstins] = useState<GSTINRecord[]>([]);
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listGSTINs(), listUploads(), listSessions()])
      .then(([g, u, s]) => { setGstins(g); setUploads(u); setSessions(s); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const lastSession = sessions[0];

  if (loading) {
    return <div className="text-gray-500">Loading...</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <Building2 size={20} className="text-blue-500" />
            <span className="text-sm font-medium text-gray-500">GSTINs Registered</span>
          </div>
          <p className="text-3xl font-bold text-gray-800">{gstins.filter(g => g.is_active).length}</p>
          <p className="text-xs text-gray-400 mt-1">{gstins.length} total</p>
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <FileUp size={20} className="text-green-500" />
            <span className="text-sm font-medium text-gray-500">Files Uploaded</span>
          </div>
          <p className="text-3xl font-bold text-gray-800">{uploads.length}</p>
          <p className="text-xs text-gray-400 mt-1">
            {uploads.reduce((s, u) => s + u.file_size, 0) > 1048576
              ? `${(uploads.reduce((s, u) => s + u.file_size, 0) / 1048576).toFixed(1)} MB`
              : `${(uploads.reduce((s, u) => s + u.file_size, 0) / 1024).toFixed(0)} KB`}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-5">
          <div className="flex items-center gap-3 mb-2">
            <Play size={20} className="text-purple-500" />
            <span className="text-sm font-medium text-gray-500">Last Run</span>
          </div>
          {lastSession ? (
            <>
              <p className="text-lg font-bold text-gray-800">
                {lastSession.status === "completed" ? "Completed" : lastSession.status}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {lastSession.states_count} states, {lastSession.files_count} files
              </p>
            </>
          ) : (
            <p className="text-gray-400 text-sm">No runs yet</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-3">Quick Start</h3>
        <div className="flex gap-3">
          <button
            onClick={() => navigate("/gstins")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
          >
            Manage GSTINs
          </button>
          <button
            onClick={() => navigate("/upload")}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
          >
            Upload Files
          </button>
          {lastSession?.status === "completed" && (
            <button
              onClick={() => navigate("/review")}
              className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700"
            >
              Review Output
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
