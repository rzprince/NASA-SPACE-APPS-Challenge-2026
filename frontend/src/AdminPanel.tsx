import { useEffect, useMemo, useState, type FormEvent } from "react";
import {
  GROUPS, checkAdmin, configured, createEvidence, currentSession, deleteEvidence,
  loadAudit, loadEvidence, savedSession, signIn, signOut, signUp, updateEvidence,
  type AuditRow, type EditorSession, type EntryDraft, type EvidenceEntry, type GroupName, type ReviewState,
} from "./boponxDb";

const EMPTY: EntryDraft = {
  category: "crop", code: "", title_en: "", title_bn: "", summary_en: "", summary_bn: "",
  region_code: "", crop_code: "", source_name: "", source_url: "",
  review_state: "draft", content: {},
};
const LABELS: Record<GroupName, string> = {
  district: "Districts · জেলা", region: "Divisions · বিভাগ", season: "Seasons · মৌসুম",
  soil: "Soil · মাটি", crop: "Crops · ফসল", hazard: "Risks · ঝুঁকি",
  source: "Sources · উৎস", plan_action: "90-day tasks · ৯০ দিনের কাজ",
};

export default function AdminPanel() {
  const [session, setSession] = useState<EditorSession | null>(() => savedSession());
  const [authorized, setAuthorized] = useState(false);
  const [checking, setChecking] = useState(Boolean(session));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [registering, setRegistering] = useState(false);
  const [items, setItems] = useState<EvidenceEntry[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [group, setGroup] = useState<GroupName | "all">("all");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<EntryDraft>(EMPTY);
  const [json, setJson] = useState("{}");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function sync() {
    const [records, history] = await Promise.all([loadEvidence(true), loadAudit()]);
    setItems(records);
    setAudit(history);
  }
  useEffect(() => {
    let active = true;
    (async () => {
      if (!session) { setChecking(false); return; }
      try {
        const fresh = await currentSession();
        const valid = Boolean(fresh && await checkAdmin());
        if (!active) return;
        setSession(fresh);
        setAuthorized(valid);
        if (valid) await sync();
      } catch (e) { if (active) setError(e instanceof Error ? e.message : "Unable to verify permission."); }
      finally { if (active) setChecking(false); }
    })();
    return () => { active = false; };
  }, [session?.user.id]);

  const visible = useMemo(() => items.filter(x => {
    const g = group === "all" || x.category === group;
    const term = search.toLowerCase().trim();
    return g && (!term || [x.code, x.title_en, x.title_bn, x.summary_en, x.region_code].join(" ").toLowerCase().includes(term));
  }), [items, group, search]);
  const counts = useMemo(() => ({
    all: items.length, approved: items.filter(x => x.review_state === "approved").length,
    draft: items.filter(x => x.review_state === "draft").length,
  }), [items]);

  async function login(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      if (registering) {
        const result = await signUp(email.trim(), password);
        setMessage(result.session
          ? "Account created. Access requires a project-owner role assignment."
          : "Account requested. Check your email to confirm it, then sign in. An owner must grant editor access.");
        setRegistering(false);
      } else {
        const s = await signIn(email.trim(), password);
        setSession(s);
        setChecking(true);
        setPassword("");
      }
    } catch(e) { setError(e instanceof Error ? e.message : "Authentication failed."); }
    finally { setBusy(false); }
  }
  async function exit() {
    setBusy(true);
    try { await signOut(); setAuthorized(false); setSession(null); setItems([]); setSelectedId(null); }
    catch(e) { setError(e instanceof Error ? e.message : "Sign-out failed."); }
    finally { setBusy(false); }
  }
  function pick(row: EvidenceEntry) {
    setSelectedId(row.id);
    const { id: _id, created_at: _created, updated_at: _updated, ...editable } = row;
    setDraft(editable);
    setJson(JSON.stringify(editable.content ?? {}, null, 2));
    setMessage(""); setError("");
  }
  function createNew() {
    setSelectedId(null); setDraft({ ...EMPTY, category: group === "all" ? "crop" : group });
    setJson("{}"); setMessage(""); setError("");
  }
  function change<K extends keyof EntryDraft>(key: K, value: EntryDraft[K]) {
    setDraft(old => ({ ...old, [key]: value }));
  }
  async function save(e: FormEvent) {
    e.preventDefault(); setError(""); setMessage("");
    let data: Record<string, unknown>;
    try {
      data = JSON.parse(json);
      if (!data || Array.isArray(data) || typeof data !== "object") throw new Error("JSON must be an object.");
      if (draft.source_url && !draft.source_url.startsWith("https://")) throw new Error("Source URLs must use HTTPS.");
      if (!/^[a-z0-9][a-z0-9_-]{1,89}$/.test(draft.code)) throw new Error("Use a lowercase code of at least two letters/numbers; hyphens and underscores allowed.");
      if (draft.title_en.trim().length < 2) throw new Error("English title is required.");
    } catch(e) { setError(e instanceof Error ? e.message : "Invalid data."); return; }
    setBusy(true);
    try {
      const payload: EntryDraft = { ...draft, title_en: draft.title_en.trim(), content: data };
      const saved = selectedId ? await updateEvidence(selectedId, payload) : await createEvidence(payload);
      await sync();
      pick(saved);
      setMessage(selectedId ? "Update saved and confirmed in Supabase. · পরিবর্তন সংরক্ষিত" : "New record created and confirmed in Supabase. · তথ্য যোগ হয়েছে");
    } catch(e) { setError(e instanceof Error ? e.message : "Save failed."); }
    finally { setBusy(false); }
  }
  async function remove() {
    if (!selectedId) return;
    const item = items.find(x => x.id === selectedId);
    if (!window.confirm("Permanently delete “" + (item?.title_en || selectedId) + "”? Audit history remains. \n\nএই তথ্য স্থায়ীভাবে মুছে ফেলবেন?")) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await deleteEvidence(selectedId);
      createNew();
      await sync();
      setMessage("Record deleted and verified. · তথ্য মুছে ফেলা হয়েছে");
    } catch(e) { setError(e instanceof Error ? e.message : "Delete failed."); }
    finally { setBusy(false); }
  }

  if (!configured()) return <main className="cms-shell"><section className="cms-welcome">
    <h1>Administrator setup needed</h1><p>Set VITE_BOPONX_SUPABASE_URL and VITE_BOPONX_SUPABASE_PUBLISHABLE_KEY for this deployment. Never use a service-role key in browser code.</p>
  </section></main>;

  if (!session || checking || !authorized) return <main className="cms-shell"><section className="cms-welcome">
    <p className="cms-eyebrow">BOPONX · AUTHORIZED OPERATORS</p>
    <h1>Evidence control room <span>তথ্য পরিচালনা</span></h1>
    <p>Manage verified agricultural references, bilingual copy, seasonal information and 90-day action tasks. All edits are access-controlled and audited.</p>
    {checking ? <p role="status">Checking account permissions…</p> : session && !authorized ? <>
      <p className="cms-notice">Signed in as {session.user.email || session.user.id}, but this account is not yet assigned as a BoponX editor. An existing owner must approve access.</p>
      <button onClick={exit}>Sign out · বের হোন</button>
    </> : <form onSubmit={login} className="cms-auth-form">
      <label>Email · ইমেইল<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label>Password · পাসওয়ার্ড<input type="password" required minLength={6} autoComplete={registering ? "new-password" : "current-password"} value={password} onChange={e => setPassword(e.target.value)} /></label>
      <button type="submit" disabled={busy}>{busy ? "Please wait…" : registering ? "Create account · অ্যাকাউন্ট খুলুন" : "Sign in · প্রবেশ করুন"}</button>
      <button type="button" className="cms-text-button" onClick={() => setRegistering(!registering)}>{registering ? "Already registered? Sign in" : "Request an editor account"}</button>
    </form>}
    {message && <p className="cms-success" role="status">{message}</p>}
    {error && <p className="cms-error" role="alert">{error}</p>}
    <small>Admin accounts never self-approve. Only users granted a database role can edit content.</small>
  </section></main>;

  return <main className="cms-shell">
    <header className="cms-head"><div><p className="cms-eyebrow">SECURE EVIDENCE CMS · নিরাপদ তথ্য ব্যবস্থাপনা</p>
      <h1>Admin workspace</h1><p>Database-backed create, read, update and delete; publication review; action log.</p></div>
      <div className="cms-head-actions"><span>{session.user.email}</span><button onClick={exit} disabled={busy}>Sign out</button></div>
    </header>
    <div className="cms-metrics">
      <div><strong>{counts.all}</strong><span>All records · মোট</span></div>
      <div><strong>{counts.approved}</strong><span>Public · প্রকাশিত</span></div>
      <div><strong>{counts.draft}</strong><span>Needs review · খসড়া</span></div>
      <div><strong>{audit.length}</strong><span>Recent audit events</span></div>
    </div>
    {error && <p className="cms-error" role="alert">{error}</p>}
    {message && <p className="cms-success" role="status">{message}</p>}
    <div className="cms-workspace">
      <section className="cms-record-list" aria-label="Data records">
        <div className="cms-list-tools">
          <label>Content type · তথ্যের ধরন<select value={group} onChange={e => setGroup(e.target.value as GroupName | "all")}>
            <option value="all">All types · সব ধরনের</option>{GROUPS.map(g => <option key={g} value={g}>{LABELS[g]}</option>)}
          </select></label>
          <label>Search · খুঁজুন<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="District, crop, code…" /></label>
          <button onClick={createNew} className="cms-primary" disabled={busy}>+ Add new · নতুন যোগ</button>
        </div>
        <p className="cms-count">{visible.length} matching records</p>
        <div className="cms-record-scroll">{visible.map(item => <button type="button" className={"cms-record " + (item.id === selectedId ? "selected" : "")} key={item.id} onClick={() => pick(item)}>
          <span className={"cms-state " + item.review_state}>{item.review_state}</span>
          <strong>{item.title_bn || item.title_en}</strong>
          <small>{item.title_en} · {item.category} · {item.code}</small>
        </button>)}</div>
      </section>
      <section className="cms-editor" aria-label="Edit selected evidence">
        <form onSubmit={save}><div className="cms-editor-title"><div><p className="cms-eyebrow">{selectedId ? "EDIT RECORD" : "NEW RECORD"}</p><h2>{selectedId ? "Update evidence" : "Add evidence"} <span>তথ্য সম্পাদনা</span></h2></div>
          <span className="cms-state">{draft.review_state}</span></div>
          <div className="cms-form-grid">
            <label>Category · বিভাগ<select value={draft.category} onChange={e => change("category",e.target.value as GroupName)}>{GROUPS.map(g=><option key={g} value={g}>{LABELS[g]}</option>)}</select></label>
            <label>Unique code · শনাক্তকারী<input required value={draft.code} onChange={e => change("code",e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g,"-"))} placeholder="e.g. rajshahi-mustard" /></label>
            <label>English title · ইংরেজি নাম<input required value={draft.title_en} onChange={e => change("title_en",e.target.value)} /></label>
            <label>বাংলা শিরোনাম · Bangla title<input lang="bn" value={draft.title_bn} onChange={e => change("title_bn",e.target.value)} /></label>
            <label className="cms-wide">English explanation · ইংরেজি ব্যাখ্যা<textarea rows={3} value={draft.summary_en} onChange={e => change("summary_en",e.target.value)} /></label>
            <label className="cms-wide">বাংলায় সহজ ব্যাখ্যা · Simple Bangla<textarea lang="bn" rows={3} value={draft.summary_bn} onChange={e => change("summary_bn",e.target.value)} /></label>
            <label>Region code · অঞ্চল<input value={draft.region_code} onChange={e => change("region_code",e.target.value)} /></label>
            <label>Crop code · ফসল<input value={draft.crop_code} onChange={e => change("crop_code",e.target.value)} /></label>
            <label>Source organization · উৎস<input value={draft.source_name} onChange={e => change("source_name",e.target.value)} /></label>
            <label>Source HTTPS URL · উৎসের লিংক<input type="url" value={draft.source_url} onChange={e => change("source_url",e.target.value)} placeholder="https://..." /></label>
            <label className="cms-wide">Structured options (JSON) · অতিরিক্ত তথ্য<textarea className="cms-code-area" spellCheck={false} rows={6} value={json} onChange={e=>setJson(e.target.value)} /></label>
            <label className="cms-wide">Publication status · প্রকাশের অবস্থা<select value={draft.review_state} onChange={e => change("review_state", e.target.value as ReviewState)}>
              <option value="draft">Draft — admin only · খসড়া</option>
              <option value="approved">Approved — public · প্রকাশিত</option>
              <option value="archived">Archived — admin only · সংরক্ষিত</option>
            </select></label>
          </div>
          <p className="cms-editor-warning">Publishing makes this entry visible to farmers. Verify crop guidance with official local evidence before approval. প্রকাশের আগে কৃষি তথ্য যাচাই করুন।</p>
          <div className="cms-form-actions"><button className="cms-primary" type="submit" disabled={busy}>{busy?"Saving…":selectedId?"Save changes · সংরক্ষণ":"Create record · যোগ করুন"}</button>
            <button type="button" onClick={createNew}>Clear</button>
            {selectedId && <button type="button" className="cms-danger" onClick={remove} disabled={busy}>Delete permanently · মুছুন</button>}
          </div>
        </form>
      </section>
    </div>
    <section className="cms-audit"><h2>Recent database activity · পরিবর্তনের ইতিহাস</h2>
      <div className="cms-audit-items">{audit.length ? audit.slice(0,20).map(row=><p key={row.id}><strong>{row.action}</strong> <span>{row.entry_id?.slice(0,8)} · {new Date(row.changed_at).toLocaleString()}</span></p>):<p>No edits recorded yet.</p>}</div>
    </section>
  </main>;
}
