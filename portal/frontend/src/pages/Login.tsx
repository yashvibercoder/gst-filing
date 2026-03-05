import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listCompaniesPublic, setActiveCompanyId, type CompanyRecord } from "../lib/api";
import { FileCheck2, ArrowRight, Plus } from "lucide-react";

export default function Login() {
  const [companies, setCompanies] = useState<CompanyRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    listCompaniesPublic().then((data) => {
      setCompanies(data);
      setLoading(false);
    });
  }, []);

  const enter = (c: CompanyRecord) => {
    setActiveCompanyId(c.id, c.name, c.slug ?? c.name.toLowerCase().replace(/\s+/g, "-"));
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      {/* Header */}
      <div className="mb-10 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl mb-4">
          <FileCheck2 size={28} className="text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white">GST Filing</h1>
        <p className="text-gray-400 mt-2 text-sm">Select a company profile to continue</p>
      </div>

      {/* Company cards */}
      <div className="w-full max-w-md space-y-3">
        {loading ? (
          <p className="text-center text-gray-500 text-sm">Loading…</p>
        ) : companies.length === 0 ? (
          <div className="text-center space-y-4">
            <p className="text-gray-400 text-sm">No companies set up yet.</p>
            <button
              onClick={() => {
                // Enter with a placeholder so user can create the first company
                navigate("/companies");
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <Plus size={16} />
              Create First Company
            </button>
          </div>
        ) : (
          companies.map((c) => (
            <button
              key={c.id}
              onClick={() => enter(c)}
              className="w-full flex items-center justify-between px-5 py-4 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl text-left transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-400 font-bold text-base">
                    {c.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-white font-semibold text-sm">{c.name}</p>
                  {c.amazon_seller_id && (
                    <p className="text-gray-500 text-xs font-mono mt-0.5">{c.amazon_seller_id}</p>
                  )}
                </div>
              </div>
              <ArrowRight size={18} className="text-gray-600 group-hover:text-blue-400 transition-colors" />
            </button>
          ))
        )}
      </div>

      <p className="mt-10 text-xs text-gray-600">
        GST Filing Automation · Internal Portal
      </p>
    </div>
  );
}
