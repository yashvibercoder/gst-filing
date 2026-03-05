const API_BASE = (window.location.port === "5173"
  ? "http://localhost:8000"
  : window.location.origin) + "/api";

export const getActiveCompanyId = (): number | null => {
  const v = localStorage.getItem("activeCompanyId");
  return v ? parseInt(v, 10) : null;
};

export const setActiveCompanyId = (id: number, name: string, slug: string) => {
  localStorage.setItem("activeCompanyId", String(id));
  localStorage.setItem("activeCompanyName", name);
  localStorage.setItem("activeCompanySlug", slug);
  window.dispatchEvent(new Event("companyChanged"));
};

export const clearActiveCompany = () => {
  localStorage.removeItem("activeCompanyId");
  localStorage.removeItem("activeCompanyName");
  localStorage.removeItem("activeCompanySlug");
  window.dispatchEvent(new Event("companyChanged"));
};

export const getActiveCompanyFromStorage = (): { id: number; name: string; slug: string } | null => {
  const id = localStorage.getItem("activeCompanyId");
  const name = localStorage.getItem("activeCompanyName");
  const slug = localStorage.getItem("activeCompanySlug");
  if (!id || !name) return null;
  return { id: parseInt(id, 10), name, slug: slug ?? "" };
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const companyId = getActiveCompanyId();
  const companyHeader: Record<string, string> = companyId ? { "X-Company-Id": String(companyId) } : {};
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...companyHeader, ...(options?.headers as Record<string, string> | undefined) },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Types
export interface GSTINRecord {
  id: number;
  gstin: string;
  state_code: string;
  state_name: string;
  portal_username: string | null;
  portal_password: string | null;
  is_active: boolean;
}

export interface UploadRecord {
  id: number;
  original_filename: string;
  stored_filename: string;
  platform: string | null;
  file_size: number;
  uploaded_at: string;
}

