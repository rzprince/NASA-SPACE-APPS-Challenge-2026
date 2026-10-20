/** BoponX browser data access. Public publishable key only; row-level security enforces authorization. */
export const DB_URL = (import.meta.env.VITE_BOPONX_SUPABASE_URL || "").replace(/\/$/, "");
const PUBLIC_KEY = import.meta.env.VITE_BOPONX_SUPABASE_PUBLISHABLE_KEY || "";
const SESSION_KEY = "boponx:editor-session";

export const GROUPS = ["district", "region", "season", "soil", "crop", "hazard", "source", "plan_action"] as const;
export type GroupName = (typeof GROUPS)[number];
export type ReviewState = "draft" | "approved" | "archived";

export type EvidenceEntry = {
  id: string;
  category: GroupName;
  code: string;
  title_en: string;
  title_bn: string;
  summary_en: string;
  summary_bn: string;
  region_code: string;
  crop_code: string;
  source_name: string;
  source_url: string;
  review_state: ReviewState;
  content: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};
export type EntryDraft = Omit<EvidenceEntry, "id" | "created_at" | "updated_at">;
export type EditorSession = {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  user: { id: string; email?: string };
};
export type AuditRow = {
  id: number;
  entry_id: string | null;
  action: string;
  actor_id: string | null;
  changed_at: string;
};

export function configured() { return Boolean(DB_URL && PUBLIC_KEY); }

function headers(token?: string, prefer?: string): HeadersInit {
  return {
    apikey: PUBLIC_KEY,
    ...(token ? { Authorization: "Bearer " + token } : {}),
    ...(prefer ? { Prefer: prefer } : {}),
  };
}
async function result<T>(r: Response): Promise<T> {
  const raw = await r.text();
  let payload: any = null;
  try { payload = raw ? JSON.parse(raw) : null; } catch { throw new Error("Unrecognized database response."); }
  if (!r.ok) throw new Error(payload?.msg || payload?.message || payload?.error_description || "Database request failed (" + r.status + ")");
  return payload as T;
}
export function savedSession(): EditorSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) as EditorSession : null;
  } catch { return null; }
}
function saveSession(s: EditorSession | null) {
  if (s) sessionStorage.setItem(SESSION_KEY, JSON.stringify(s));
  else sessionStorage.removeItem(SESSION_KEY);
}
function normalizeSession(data: any): EditorSession {
  const original = savedSession();
  const session: EditorSession = {
    access_token: data.access_token,
    refresh_token: data.refresh_token || original?.refresh_token || "",
    expires_at: Math.floor(Date.now() / 1000) + (Number(data.expires_in) || 3600),
    user: data.user || original?.user || { id: "" },
  };
  saveSession(session);
  return session;
}
export async function signIn(email: string, password: string) {
  if (!configured()) throw new Error("Supabase configuration is missing.");
  const r = await fetch(DB_URL + "/auth/v1/token?grant_type=password", {
    method: "POST", headers: { ...headers(), "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return normalizeSession(await result<any>(r));
}
export async function signUp(email: string, password: string) {
  if (!configured()) throw new Error("Supabase configuration is missing.");
  const r = await fetch(DB_URL + "/auth/v1/signup", {
    method: "POST", headers: { ...headers(), "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return result<{ user?: { id: string }; session?: EditorSession | null }>(r);
}
export async function currentSession(): Promise<EditorSession | null> {
  const stored = savedSession();
  if (!stored) return null;
  if (stored.expires_at > Date.now() / 1000 + 60) return stored;
  if (!stored.refresh_token) { saveSession(null); return null; }
  const r = await fetch(DB_URL + "/auth/v1/token?grant_type=refresh_token", {
    method: "POST", headers: { ...headers(), "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: stored.refresh_token }),
  });
  if (!r.ok) { saveSession(null); return null; }
  return normalizeSession(await result<any>(r));
}
export async function signOut() {
  const s = await currentSession();
  if (s) {
    try { await fetch(DB_URL + "/auth/v1/logout", { method: "POST", headers: headers(s.access_token) }); } catch { /* local sign-out still applies */ }
  }
  saveSession(null);
}
async function table<T>(tableName: "boponx_entries" | "boponx_admins" | "boponx_audit", query: string, method="GET", body?: unknown, authenticated=false) {
  if (!configured()) throw new Error("Connect BoponX to its Supabase project first.");
  const s = authenticated ? await currentSession() : null;
  if (authenticated && !s) throw new Error("Your administrator session expired. Sign in again.");
  const r = await fetch(DB_URL + "/rest/v1/" + tableName + "?" + query, {
    method,
    headers: { ...headers(s?.access_token, method === "GET" ? undefined : "return=representation"), ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  return result<T>(r);
}
export async function checkAdmin(): Promise<boolean> {
  const s = await currentSession();
  if (!s?.user?.id) return false;
  const rows = await table<Array<{ role: string }>>("boponx_admins", "select=role&user_id=eq." + encodeURIComponent(s.user.id), "GET", undefined, true);
  return rows.some(row => row.role === "owner" || row.role === "editor");
}
export async function loadEvidence(admin=false): Promise<EvidenceEntry[]> {
  const q = "select=*&order=updated_at.desc&limit=1500" + (admin ? "" : "&review_state=eq.approved");
  return table<EvidenceEntry[]>("boponx_entries", q, "GET", undefined, admin);
}
export async function createEvidence(entry: EntryDraft): Promise<EvidenceEntry> {
  const rows = await table<EvidenceEntry[]>("boponx_entries", "select=*", "POST", entry, true);
  if (rows.length !== 1) throw new Error("Record creation could not be verified.");
  return rows[0];
}
export async function updateEvidence(id: string, entry: EntryDraft): Promise<EvidenceEntry> {
  const rows = await table<EvidenceEntry[]>("boponx_entries", "id=eq." + encodeURIComponent(id) + "&select=*", "PATCH", entry, true);
  if (rows.length !== 1) throw new Error("Record update could not be verified.");
  return rows[0];
}
export async function deleteEvidence(id: string): Promise<void> {
  const rows = await table<EvidenceEntry[]>("boponx_entries", "id=eq." + encodeURIComponent(id) + "&select=id", "DELETE", undefined, true);
  if (rows.length !== 1) throw new Error("Record deletion could not be verified.");
}
export async function loadAudit(): Promise<AuditRow[]> {
  return table<AuditRow[]>("boponx_audit", "select=id,entry_id,action,actor_id,changed_at&order=changed_at.desc&limit=80", "GET", undefined, true);
}
