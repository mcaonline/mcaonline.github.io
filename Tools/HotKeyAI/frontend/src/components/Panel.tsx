
import { useState, useEffect, useRef } from "react";
import { useApp } from "../store/context";
import { apiClient } from "../api/client";
import Settings from "./Settings";
import { getCurrentWindow, LogicalSize } from "@tauri-apps/api/window";

export default function Panel() {
    const { state } = useApp();
    const [prompt, setPrompt] = useState("");
    const [showSettings, setShowSettings] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Auto-resize window
    useEffect(() => {
        const updateWindowSize = async () => {
            if (showSettings) {
                // Fixed size for settings
                await getCurrentWindow().setSize(new LogicalSize(800, 600));
            } else {
                // Dynamic size for main panel
                if (containerRef.current) {
                    const contentHeight = containerRef.current.scrollHeight;
                    // Cap at 800px height for main panel too, but usually it's smaller
                    const height = Math.min(800, contentHeight + 20);
                    await getCurrentWindow().setSize(new LogicalSize(800, height));
                }
            }
        };

        updateWindowSize();
        // Only use interval for dynamic content in main view, not settings
        let timer: ReturnType<typeof setInterval>;
        if (!showSettings) {
            timer = setInterval(updateWindowSize, 500);
        }
        return () => { if (timer) clearInterval(timer); };
    }, [showSettings, state.hotkeys, state.lastOutput, state.connections, prompt]);

    const execute = async (id: string) => {
        try {
            await apiClient.executeHotkey(id, { prompt });
        } catch (e) {
            console.error("Execution failed", e);
        }
    };

    const t = (key: string) => state.uiText[key] || key;
    const opacity = state.settings?.app?.ui_opacity ?? 0.95;

    // Derived state
    const activeLLM = state.activeDefaults.llm;
    const activeSTT = state.activeDefaults.stt;
    const isConnected = state.status === 'connected';

    return (
        <div className="container" ref={containerRef} style={{ background: "transparent", height: "100vh", overflow: "hidden" }}>
            <div
                className="glass-pane"
                style={{
                    background: `rgba(var(--bg-rgb), ${opacity})`,
                    backdropFilter: `blur(${opacity < 1 ? 10 + opacity * 15 : 0}px)`,
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    boxSizing: "border-box"
                }}
            >
                {showSettings ? (
                    <Settings onBack={() => setShowSettings(false)} />
                ) : (
                    <>
                        {/* Header */}
                        <header data-tauri-drag-region style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "24px", cursor: "move" }}>
                            <div data-tauri-drag-region style={{ pointerEvents: "none" }}>
                                <h1 data-tauri-drag-region style={{ margin: 0, fontSize: "1.2rem" }}>Paste & Speech AI</h1>
                                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "4px", pointerEvents: "auto" }}>
                                    <div style={{ fontSize: "0.8rem", color: isConnected ? "var(--text-secondary)" : "#f43f5e" }}>
                                        {isConnected ? "Ready" : "Disconnected"}
                                    </div>

                                    {/* Model Selector */}
                                    {isConnected && (
                                        <select
                                            value={state.activeDefaults.llm || ""}
                                            onChange={(e) => {
                                                if (e.target.value) {
                                                    apiClient.updateSettings({ routing_defaults: { ...state.settings?.routing_defaults, default_llm_connection_id: e.target.value } }).then(refreshData);
                                                }
                                            }}
                                            style={{
                                                fontSize: "0.75rem",
                                                padding: "2px 6px",
                                                borderRadius: "4px",
                                                border: "1px solid var(--glass-border)",
                                                background: "rgba(255,255,255,0.5)",
                                                cursor: "pointer"
                                            }}
                                        >
                                            <option value="" disabled>Select Model</option>
                                            {state.connections.filter(c => c.capabilities.includes('llm')).map(c => (
                                                <option key={c.connection_id} value={c.connection_id}>{c.connection_id}</option>
                                            ))}
                                        </select>
                                    )}
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: "8px", pointerEvents: "auto", alignItems: "center" }}>
                                <button className="secondary" onClick={() => setShowSettings(true)} style={{ padding: "6px 12px" }}>Settings</button>
                                <button className="close-button" onClick={(e) => { e.stopPropagation(); getCurrentWindow().close(); }} aria-label="Close">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                            </div>
                        </header>

                        {/* Prompt Zone */}
                        <div className="prompt-zone" style={{ marginBottom: "16px", display: "flex", gap: "12px", alignItems: "stretch" }}>
                            <div style={{ flex: 1, position: "relative" }}>
                                <textarea
                                    className="prompt-input"
                                    placeholder="Enter instructions... (Ctrl+Enter to send)"
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && e.ctrlKey) {
                                            // Default execute? We need a default 'Execute' action or just run the first AI hotkey?
                                            // For now, let's assume we run the "General AI" hotkey if available, or just log.
                                            // The user usually clicks a specific hotkey below.
                                            // If we have a 'Send' button, what does it do? It likely runs a default AI transformation.
                                            // Let's search for a generic AI hotkey or use the first one.
                                            const defaultHk = state.hotkeys.find(h => h.mode === 'ai_transform' && h.enabled);
                                            if (defaultHk) execute(defaultHk.id);
                                        }
                                    }}
                                    style={{
                                        width: "100%",
                                        height: "60px",
                                        resize: "none",
                                        padding: "10px",
                                        paddingRight: "40px",
                                        borderRadius: "8px",
                                        border: "1px solid var(--glass-border)",
                                        background: "rgba(255,255,255,0.6)",
                                        fontSize: "0.9rem",
                                        fontFamily: "inherit"
                                    }}
                                />
                                <button
                                    onClick={() => {
                                        const defaultHk = state.hotkeys.find(h => h.mode === 'ai_transform' && h.enabled);
                                        if (defaultHk) execute(defaultHk.id);
                                    }}
                                    style={{
                                        position: "absolute",
                                        right: "8px",
                                        bottom: "8px",
                                        background: "var(--accent-primary)",
                                        color: "white",
                                        border: "none",
                                        borderRadius: "4px",
                                        width: "28px",
                                        height: "28px",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        cursor: "pointer",
                                        opacity: prompt ? 1 : 0.5
                                    }}
                                    title="Run Default AI Command"
                                >
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                    </svg>
                                </button>
                            </div>
                            {/* Preview Card */}
                            <div style={{ width: "160px", background: "rgba(255,255,255,0.4)", borderRadius: "8px", border: "1px solid var(--glass-border)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                                <div style={{ fontWeight: 600, marginBottom: "4px" }}>Context</div>
                                <div>Text Selection</div>
                            </div>
                        </div>

                        {/* Hotkey List */}
                        <div className="hotkey-list" style={{ display: "grid", gap: "12px" }}>
                            <h2 style={{ fontSize: "1rem", marginBottom: "8px", borderBottom: "1px solid var(--glass-border)", paddingBottom: "4px" }}>Hotkeys</h2>
                            {state.hotkeys.map((hk) => {
                                const needsLLM = hk.mode === 'ai_transform' || hk.capability_requirements?.some(r => r.capability === 'llm');
                                const needsSTT = hk.capability_requirements?.some(r => r.capability === 'stt');
                                const isMissingConfig = (needsLLM && !activeLLM) || (needsSTT && !activeSTT);
                                const isDisabled = !hk.enabled || !isConnected || isMissingConfig;

                                return (
                                    <div key={hk.id} className="hotkey-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", opacity: isDisabled ? 0.6 : 1 }}>
                                        <div>
                                            <div style={{ fontWeight: 600, display: "flex", alignItems: "center", gap: "8px" }}>
                                                {t(hk.display_key)}
                                                {(hk as any).quick_key && <span style={{ fontSize: "0.7rem", border: "1px solid var(--text-secondary)", borderRadius: "4px", padding: "0 4px", opacity: 0.5 }}>{(hk as any).quick_key}</span>}
                                                {isMissingConfig && <span style={{ fontSize: "0.7rem", color: "#f43f5e", background: "rgba(244, 63, 94, 0.1)", padding: "2px 4px", borderRadius: "4px" }}>Setup Required</span>}
                                            </div>
                                            <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{t(hk.description_key)}</div>
                                        </div>
                                        <button disabled={isDisabled} onClick={() => execute(hk.id)} style={{ padding: "6px 12px", fontSize: "0.85rem" }}>
                                            {isMissingConfig ? "Setup" : "Run"}
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
