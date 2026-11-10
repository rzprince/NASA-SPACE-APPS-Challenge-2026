import { useCallback, useEffect, useRef, useState, type FormEvent, type PointerEvent as ReactPointerEvent } from "react";
import type { ChatAction, ChatResponse, ChatSnapshot } from "./api";
import { ApiError, apiPost } from "./api";

type Language = "en" | "bn";
type Message = {
  id: number;
  role: "assistant" | "user";
  text: string;
  suggestions?: string[];
  choices?: string[];
  progress?: string[];
  pending?: string | null;
  intent?: string;
};
type ActionResult = { ok: boolean; message?: string };
type SpeechResultEvent = { results: ArrayLike<ArrayLike<{ transcript: string }>> };
type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};
type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
};

type Props = {
  lang: Language;
  location: string;
  availableAreas: string[];
  snapshot: ChatSnapshot;
  onLanguageChange: (language: Language) => void;
  onAction: (action: ChatAction) => Promise<ActionResult>;
};

const WELCOME: Record<Language, string> = {
  en: "Hello! Ask about BoponX, the data and evidence on your dashboard, or how to use any site feature. I can also update your field details and create or print a plan. Type or speak naturally; I’ll say when information is unavailable.",
  bn: "স্বাগতম! বপনএক্স, ড্যাশবোর্ডের ডেটা ও প্রমাণ, অথবা ওয়েবসাইটের যেকোনো সুবিধা ব্যবহার সম্পর্কে জিজ্ঞাসা করুন। মাঠের তথ্য বদলানো এবং পরিকল্পনা তৈরি বা প্রিন্ট করতেও পারি। কোনো তথ্য অনুপলভ্য হলে তা স্পষ্ট বলব।",
};

const COMMANDS: Record<Language, string[]> = {
  en: [
    "Read my dashboard",
    "What is BoponX?",
    "What data do you use?",
    "What should I do next?",
    "Select a field or district",
    "Show rain layer",
    "Show soil moisture layer",
    "Set map date to 14 days ago",
    "Use the village/street map",
    "Switch to 2D map",
    "Set overlay opacity to 50%",
    "Open Rotation Lab",
    "Open the 90-day plan",
    "Generate my plan",
    "Set my crop to rice",
    "Set water source to rainfed",
    "Show official sources",
    "Switch to Bangla",
  ],
  bn: [
    "আমার ড্যাশবোর্ডের সারাংশ দিন",
    "বপনএক্স কী?",
    "কোন ডেটা ব্যবহার করেন?",
    "এখন কী করব?",
    "একটি মাঠ বা জেলা নির্বাচন করুন",
    "বৃষ্টির মানচিত্র দেখান",
    "মাটির আর্দ্রতা স্তর দেখান",
    "মানচিত্রের তারিখ ১৪ দিন আগে করুন",
    "গ্রাম/রাস্তার মানচিত্র ব্যবহার করুন",
    "2D মানচিত্রে যান",
    "ওভারলে স্বচ্ছতা ৫০% করুন",
    "রোটেশন ল্যাব খুলুন",
    "৯০ দিনের পরিকল্পনা খুলুন",
    "আমার পরিকল্পনা তৈরি করুন",
    "আমার ফসল ধান নির্ধারণ করুন",
    "পানির উৎস বৃষ্টিনির্ভর করুন",
    "সরকারি উৎস দেখান",
    "ইংরেজিতে পরিবর্তন করুন",
  ],
};

