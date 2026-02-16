const API_BASE = "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
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
}

export interface FileData {
  columns: string[];
  rows: Record<string, string>[];
  total: number;
}

// Health
export const checkHealth = () => request<{ status: string }>("/health");

// GSTINs
export const listGSTINs = () => request<GSTINRecord[]>("/gstins/");
export const addGSTIN = (gstin: string) =>
  request<GSTINRecord>("/gstins/", {
    method: "POST",
    body: JSON.stringify({ gstin }),
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
  const res = await fetch(`${API_BASE}/upload/`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
};
export const deleteUpload = (id: number) =>
  request<void>(`/upload/${id}`, { method: "DELETE" });

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
