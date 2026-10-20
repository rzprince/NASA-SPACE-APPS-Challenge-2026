import { useEffect, useMemo, useState } from "react";
import { configured, loadEvidence, type EvidenceEntry, type GroupName } from "./boponxDb";

type Filter = GroupName | "all";
const filters: Array<{ key: Filter; label: string; emoji: string }> = [
  { key: "plan_action", label: "সহজ কাজ · Action steps", emoji: "✅" },
  { key: "district", label: "আমার জেলা · Districts", emoji: "📍" },
  { key: "crop", label: "ফসল · Crops", emoji: "🌾" },
  { key: "soil", label: "মাটি · Soil", emoji: "🌱" },
  { key: "season", label: "মৌসুম · Seasons", emoji: "☀️" },
  { key: "hazard", label: "ঝুঁকি · Risks", emoji: "⚠️" },
  { key: "source", label: "সরকারি উৎস · Sources", emoji: "📖" },
  { key: "all", label: "সব তথ্য · All", emoji: "🔎" },
];

export default function KnowledgeHub() {
  const [records, setRecords] = useState<EvidenceEntry[]>([]);
  const [filter, setFilter] = useState<Filter>("plan_action");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState<"bn" | "en">("bn");
  const [voiceMessage, setVoiceMessage] = useState("");
  useEffect(() => {
    let alive = true;
    loadEvidence().then(data => { if (alive) { setRecords(data); setLoading(false); } })
      .catch(e => { if (alive) { setError(e instanceof Error ? e.message : "Unable to load evidence."); setLoading(false); } });
    return () => { alive = false; window.speechSynthesis?.cancel(); };
  }, []);
  const visible = useMemo(() => records.filter(record => {
    const matched = filter === "all" || record.category === filter;
    return matched && (!query || (record.title_en + " " + record.title_bn + " " + record.summary_en + " " + record.summary_bn).toLowerCase().includes(query.toLowerCase()));
  }), [records, filter, query]);
  const selected = visible.find(record => record.id === selectedId) || visible[0];
  function speak(record: EvidenceEntry) {
    setVoiceMessage("");
    if (!("speechSynthesis" in window)) { setVoiceMessage("Speech is not supported in this browser. · আপনার ব্রাউজারে শব্দ চালু নেই।"); return; }
    window.speechSynthesis.cancel();
    const text = language === "bn"
      ? [record.title_bn || record.title_en, record.summary_bn || record.summary_en].filter(Boolean).join("। ")
      : [record.title_en, record.summary_en].filter(Boolean).join(". ");
    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = language === "bn" ? "bn-BD" : "en-GB";
    speech.rate = .86;
    speech.onerror = () => setVoiceMessage("Voice unavailable. Your device may need a Bangla speech voice. · বাংলা কণ্ঠের সেটিং পরীক্ষা করুন।");
    window.speechSynthesis.speak(speech);
  }
  return <main className="knowledge-shell">
    <header className="knowledge-hero">
      <div><p className="cms-eyebrow">BOPONX · PUBLIC KNOWLEDGE · অনুমোদিত তথ্য</p>
        <h1>খেতের তথ্য, <span>আপনার ভাষায়।</span></h1>
        <p>Easy farming evidence. Big text, Bangla first, optional voice and links to sources. Only reviewed records appear here.</p></div>
      <div className="knowledge-hero-tools">
        <div className="knowledge-lang" role="group" aria-label="Select language">
          <button className={language === "bn" ? "active" : ""} onClick={() => setLanguage("bn")}>বাংলা</button>
          <button className={language === "en" ? "active" : ""} onClick={() => setLanguage("en")}>English</button>
        </div>
        <p><strong>মনে রাখুন</strong> · এই তথ্য আপনার জমির মাটি পরীক্ষা বা কৃষি কর্মকর্তার পরামর্শের বিকল্প নয়।</p>
      </div>
    </header>
    <div className="knowledge-layout">
      <aside className="knowledge-browser">
        <label className="knowledge-search">খুঁজুন · Search<input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="জেলা / ফসল / district…" /></label>
        <div className="knowledge-filters" aria-label="Evidence categories">
          {filters.map(item => <button className={item.key === filter ? "active" : ""} key={item.key} onClick={() => { setFilter(item.key); setSelectedId(""); }}>
            <span aria-hidden>{item.emoji}</span>{item.label}</button>)}
        </div>
        {loading ? <p role="status">তথ্য আসছে… · Loading</p> : <p className="knowledge-count">{visible.length} verified / published entries</p>}
        <div className="knowledge-records">
          {visible.map(record => <button className={selected?.id === record.id ? "selected" : ""} key={record.id} onClick={() => setSelectedId(record.id)}>
            <strong>{language === "bn" ? record.title_bn || record.title_en : record.title_en}</strong>
            <small>{record.category === "plan_action" ? "✅ করণীয় কাজ" : record.category}</small></button>)}
        </div>
      </aside>
      <section className="knowledge-detail" aria-live="polite">
        {!configured() ? <p className="cms-error">The database connection has not been configured for this deployment.</p>
        : error ? <p role="alert" className="cms-error">{error}</p> : !selected ? <div className="knowledge-empty"><span aria-hidden>🌾</span>
          <h2>এখনও কোনো অনুমোদিত তথ্য নেই।</h2><p>No published entry matches this filter. Try another category, or check back after review.</p></div>
        : <article className="knowledge-fact">
          <p className="cms-eyebrow">APPROVED RECORD · যাচাইকৃত তালিকা</p>
          <h2 lang={language}>{language === "bn" ? selected.title_bn || selected.title_en : selected.title_en}</h2>
          <p className="knowledge-english">{language === "bn" ? selected.title_en : selected.title_bn}</p>
          <div className="knowledge-reading" lang={language}>{language === "bn"
            ? selected.summary_bn || selected.summary_en || "বিস্তারিত তথ্যের জন্য উৎস দেখুন।"
            : selected.summary_en || selected.summary_bn || "See the linked source for further details."}</div>
          <button className="knowledge-speak" onClick={() => speak(selected)}><span aria-hidden>🔊</span> {language === "bn" ? "শুনে নিন" : "Read aloud"}</button>
          {voiceMessage && <p role="status">{voiceMessage}</p>}
          {selected.category === "plan_action" && <div className="knowledge-step">📅 {language === "bn" ? "৯০ দিনের পরিকল্পনার ধাপ" : "90-day planning step"} {Number(selected.content.month_offset ?? 0) + 1}</div>}
          <div className="knowledge-source"><span>Source · তথ্যের উৎস</span>
            <strong>{selected.source_name || "BoponX evidence registry"}</strong>
            {selected.source_url ? <a href={selected.source_url} target="_blank" rel="noopener noreferrer">View evidence ↗ · উৎস দেখুন</a> : <p>Source link not attached to this label.</p>}</div>
          <p className="knowledge-caution">⚠️ Historical climate data are not weather forecasts. District-level guidance does not establish field-level soil suitability. · জমির সিদ্ধান্ত নেওয়ার আগে স্থানীয়ভাবে যাচাই করুন।</p>
        </article>}
      </section>
    </div>
  </main>;
}