const ACTION_TITLES: Record<string, Record<Language, string>> = {
  selectPlace: { en: "Field selected", bn: "মাঠ নির্বাচন হয়েছে" },
  selectPoint: { en: "Point selected", bn: "বিন্দু নির্বাচন হয়েছে" },
  locateMe: { en: "Location requested", bn: "অবস্থানের অনুরোধ করা হয়েছে" },
  setActiveLayer: { en: "Map layer updated", bn: "মানচিত্র স্তর বদলেছে" },
  setMapDate: { en: "Map date updated", bn: "মানচিত্রের তারিখ বদলেছে" },
  setMapStyle: { en: "Base map updated", bn: "ভিত্তি মানচিত্র বদলেছে" },
  setMapProjection: { en: "Map view updated", bn: "মানচিত্রের দৃশ্য বদলেছে" },
  setMapOpacity: { en: "Overlay opacity updated", bn: "ওভারলে স্বচ্ছতা বদলেছে" },
  setCameraPreset: { en: "Map camera moved; the exact previous position cannot be restored", bn: "মানচিত্র সরেছে; আগের নির্দিষ্ট অবস্থান ফেরানো যাবে না" },
  setPlanStartDate: { en: "Plan start date updated", bn: "পরিকল্পনার শুরুর তারিখ বদলেছে" },
  selectStrategy: { en: "Rotation strategy selected", bn: "ফসল পর্যায়ের কৌশল নির্বাচন হয়েছে" },
  setClimateScenario: { en: "What-if scenario updated (not a forecast)", bn: "সিমুলেশন বদলেছে (পূর্বাভাস নয়)" },
  setIntendedCrop: { en: "Crop recorded", bn: "ফসল নথিভুক্ত হয়েছে" },
  addPreviousCrop: { en: "Previous crop recorded", bn: "আগের ফসল নথিভুক্ত হয়েছে" },
  removePreviousCrop: { en: "Previous crop removed", bn: "আগের ফসল সরানো হয়েছে" },
  runPlan: { en: "Plan generated", bn: "পরিকল্পনা তৈরি হয়েছে" },
  navigate: { en: "Page opened", bn: "পাতা খোলা হয়েছে" },
  setSoilPh: { en: "Soil-test pH recorded", bn: "মাটি পরীক্ষার pH নথিভুক্ত হয়েছে" },
};

function localError(error: unknown, lang: Language) {
  if (error instanceof ApiError) {
    if (error.status === 429) return lang === "bn" ? "অনেক অনুরোধ হয়েছে। একটু পরে আবার চেষ্টা করুন।" : "Too many requests. Please try again shortly.";
    if (error.status === 0) return lang === "bn" ? "সহকারী সার্ভারে সংযোগ নেই। আবার চেষ্টা করুন।" : "The assistant service is offline. Please retry.";
    return lang === "bn" ? "অনুরোধটি সম্পন্ন করা যায়নি। আবার চেষ্টা করুন।" : "The request could not be completed. Please try again.";
  }
  return lang === "bn" ? "অনুরোধটি সম্পন্ন করা যায়নি।" : "I could not complete that request.";
}

