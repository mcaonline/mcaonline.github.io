import { useState, useEffect, useRef } from "react";
import { apiClient, HotkeyDefinition } from "../api/client";
import Settings from "./Settings";
import { getCurrentWindow, LogicalSize } from "@tauri-apps/api/window";

export default function Panel() {
    const [hotkeys, setHotkeys] = useState<HotkeyDefinition[]>([]);
    const [uiText, setUiText] = useState<Record<string, string>>({});
    const [status, setStatus] = useState("Connecting...");
    const [lastOutput, setLastOutput] = useState("");
    const [showSettings, setShowSettings] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [history, setHistory] = useState<any[]>([]);
    const [prompt, setPrompt] = useState("");
    const [activeDefaults, setActiveDefaults] = useState<{ llm?: string, stt?: string }>({});
    const [opacity, setOpacity] = useState(0.95);
    const containerRef = useRef<HTMLDivElement>(null);

    const t = (key: string) => uiText[key] || key;

    useEffect(() => {
        const init = async (retries = 15) => {
            for (let i = 0; i < retries; i++) {
                try {
                    await apiClient.healthCheck();
                    setStatus("Connected");

                    const [hotkeyList, textCatalog, settings] = await Promise.all([
                        apiClient.getHotkeys(),
                        apiClient.getUiText(),
                        apiClient.getSettings()
                    ]);

                    setHotkeys(hotkeyList);
                    setUiText(textCatalog);
                    setActiveDefaults({
                        llm: settings?.routing_defaults?.default_llm_connection_id,
                        stt: settings?.routing_defaults?.default_stt_connection_id
                    });
                    setOpacity(settings?.app?.ui_opacity ?? 0.95);
                    return;
                } catch (e) {
                    await new Promise(r => setTimeout(r, 1000));
                }
            }
            setStatus("Offline");
        };

        init();
    }, [showSettings]);

    // Auto-resize window to content
    useEffect(() => {
        const handleResize = () => {
            if (containerRef.current) {
                // We add a bit more buffer and ensure we calculate from the glass pane if needed
                const height = containerRef.current.offsetHeight;
                const width = 900;
                // Only resize if we have a valid height to prevent "blank" windows
                if (height > 100) {
                    getCurrentWindow().setSize(new LogicalSize(width, height + 20));
                }
            }
        };

        // Resize on mount and whenever relevant state changes
        const timer = setInterval(handleResize, 500); // Check more frequently or use ResizeObserver
        handleResize();
        return () => clearInterval(timer);
    }, [showSettings, showHistory, hotkeys, lastOutput, opacity]);

    const fetchHistory = async () => {
        try {
            const data = await apiClient.getHistory();
            setHistory(data || []);
        } catch (e) {
            console.error("Failed to fetch history");
        }
    };

    const toggleHistory = () => {
        if (!showHistory) fetchHistory();
        setShowHistory(!showHistory);
    };

    const execute = async (id: string) => {
        setLastOutput("Running...");
        try {
            const res = await apiClient.executeHotkey(id);
            setLastOutput(res.result || "Done");
        } catch (e) {
            setLastOutput("Error executing hotkey");
        }
    };

    const closeApp = () => getCurrentWindow().close();

    return (
        <div className="container" ref={containerRef} style={{ background: "transparent" }}>
            <div
                className="glass-pane"
                style={{
                    background: `rgba(255, 255, 255, ${opacity})`,
                    backdropFilter: `blur(${opacity < 1 ? 10 + opacity * 15 : 0}px)`
                }}
            >
                {showSettings ? (
                    <Settings onBack={() => setShowSettings(false)} t={t} />
                ) : (
                    <>
                        <header data-tauri-drag-region style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "32px", cursor: "move" }}>
                            <div data-tauri-drag-region style={{ pointerEvents: "none" }}>
                                <h1 data-tauri-drag-region style={{ margin: 0 }}>Paste & Speech AI</h1>
                                <div style={{ display: "flex", gap: "12px", marginTop: "4px" }}>
                                    <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                                        Status: <span style={{ color: status === 'Connected' ? '#10b981' : '#f43f5e', fontWeight: 700 }}>{status}</span>
                                    </p>
                                    {status === 'Connected' && activeDefaults.llm && (
                                        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                                            &bull; AI: <span style={{ color: "var(--accent-primary)", fontWeight: 600 }}>{activeDefaults.llm}</span>
                                        </p>
                                    )}
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: "8px", pointerEvents: "auto", alignItems: "center" }}>
                                <button className="secondary" onClick={toggleHistory} style={{ padding: "8px 12px" }}>{showHistory ? "Back" : "History"}</button>
                                <button className="secondary" onClick={() => setShowSettings(true)} style={{ padding: "8px 12px" }}>Settings</button>
                                <button className="close-button" onClick={closeApp} aria-label="Close" title="Close Application">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                            </div>
                        </header>

                        {showHistory ? (
                            <div className="history-view" style={{ flex: 1, minHeight: 0 }}>
                                <h2 style={{ marginBottom: "20px" }}>Session History</h2>
                                <div style={{ display: "grid", gap: "12px" }}>
                                    {history.length === 0 && <div style={{ textAlign: "center", opacity: 0.5, padding: "20px" }}>No history recorded yet.</div>}
                                    {history.map((entry, idx) => (
                                        <div key={idx} className="hotkey-card" style={{ display: "block", padding: "16px" }}>
                                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", opacity: 0.6, marginBottom: "8px" }}>
                                                <div style={{ display: "flex", gap: "8px" }}>
                                                    <span style={{ fontWeight: 700 }}>{entry.hotkey_id}</span>
                                                    <span>&bull; {entry.model_id}</span>
                                                </div>
                                                <span>{new Date(entry.timestamp * 1000).toLocaleTimeString()} ({entry.duration.toFixed(1)}s)</span>
                                            </div>
                                            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "4px", color: "var(--text-primary)" }}>{entry.input_preview}...</div>
                                            <div style={{ fontSize: "0.85rem", opacity: 0.8, fontStyle: "italic" }}>{entry.output_preview}...</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <>
                                <div className="prompt-zone">
                                    <textarea
                                        placeholder="Enter custom instructions (e.g. 'Translate to German' or 'Fix grammar')"
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                    />
                                    <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "8px", opacity: 0.8 }}>
                                        {t("trust.ai_mistakes_notice")}
                                    </div>
                                </div>

                                <div className="hotkey-list" style={{ flex: 1, minHeight: 0 }}>
                                    <h2 style={{ marginBottom: "20px", borderBottom: "1px solid var(--glass-border)", paddingBottom: "10px" }}>Hotkeys</h2>
                                    {hotkeys.map((hk) => {
                                        const needsLLM = hk.mode === 'ai_transform' || hk.capability_requirements?.some(r => r.capability === 'llm');
                                        const needsSTT = hk.capability_requirements?.some(r => r.capability === 'stt');

                                        const isMissingConfig = (needsLLM && !activeDefaults.llm) || (needsSTT && !activeDefaults.stt);
                                        // OCR is mostly local for now or falls back, but we can check if it's explicitly required

                                        const isDisabled = !hk.enabled || status !== "Connected" || isMissingConfig;

                                        return (
                                            <div key={hk.id || hk.display_key} className="hotkey-card" style={{ opacity: isMissingConfig ? 0.6 : 1 }}>
                                                <div style={{ paddingRight: "20px", flex: 1 }}>
                                                    <div style={{ fontWeight: 700, fontSize: "1.05rem", display: "flex", alignItems: "center", gap: "8px" }}>
                                                        {t(hk.display_key)}
                                                        {isMissingConfig && (
                                                            <span style={{ fontSize: "0.7rem", backgroundColor: "rgba(244, 63, 94, 0.1)", color: "#f43f5e", padding: "2px 6px", borderRadius: "4px" }}>
                                                                Unconfigured
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>{t(hk.description_key)}</div>
                                                </div>
                                                <button
                                                    onClick={() => execute(hk.id!)}
                                                    disabled={isDisabled}
                                                    style={{ minWidth: "80px" }}
                                                >
                                                    {isMissingConfig ? "Setup AI" : "Run"}
                                                </button>
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="output-area" style={{ marginTop: "40px" }}>
                                    <h2 style={{ fontSize: "1.1rem", marginBottom: "12px", color: "var(--accent-primary)" }}>Latest Output</h2>
                                    <pre style={{ maxHeight: "150px", overflowY: "auto", whiteSpace: "pre-wrap" }}>
                                        {lastOutput || "Press a hotkey to see results..."}
                                    </pre>
                                </div>
                            </>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