export interface SessionRecord {
  id: number;
  month: number;
  year: number;
  status: string;
  states_count: number;
  files_count: number;
  validation_summary: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface StateInfo {
  code: string;
  name: string;
  files: string[];
  json_files: string[];
}

export interface ValidationCheck {
  check: string;
  status: string;
  state: string;
  details: string;
}

export interface ValidationReport {
  summary: { pass: number; fail: number; warn: number };
  checks: ValidationCheck[];
}

export interface FileData {
  columns: string[];
  rows: Record<string, string>[];
  total: number;
}

export interface StateAnalytics {
  code: string;
  name: string;
  taxable_value: number;
  igst: number;
  cgst: number;
  sgst: number;
  total_tax: number;
  invoice_count: number;
  sections: { b2b: number; b2cs: number; cdnr: number };
}

export interface RateBreakdown {
  rate: number;
  taxable_value: number;
  tax: number;
}

export interface AnalyticsData {
  total_taxable_value: number;
  total_igst: number;
  total_cgst: number;
  total_sgst: number;
  total_tax: number;
  states: StateAnalytics[];
  rate_breakdown: RateBreakdown[];
}

export interface SectionSummary {
  key: string;
  label: string;
  section_code: string;
  rows: number;
  igst: number;
  cgst: number;
  sgst: number;
  cess: number;
}

export interface StateSummary {
  code: string;
  name: string;
  sections: SectionSummary[];
}

export interface SessionSummary {
  states: StateSummary[];
}

export interface CompanyRecord {
  id: number;
  name: string;
  slug: string | null;
  amazon_seller_id: string | null;
  is_active: boolean;
  created_at: string;
}

// Health
export const checkHealth = () => request<{ status: string }>("/health");

// Companies
// Used on login page — no X-Company-Id header needed
export const listCompaniesPublic = async (): Promise<CompanyRecord[]> => {
  const res = await fetch(`${API_BASE}/companies/`);
  if (!res.ok) return [];
  return res.json();
};
export const listCompanies = () => request<CompanyRecord[]>("/companies/");
export const getActiveCompany = () => request<CompanyRecord | null>("/companies/active");
export const createCompany = (name: string, amazon_seller_id?: string) =>
  request<CompanyRecord>("/companies/", {
    method: "POST",
    body: JSON.stringify({ name, amazon_seller_id: amazon_seller_id || null }),
  });
export const updateCompany = (id: number, data: { name?: string; amazon_seller_id?: string }) =>
  request<CompanyRecord>(`/companies/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
export const activateCompany = (id: number) =>
  request<CompanyRecord>(`/companies/${id}/activate`, { method: "POST" });
export const deleteCompany = (id: number) =>
  request<void>(`/companies/${id}`, { method: "DELETE" });

// GSTINs
export const listGSTINs = () => request<GSTINRecord[]>("/gstins/");
export const addGSTIN = (gstin: string, portal_username?: string, portal_password?: string) =>
  request<GSTINRecord>("/gstins/", {
    method: "POST",
    body: JSON.stringify({ gstin, portal_username: portal_username || null, portal_password: portal_password || null }),
  });
export const updateGSTIN = (id: number, data: { is_active?: boolean; portal_username?: string; portal_password?: string }) =>
  request<GSTINRecord>(`/gstins/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
export const toggleGSTIN = (id: number, is_active: boolean) =>
  request<GSTINRecord>(`/gstins/${id}`, {
    method: "PUT",
    body: JSON.stringify({ is_active }),
  });
export const deleteGSTIN = (id: number) =>
  request<void>(`/gstins/${id}`, { method: "DELETE" });

// Uploads
export const listUploads = () => request<UploadRecord[]>("/upload/");
export const uploadFile = async (file: File): Promise<UploadRecord> => {
  const form = new FormData();
  form.append("file", file);
  const companyId = getActiveCompanyId();
  const headers: Record<string, string> = companyId ? { "X-Company-Id": String(companyId) } : {};
  const res = await fetch(`${API_BASE}/upload/`, { method: "POST", body: form, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
};
export const deleteUpload = (id: number) =>
  request<void>(`/upload/${id}`, { method: "DELETE" });
export const updateUploadPlatform = (id: number, platform: string | null) =>
  request<UploadRecord>(`/upload/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ platform }),
  });

// Processing
export const runProcessing = (month: number, year: number) =>
  request<SessionRecord>("/processing/run", {
    method: "POST",
    body: JSON.stringify({ month, year }),
  });
export const getSessionStatus = (id: number) =>
  request<SessionRecord>(`/processing/status/${id}`);
export const listSessions = () => request<SessionRecord[]>("/processing/history");

// Results
export const listStates = (sessionId: number) =>
  request<StateInfo[]>(`/results/${sessionId}/states`);
export const getFileData = (sessionId: number, stateCode: string, filename: string) =>
  request<FileData>(`/results/${sessionId}/states/${stateCode}/files/${filename}`);
export const getDownloadUrl = (sessionId: number, stateCode: string, filename: string) =>
  `${API_BASE}/results/${sessionId}/states/${stateCode}/files/${filename}/download`;
export const getValidationReport = (sessionId: number) =>
  request<ValidationReport>(`/results/${sessionId}/validation`);
export const getStateJson = (sessionId: number, stateCode: string) =>
  request<Record<string, unknown>>(`/results/${sessionId}/states/${stateCode}/json`);
export const getJsonDownloadUrl = (sessionId: number, stateCode: string) =>
  `${API_BASE}/results/${sessionId}/states/${stateCode}/json/download`;
export const getAnalytics = (sessionId: number) =>
  request<AnalyticsData>(`/results/${sessionId}/analytics`);
export const getSessionSummary = (sessionId: number) =>
  request<SessionSummary>(`/results/${sessionId}/summary`);
export const getSessionDownloadUrl = (sessionId: number) =>
  `${API_BASE}/results/${sessionId}/download`;

// Audit
export interface AuditRunResult {
  status: string;
  stdout: string;
  stderr: string;
  has_report: boolean;
}

export const uploadAuditTemplates = async (files: File[]): Promise<{ uploaded: string[]; count: number }> => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const companyId = getActiveCompanyId();
  const headers: Record<string, string> = companyId ? { "X-Company-Id": String(companyId) } : {};
  const res = await fetch(`${API_BASE}/audit/upload-templates`, { method: "POST", body: form, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
};
export const listAuditTemplates = () => request<string[]>("/audit/templates");
export const clearAuditTemplates = () =>
  request<{ status: string }>("/audit/templates", { method: "DELETE" });
export const runAudit = (stateCode: string) =>
  request<AuditRunResult>(`/audit/run?state_code=${stateCode}`, { method: "POST" });
export const getAuditReport = async (): Promise<string> => {
  const res = await fetch(`${API_BASE}/audit/report`);
  if (!res.ok) throw new Error("No audit report found");
  return res.text();
};