export default function BoponXAssistant({
  lang,
  location,
  availableAreas,
  snapshot,
  onLanguageChange,
  onAction,
}: Props) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const [quickMenuOpen, setQuickMenuOpen] = useState(false);
  const [autocomplete, setAutocomplete] = useState<string[]>([]);
  const [retryMessage, setRetryMessage] = useState("");
  const [panelPosition, setPanelPosition] = useState<{ left: number; top: number } | null>(null);
  const [draggingPanel, setDraggingPanel] = useState(false);
  const [launcherPosition, setLauncherPosition] = useState<{ left: number; top: number } | null>(null);
  const [draggingLauncher, setDraggingLauncher] = useState(false);
  const messageId = useRef(0);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const launcherRef = useRef<HTMLButtonElement | null>(null);
  const dragOrigin = useRef<{ pointerId: number; x: number; y: number; left: number; top: number } | null>(null);
  const launcherDragOrigin = useRef<{ pointerId: number; x: number; y: number; left: number; top: number } | null>(null);
  const launcherDidMove = useRef(false);
  const actionRef = useRef(onAction);
  actionRef.current = onAction;

  const clampPanelPosition = useCallback((left: number, top: number) => {
    const panel = document.getElementById("boponx-assistant-panel");
    const width = panel?.offsetWidth ?? Math.min(390, window.innerWidth - 24);
    const height = panel?.offsetHeight ?? Math.min(580, window.innerHeight - 128);
    return {
      left: Math.max(8, Math.min(left, window.innerWidth - width - 8)),
      top: Math.max(8, Math.min(top, window.innerHeight - height - 8)),
    };
  }, []);

  const clampLauncherPosition = useCallback((left: number, top: number) => {
    const launcher = launcherRef.current;
    const width = launcher?.offsetWidth ?? 68;
    const height = launcher?.offsetHeight ?? 68;
    return {
      left: Math.max(8, Math.min(left, window.innerWidth - width - 8)),
      top: Math.max(8, Math.min(top, window.innerHeight - height - 8)),
    };
  }, []);

  const placePanelNearLauncher = useCallback((left: number, top: number, width: number, height: number) => {
    const panel = document.getElementById("boponx-assistant-panel");
    const panelWidth = panel?.offsetWidth ?? Math.min(390, window.innerWidth - 24);
    const panelHeight = panel?.offsetHeight ?? Math.min(580, window.innerHeight - 128);
    const panelTop = top >= panelHeight + 16 ? top - panelHeight - 14 : top + height + 14;
    setPanelPosition(clampPanelPosition(left + width - panelWidth, panelTop));
  }, [clampPanelPosition]);

  function startPanelDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (event.button !== 0) return;
    const panel = document.getElementById("boponx-assistant-panel");
    if (!panel) return;
    event.preventDefault();
    const rect = panel.getBoundingClientRect();
    dragOrigin.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      left: rect.left,
      top: rect.top,
    };
    setDraggingPanel(true);
  }

  function startLauncherDrag(event: ReactPointerEvent<HTMLButtonElement>) {
    if (event.button !== 0 || !launcherRef.current) return;
    event.preventDefault();
    const rect = launcherRef.current.getBoundingClientRect();
    launcherDragOrigin.current = {
      pointerId: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      left: rect.left,
      top: rect.top,
    };
    launcherDidMove.current = false;
    setDraggingLauncher(true);
  }

  function toggleAssistant() {
    if (launcherDidMove.current) {
      launcherDidMove.current = false;
      return;
    }
    if (!open && launcherPosition) {
      const launcher = launcherRef.current?.getBoundingClientRect();
      if (launcher) placePanelNearLauncher(launcher.left, launcher.top, launcher.width, launcher.height);
    }
    setOpen((current) => !current);
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy, open]);

  useEffect(() => {
    if (!draggingPanel) return;
    const handlePointerMove = (event: PointerEvent) => {
      const origin = dragOrigin.current;
      if (!origin || event.pointerId !== origin.pointerId) return;
      setPanelPosition(clampPanelPosition(
        origin.left + event.clientX - origin.x,
        origin.top + event.clientY - origin.y,
      ));
    };
    const stopDragging = (event: PointerEvent) => {
      if (dragOrigin.current?.pointerId !== event.pointerId) return;
      dragOrigin.current = null;
      setDraggingPanel(false);
    };
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopDragging);
    window.addEventListener("pointercancel", stopDragging);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopDragging);
      window.removeEventListener("pointercancel", stopDragging);
    };
  }, [clampPanelPosition, draggingPanel]);

  useEffect(() => {
    if (!draggingLauncher) return;
    const handlePointerMove = (event: PointerEvent) => {
      const origin = launcherDragOrigin.current;
      if (!origin || event.pointerId !== origin.pointerId) return;
      const dx = event.clientX - origin.x;
      const dy = event.clientY - origin.y;
      if (!launcherDidMove.current && Math.hypot(dx, dy) < 5) return;
      launcherDidMove.current = true;
      const position = clampLauncherPosition(origin.left + dx, origin.top + dy);
      setLauncherPosition(position);
      if (open) {
        const launcher = launcherRef.current?.getBoundingClientRect();
        placePanelNearLauncher(position.left, position.top, launcher?.width ?? 68, launcher?.height ?? 68);
      }
    };
    const stopDragging = (event: PointerEvent) => {
      if (launcherDragOrigin.current?.pointerId !== event.pointerId) return;
      launcherDragOrigin.current = null;
      setDraggingLauncher(false);
    };
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopDragging);
    window.addEventListener("pointercancel", stopDragging);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopDragging);
      window.removeEventListener("pointercancel", stopDragging);
    };
  }, [clampLauncherPosition, draggingLauncher, open, placePanelNearLauncher]);

  useEffect(() => {
    if (!panelPosition && !launcherPosition) return;
    const keepAssistantInView = () => {
      setPanelPosition((position) =>
        position ? clampPanelPosition(position.left, position.top) : position,
      );
      setLauncherPosition((position) =>
        position ? clampLauncherPosition(position.left, position.top) : position,
      );
    };
    window.addEventListener("resize", keepAssistantInView);
    return () => window.removeEventListener("resize", keepAssistantInView);
  }, [clampLauncherPosition, clampPanelPosition, launcherPosition, panelPosition]);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        setQuickMenuOpen(false);
        launcherRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  useEffect(() => () => recognitionRef.current?.stop(), []);

  useEffect(() => {
    const value = draft.trim().toLocaleLowerCase();
    if (!value) {
      setAutocomplete([]);
      return;
    }
    const timer = window.setTimeout(() => {
      const candidates = [
        ...COMMANDS.en,
        ...COMMANDS.bn,
        ...availableAreas.map((area) => `Select ${area}`),
      ];
      setAutocomplete(
        candidates
          .filter((command) => command.toLocaleLowerCase().startsWith(value) || command.toLocaleLowerCase().includes(value))
          .slice(0, 4),
      );
    }, 180);
    return () => window.clearTimeout(timer);
  }, [availableAreas, draft]);

  function addMessage(message: Omit<Message, "id">) {
    const id = messageId.current++;
    setMessages((current) => [...current, { ...message, id }]);
  }

  function updateMessage(id: number, patch: Partial<Message>) {
    setMessages((current) => current.map((message) => message.id === id ? { ...message, ...patch } : message));
  }

  async function executeActions(actions: ChatAction[], messageIdForProgress: number) {
    const completed: string[] = [];
    for (const action of actions) {
      if (action.type === "guidedTour") {
        const tourSteps = [
          { view: "earth", text: lang === "bn" ? "১/৩: মাঠ নির্বাচন ও NASA মানচিত্র স্তর।" : "1/3: Choose a field and explore NASA map layers." },
          { view: "rotation", text: lang === "bn" ? "২/৩: কৃষকের তথ্য ও রোটেশন ল্যাব।" : "2/3: Add farmer details in the Rotation Lab." },
          { view: "plan", text: lang === "bn" ? "৩/৩: ৯০ দিনের পরিকল্পনা পর্যালোচনা ও প্রিন্ট।" : "3/3: Review and print your 90-day plan." },
        ];
        for (const step of tourSteps) {
          const result = await actionRef.current({ type: "navigate", payload: { view: step.view } });
          if (!result.ok) {
            updateMessage(messageIdForProgress, { progress: [...completed, result.message ?? localError(null, lang)] });
            return false;
          }
          completed.push(step.text);
          updateMessage(messageIdForProgress, { progress: [...completed] });
          await new Promise((resolve) => window.setTimeout(resolve, 750));
        }
        continue;
      }

      const result = await actionRef.current(action);
      if (!result.ok) {
        const stopped = lang === "bn" ? `এখানে থেমেছি: ${result.message ?? "কাজটি করা যায়নি।"}` : `Stopped here: ${result.message ?? "That step could not be completed."}`;
        updateMessage(messageIdForProgress, { progress: [...completed, stopped] });
        return false;
      }
      const successTitle = ACTION_TITLES[action.type]?.[lang] ?? action.label ?? (lang === "bn" ? "সম্পন্ন" : "Done");
      completed.push(`✓ ${successTitle}`);
      updateMessage(messageIdForProgress, { progress: [...completed] });
      if (action.type === "setLanguage") {
        const target = action.payload?.lang;
        if (target === "en" || target === "bn") onLanguageChange(target);
      }
    }
    return true;
  }

  async function handleMessage(raw: string) {
    const query = raw.trim();
    if (!query || busy) return;
    setDraft("");
    setAutocomplete([]);
    setSpeechError("");
    setRetryMessage("");
    addMessage({ role: "user", text: query });
    setBusy(true);

    try {
      const history = messages.slice(-10).map((item) => ({
        role: item.role,
        content: item.text,
        pending: item.pending ?? null,
        intent: item.intent ?? null,
      }));
      const response = await apiPost<ChatResponse>("/api/v1/assistant/chat", {
        message: query,
        lang,
        history,
        snapshot,
      });
      const assistantId = messageId.current++;
      setMessages((current) => [
        ...current,
        {
          id: assistantId,
          role: "assistant",
          text: response.reply,
          suggestions: response.suggestions,
          choices: response.choices,
          pending: response.pending,
          intent: response.intent,
        },
      ]);
      if (response.actions.length) {
        await executeActions(response.actions, assistantId);
      }
    } catch (error) {
      const failure = localError(error, lang);
      addMessage({ role: "assistant", text: failure });
      if (error instanceof ApiError && error.status === 0) setRetryMessage(query);
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleMessage(draft);
  }

  function startListening() {
    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setSpeechError(lang === "bn" ? "এই ব্রাউজারে ভয়েস ইনপুট নেই। Chrome বা Edge ব্যবহার করুন।" : "Voice input is not supported in this browser. Try Chrome or Edge.");
      return;
    }
    recognitionRef.current?.stop();
    setSpeechError("");
    const recognition = new Recognition();
    recognition.lang = lang === "bn" ? "bn-BD" : "en-US";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim();
      setListening(false);
      if (transcript) void handleMessage(transcript);
    };
    recognition.onerror = () => {
      setListening(false);
      setSpeechError(lang === "bn" ? "ভয়েস শনাক্ত করা যায়নি। আবার চেষ্টা করুন।" : "Could not recognize speech. Please try again.");
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setListening(true);
    } catch {
      setListening(false);
      setSpeechError(lang === "bn" ? "মাইক্রোফোন চালু করা যায়নি।" : "Could not start the microphone.");
    }
  }

  const quickActions = [
    {
      group: lang === "bn" ? "মাঠ" : "Field",
      commands: lang === "bn" ? ["মানচিত্র খোলো", "আমার অবস্থান নির্বাচন করুন", "রাজশাহী নির্বাচন করুন"] : ["Open map", "Use my location", "Select Rajshahi"],
    },
    {
      group: lang === "bn" ? "ডেটা" : "Data",
      commands: lang === "bn"
        ? ["আমার ড্যাশবোর্ডের সারাংশ দিন", "বৃষ্টির মানচিত্র দেখান", "মাটির আর্দ্রতা স্তর দেখান", "NASA ডেটা আবার লোড করুন"]
        : ["Read my dashboard", "Show rain layer", "Show soil moisture layer", "Retry NASA data"],
    },
    {
      group: lang === "bn" ? "কৃষি তথ্য" : "Farm questions",
      commands: lang === "bn"
        ? ["আমার ফসল ধান নির্ধারণ করুন", "গত মৌসুমে ধান চাষ করেছি", "আগের ফসল থেকে ধান সরান", "পানির উৎস বৃষ্টিনির্ভর করুন", "ভারী বৃষ্টির পর পানি জমে থাকে", "পানি সাশ্রয় অগ্রাধিকার", "মাটি পরীক্ষা নিশ্চিত নই", "যন্ত্রপাতি সনাতন", "স্থানীয় বাজার লক্ষ্য"]
        : ["Set rice as my crop", "I grew rice last season", "Remove rice from previous crops", "Set water source to rainfed", "Water stays after heavy rain", "Prioritize water saving", "Soil test not sure", "Equipment is manual", "Local market goal"],
    },
    {
      group: lang === "bn" ? "পরিকল্পনা" : "Plan",
      commands: lang === "bn"
        ? ["রোটেশন ল্যাব খুলুন", "পরিকল্পনা ডিসেম্বর থেকে শুরু করুন", "পরিকল্পনার বছর 2027 করুন", "আমার পরিকল্পনা তৈরি করুন", "আমার পরিকল্পনা প্রিন্ট করুন", "সরকারি কৃষি হেল্পলাইন"]
        : ["Open Rotation Lab", "Plan from December", "Set plan year to 2027", "Generate my plan", "Print my plan", "Open the agricultural helpline"],
    },
    {
      group: lang === "bn" ? "ভাষা" : "Language",
      commands: lang === "bn" ? ["ইংরেজিতে পরিবর্তন করুন"] : ["Switch to Bangla"],
    },
  ];

  return (
    <div
      className={`boponx-assistant no-print ${draggingPanel ? "assistant-is-dragging" : ""} ${draggingLauncher ? "assistant-launcher-is-dragging" : ""}`}
      style={launcherPosition ? { left: launcherPosition.left, top: launcherPosition.top, right: "auto", bottom: "auto" } : undefined}
    >
      {open && (
        <section
          id="boponx-assistant-panel"
          className="assistant-panel"
          aria-label={lang === "bn" ? "বপনএক্স মাঠ সহকারী" : "BoponX field assistant"}
          aria-modal="false"
          style={panelPosition ? { position: "fixed", left: panelPosition.left, top: panelPosition.top, right: "auto", bottom: "auto" } : undefined}
        >
          <header className="assistant-header">
            <button
              type="button"
              className="assistant-drag-handle"
              aria-label={lang === "bn" ? "সহকারী সরাতে ধরে টানুন" : "Drag to move the assistant"}
              title={lang === "bn" ? "ধরে টেনে সরান" : "Drag to move"}
              onPointerDown={startPanelDrag}
              onKeyDown={(event) => {
                if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) return;
                event.preventDefault();
                const panel = document.getElementById("boponx-assistant-panel");
                const rect = panel?.getBoundingClientRect();
                if (!rect) return;
                const step = event.shiftKey ? 48 : 20;
                const delta = {
                  ArrowLeft: [-step, 0],
                  ArrowRight: [step, 0],
                  ArrowUp: [0, -step],
                  ArrowDown: [0, step],
                }[event.key];
                if (delta) setPanelPosition(clampPanelPosition(rect.left + delta[0], rect.top + delta[1]));
              }}
            >
              <span aria-hidden="true">⠿</span>
            </button>
            <img src="/boponx-logo-icon.png" alt="" />
            <div className="assistant-header-copy">
              <strong>{lang === "bn" ? "বপনএক্স সহকারী" : "BoponX Assistant"}</strong>
              <span>{lang === "bn" ? "ড্যাশবোর্ড-সচেতন · সরাতে ধরে টানুন" : "Dashboard-aware · drag to move"}</span>
            </div>
            <div className="assistant-language" role="group" aria-label={lang === "bn" ? "সহকারীর ভাষা" : "Assistant language"}>
              <button type="button" className={lang === "en" ? "active" : ""} onClick={() => onLanguageChange("en")} aria-pressed={lang === "en"}>EN</button>
              <button type="button" className={lang === "bn" ? "active" : ""} onClick={() => onLanguageChange("bn")} aria-pressed={lang === "bn"}>বাং</button>
            </div>
            {panelPosition && (
              <button
                type="button"
                className="assistant-reset-position"
                aria-label={lang === "bn" ? "সহকারীর আগের অবস্থানে ফিরুন" : "Reset assistant position"}
                title={lang === "bn" ? "অবস্থান রিসেট" : "Reset position"}
                onClick={() => setPanelPosition(null)}
              >
                ↙
              </button>
            )}
            <button type="button" className="assistant-close" aria-label={lang === "bn" ? "সহকারী বন্ধ করুন" : "Close assistant"} onClick={() => { setOpen(false); launcherRef.current?.focus(); }}>×</button>
          </header>
          <div className="assistant-context">
            <span className="assistant-live-dot" />
            <span>{location}</span>
            <span>·</span>
            <span>{lang === "bn" ? "উৎস-ভিত্তিক সহায়তা" : "Evidence-aware help"}</span>
          </div>
          {((snapshot.fieldData as { dataStatus?: string } | undefined)?.dataStatus === "loading" ||
            (snapshot.fieldData as { dataStatus?: string } | undefined)?.dataStatus === "unavailable") && (
            <div className="assistant-data-state" role="status">
              {(snapshot.fieldData as { dataStatus?: string }).dataStatus === "loading"
                ? (lang === "bn" ? "NASA ডেটা লোড হচ্ছে…" : "Loading NASA data…")
                : (lang === "bn" ? "NASA ডেটা অনুপলভ্য। “আবার চেষ্টা” বলুন।" : "NASA data unavailable. Say “retry” to try again.")}
            </div>
          )}
          <div className="assistant-messages" aria-live="polite">
            {messages.length === 0 && <div className="assistant-message assistant-response">{WELCOME[lang]}</div>}
            {messages.map((message) => (
              <div key={message.id} className={`assistant-message-wrap ${message.role === "user" ? "assistant-user-wrap" : ""}`}>
                <div className={`assistant-message ${message.role === "user" ? "assistant-user" : "assistant-response"}`}>{message.text}</div>
                {!!message.progress?.length && (
                  <div className="assistant-progress" aria-live="polite">
                    {message.progress.map((step, index) => <span key={`${message.id}-${index}`}>{step}</span>)}
                  </div>
                )}
                {!!message.choices?.length && (
                  <div className="assistant-prompts assistant-choice-chips">
                    {message.choices.map((choice) => <button key={choice} type="button" onClick={() => void handleMessage(choice)}>{choice}</button>)}
                  </div>
                )}
                {!!message.suggestions?.length && (
                  <div className="assistant-prompts">
                    {message.suggestions.map((suggestion) => <button key={suggestion} type="button" onClick={() => void handleMessage(suggestion)}>{suggestion}</button>)}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="assistant-thinking" role="status">{lang === "bn" ? "একটু অপেক্ষা করুন…" : "Working…"}</div>}
            <div ref={endRef} />
          </div>
          {messages.length === 0 && (
            <div className="assistant-prompts">
              {(lang === "bn" ? ["বৃষ্টির মানচিত্র দেখান", "মাটির আর্দ্রতা কেমন?", "রোটেশন ল্যাব খুলুন"] : ["Show rain layer", "How is soil moisture?", "Open Rotation Lab"]).map((prompt) => (
                <button type="button" key={prompt} onClick={() => void handleMessage(prompt)}>{prompt}</button>
              ))}
            </div>
          )}
          {quickMenuOpen && (
            <div className="assistant-quick-menu" aria-label={lang === "bn" ? "দ্রুত কাজ" : "Quick actions"}>
              {quickActions.map((section) => (
                <div key={section.group}>
                  <strong>{section.group}</strong>
                  <div className="assistant-prompts">
                    {section.commands.map((command) => <button type="button" key={command} onClick={() => { setQuickMenuOpen(false); void handleMessage(command); }}>{command}</button>)}
                  </div>
                </div>
              ))}
            </div>
          )}
          {!!autocomplete.length && (
            <div className="assistant-autocomplete assistant-prompts" aria-label={lang === "bn" ? "কমান্ড পরামর্শ" : "Command suggestions"}>
              {autocomplete.map((command) => <button key={command} type="button" onClick={() => void handleMessage(command)}>{command}</button>)}
            </div>
          )}
          {speechError && <p className="assistant-error" role="status">{speechError}</p>}
          {!!retryMessage && (
            <div className="assistant-retry">
              <span>{lang === "bn" ? "সংযোগ নেই" : "Offline"}</span>
              <button type="button" onClick={() => void handleMessage(retryMessage)}>{lang === "bn" ? "আবার চেষ্টা" : "Retry"}</button>
            </div>
          )}
          <form className="assistant-compose" onSubmit={submit}>
            <button type="button" className="assistant-menu-button" aria-label={lang === "bn" ? "দ্রুত কাজ দেখান" : "Show quick actions"} aria-expanded={quickMenuOpen} onClick={() => setQuickMenuOpen((value) => !value)}>+</button>
            <input
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={lang === "bn" ? "প্রশ্ন বা নির্দেশ লিখুন…" : "Ask or tell BoponX…"}
              aria-label={lang === "bn" ? "বার্তা লিখুন" : "Type a message"}
              disabled={busy}
            />
            <button
              type="button"
              className={`assistant-mic ${listening ? "listening" : ""}`}
              aria-label={listening ? (lang === "bn" ? "ভয়েস ইনপুট বন্ধ করুন" : "Stop voice input") : (lang === "bn" ? "ভয়েস ইনপুট শুরু করুন" : "Start voice input")}
              title={listening ? (lang === "bn" ? "শুনছি…" : "Listening…") : (lang === "bn" ? "ভয়েস ইনপুট" : "Voice input")}
              onClick={() => listening ? recognitionRef.current?.stop() : startListening()}
              disabled={busy}
            >
              {listening ? "■" : "🎙"}
            </button>
            <button className="assistant-send" type="submit" aria-label={lang === "bn" ? "বার্তা পাঠান" : "Send message"} disabled={busy || !draft.trim()}>➤</button>
          </form>
          <p className="assistant-disclaimer">
            {lang === "bn" ? "কৃষি সিদ্ধান্ত স্থানীয় কৃষি সম্প্রসারণ কর্তৃপক্ষের সাথে যাচাই করুন।" : "Verify field decisions with local agricultural extension staff."}
          </p>
        </section>
      )}
      <button
        ref={launcherRef}
        type="button"
        className={`assistant-launcher ${open ? "active" : ""}`}
        aria-label={open
          ? (lang === "bn" ? "সহকারী বন্ধ করুন; ধরে টেনে সরান" : "Close assistant; drag to move")
          : (lang === "bn" ? "বপনএক্স সহকারী খুলুন; ধরে টেনে সরান" : "Open assistant; drag to move")}
        title={lang === "bn" ? "সহকারী সরাতে ধরে টানুন" : "Drag to move the assistant"}
        aria-expanded={open}
        aria-controls="boponx-assistant-panel"
        onPointerDown={startLauncherDrag}
        onKeyDown={(event) => {
          if (!launcherPosition || !["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) return;
          event.preventDefault();
          const rect = launcherRef.current?.getBoundingClientRect();
          if (!rect) return;
          const step = event.shiftKey ? 48 : 20;
          const delta = {
            ArrowLeft: [-step, 0],
            ArrowRight: [step, 0],
            ArrowUp: [0, -step],
            ArrowDown: [0, step],
          }[event.key];
          if (delta) setLauncherPosition(clampLauncherPosition(rect.left + delta[0], rect.top + delta[1]));
        }}
        onClick={toggleAssistant}
      >
        {open ? <span className="assistant-launcher-close">×</span> : <img src="/boponx-logo-icon.png" alt="" />}
      </button>
      {launcherPosition && (
        <button
          type="button"
          className="assistant-launcher-reset"
          aria-label={lang === "bn" ? "সহকারীর বোতাম আগের অবস্থানে ফিরুন" : "Reset assistant button position"}
          title={lang === "bn" ? "বোতামের অবস্থান রিসেট" : "Reset launcher position"}
          onClick={() => setLauncherPosition(null)}
        >
          ⌖
        </button>
      )}
    </div>
  );
}
