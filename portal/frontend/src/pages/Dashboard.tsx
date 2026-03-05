import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Building2,
  FileUp,
  Play,
  ArrowRight,
  IndianRupee,
  TrendingUp,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  BarChart3,
} from "lucide-react";
import {
  listGSTINs,
  listUploads,
  listSessions,
  getAnalytics,
  getValidationReport,
  type GSTINRecord,
  type UploadRecord,
  type SessionRecord,
  type AnalyticsData,
  type ValidationReport,
} from "../lib/api";

function formatCurrency(n: number): string {
  if (n >= 10000000) return `${(n / 10000000).toFixed(2)} Cr`;
  if (n >= 100000) return `${(n / 100000).toFixed(2)} L`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)} K`;
  return n.toFixed(2);
}

const RATE_COLORS: Record<number, string> = {
  0: "bg-gray-400",
  5: "bg-emerald-500",
  12: "bg-sky-500",
  18: "bg-amber-500",
  28: "bg-rose-500",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [gstins, setGstins] = useState<GSTINRecord[]>([]);
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listGSTINs(), listUploads(), listSessions()])
      .then(([g, u, s]) => {
        setGstins(g);
        setUploads(u);
        setSessions(s);
        const lastCompleted = s.find((sess) => sess.status === "completed");
        if (lastCompleted) {
          Promise.all([
            getAnalytics(lastCompleted.id).catch(() => null),
            getValidationReport(lastCompleted.id).catch(() => null),
          ]).then(([a, v]) => {
            setAnalytics(a);
            setValidation(v);
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const lastSession = sessions[0];
  const totalSize = uploads.reduce((s, u) => s + u.file_size, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400 text-lg">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-gray-900">Dashboard</h2>
        <p className="text-sm text-gray-500 mt-1">GST Filing Automation Overview</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* GSTINs Card */}
        <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-5 border-l-4 border-l-primary transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary-light">
              <Building2 size={18} className="text-primary" />
            </div>
            <span className="text-sm font-medium text-gray-500">GSTINs Registered</span>
          </div>
          <p className="text-3xl font-bold tracking-tight text-gray-900">
            {gstins.filter((g) => g.is_active).length}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {gstins.length} total &middot; {gstins.filter((g) => !g.is_active).length} inactive
          </p>
        </div>

        {/* Files Card */}
        <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-5 border-l-4 border-l-success transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-success-light">
              <FileUp size={18} className="text-success" />
            </div>
            <span className="text-sm font-medium text-gray-500">Files Uploaded</span>
          </div>
          <p className="text-3xl font-bold tracking-tight text-gray-900">{uploads.length}</p>
          <p className="text-xs text-gray-400 mt-1">
            {totalSize > 1048576
              ? `${(totalSize / 1048576).toFixed(1)} MB`
              : `${(totalSize / 1024).toFixed(0)} KB`}{" "}
            total
          </p>
        </div>

        {/* Last Run Card */}
        <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-5 border-l-4 border-l-purple transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-purple-light">
              <Play size={18} className="text-purple" />
            </div>
            <span className="text-sm font-medium text-gray-500">Last Run</span>
          </div>
          {lastSession ? (
            <>
              <p className="text-lg font-bold text-gray-900 capitalize">{lastSession.status}</p>
              <p className="text-xs text-gray-400 mt-1">
                {String(lastSession.month).padStart(2, "0")}/{lastSession.year} &middot;{" "}
                {lastSession.states_count} states &middot; {lastSession.files_count} files
              </p>
            </>
          ) : (
            <p className="text-gray-400 text-sm mt-2">No runs yet</p>
          )}
        </div>
      </div>

      {/* Validation Summary Banner */}
      {validation && (
        <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 size={18} className="text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Validation Results</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full">
              <CheckCircle2 size={14} /> {validation.summary.pass} Pass
            </span>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-red-700 bg-red-50 px-3 py-1 rounded-full">
              <XCircle size={14} /> {validation.summary.fail} Fail
            </span>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-700 bg-amber-50 px-3 py-1 rounded-full">
              <AlertTriangle size={14} /> {validation.summary.warn} Warn
            </span>
          </div>
        </div>
      )}

      {/* Tax Analytics Section */}
      {analytics && (
        <>
          {/* Tax Liability Summary */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <IndianRupee size={20} className="text-primary" />
              Tax Liability Summary
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl ring-1 ring-blue-100 p-4">
                <p className="text-xs font-medium text-blue-600 uppercase tracking-wide">
                  Taxable Value
                </p>
                <p className="text-2xl font-bold tracking-tight text-gray-900 mt-1">
                  {formatCurrency(analytics.total_taxable_value)}
                </p>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-white rounded-xl ring-1 ring-orange-100 p-4">
                <p className="text-xs font-medium text-orange-600 uppercase tracking-wide">IGST</p>
                <p className="text-2xl font-bold tracking-tight text-gray-900 mt-1">
                  {formatCurrency(analytics.total_igst)}
                </p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-white rounded-xl ring-1 ring-green-100 p-4">
                <p className="text-xs font-medium text-green-600 uppercase tracking-wide">
                  CGST + SGST
                </p>
                <p className="text-2xl font-bold tracking-tight text-gray-900 mt-1">
                  {formatCurrency(analytics.total_cgst + analytics.total_sgst)}
                </p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-white rounded-xl ring-1 ring-purple-100 p-4">
                <p className="text-xs font-medium text-purple-600 uppercase tracking-wide">
                  Total Tax
                </p>
                <p className="text-2xl font-bold tracking-tight text-gray-900 mt-1">
                  {formatCurrency(analytics.total_tax)}
                </p>
              </div>
            </div>
          </div>

          {/* Tax Rate Distribution */}
          {analytics.rate_breakdown.length > 0 && (
            <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-5">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp size={20} className="text-primary" />
                Tax Rate Distribution
              </h3>
              {/* Stacked bar */}
              <div className="flex rounded-lg overflow-hidden h-8 mb-4">
                {analytics.rate_breakdown.map((rb) => {
                  const pct =
                    analytics.total_taxable_value > 0
                      ? (rb.taxable_value / analytics.total_taxable_value) * 100
                      : 0;
                  if (pct < 0.5) return null;
                  return (
                    <div
                      key={rb.rate}
                      className={`${RATE_COLORS[rb.rate] || "bg-gray-400"} flex items-center justify-center text-white text-xs font-medium transition-all duration-300`}
                      style={{ width: `${pct}%` }}
                      title={`${rb.rate}% — ${pct.toFixed(1)}%`}
                    >
                      {pct > 8 ? `${rb.rate}%` : ""}
                    </div>
                  );
                })}
              </div>
              {/* Legend */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {analytics.rate_breakdown.map((rb) => (
                  <div key={rb.rate} className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-sm ${RATE_COLORS[rb.rate] || "bg-gray-400"}`}
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-700">{rb.rate}%</span>
                      <span className="text-xs text-gray-400 ml-1">
                        {formatCurrency(rb.taxable_value)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* State-wise Breakdown */}
          <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-5">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <MapPin size={20} className="text-primary" />
              State-wise Tax Breakdown
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      State
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Taxable Value
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      IGST
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      CGST
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      SGST
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Total Tax
                    </th>
                    <th className="text-right py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Invoices
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[...analytics.states]
                    .sort((a, b) => b.total_tax - a.total_tax)
                    .map((st, i) => {
                      const maxTax = Math.max(...analytics.states.map((s) => s.total_tax));
                      const intensity = maxTax > 0 ? st.total_tax / maxTax : 0;
                      return (
                        <tr
                          key={st.code}
                          className={`border-b border-gray-50 transition-colors hover:bg-gray-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}`}
                        >
                          <td className="py-2.5 px-3 font-medium text-gray-800">
                            {st.code}-{st.name}
                          </td>
                          <td className="py-2.5 px-3 text-right text-gray-600 tabular-nums">
                            {formatCurrency(st.taxable_value)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-gray-600 tabular-nums">
                            {formatCurrency(st.igst)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-gray-600 tabular-nums">
                            {formatCurrency(st.cgst)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-gray-600 tabular-nums">
                            {formatCurrency(st.sgst)}
                          </td>
                          <td className="py-2.5 px-3 text-right tabular-nums">
                            <span
                              className={`font-semibold ${intensity > 0.6 ? "text-rose-600" : intensity > 0.3 ? "text-amber-600" : "text-emerald-600"}`}
                            >
                              {formatCurrency(st.total_tax)}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-gray-500 tabular-nums">
                            {st.invoice_count}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-200 bg-gray-50 font-semibold">
                    <td className="py-2.5 px-3 text-gray-800">Total</td>
                    <td className="py-2.5 px-3 text-right text-gray-800 tabular-nums">
                      {formatCurrency(analytics.total_taxable_value)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-800 tabular-nums">
                      {formatCurrency(analytics.total_igst)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-800 tabular-nums">
                      {formatCurrency(analytics.total_cgst)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-800 tabular-nums">
                      {formatCurrency(analytics.total_sgst)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-900 tabular-nums">
                      {formatCurrency(analytics.total_tax)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-gray-800 tabular-nums">
                      {analytics.states.reduce((s, st) => s + st.invoice_count, 0)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Quick Start */}
      <div className="bg-white rounded-xl ring-1 ring-gray-100 shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Start</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => navigate("/gstins")}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg text-sm font-medium transition-colors duration-150 hover:bg-primary/90"
          >
            Manage GSTINs <ArrowRight size={14} />
          </button>
          <button
            onClick={() => navigate("/upload")}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-success text-white rounded-lg text-sm font-medium transition-colors duration-150 hover:bg-success/90"
          >
            Upload Files <ArrowRight size={14} />
          </button>
          {lastSession?.status === "completed" && (
            <button
              onClick={() => navigate("/review")}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-purple text-white rounded-lg text-sm font-medium transition-colors duration-150 hover:bg-purple/90"
            >
              Review Output <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
