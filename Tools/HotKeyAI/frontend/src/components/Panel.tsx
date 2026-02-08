
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
        const handleResize = () => {
            if (containerRef.current) {
                // Measure content height
                const contentHeight = containerRef.current.scrollHeight;
                const height = Math.min(800, contentHeight + 40); // Cap at 800px, add buffer
                const width = 800; // Standard width

                // Only resize if significantly different to avoid jitter
                // For settings, we might want a fixed larger size
                if (showSettings) {
                    getCurrentWindow().setSize(new LogicalSize(width, 600));
                } else {
                    if (height > 100) {
                        getCurrentWindow().setSize(new LogicalSize(width, height));
                    }
                }
            }
        };

        // Resize immediately and then on interval/change
        handleResize();
        const timer = setInterval(handleResize, 200); // Check more frequently
        return () => clearInterval(timer);
    }, [showSettings, state.hotkeys, state.lastOutput, state.connections, prompt]); // Add dependencies that change height

    const execute = async (id: string) => {
        try {
            await apiClient.executeHotkey(id, { prompt });
            // Ideally we'd show a "Working..." state here, but for now we rely on the output area update
            // or the backend pushing an update.
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
        <div className="container" ref={containerRef} style={{ background: "transparent" }}>
            <div
                className="glass-pane"
                style={{
                    background: `rgba(var(--bg-rgb), ${opacity})`,
                    backdropFilter: `blur(${opacity < 1 ? 10 + opacity * 15 : 0}px)`
                }}
            >
                {showSettings ? (
                    <Settings onBack={() => setShowSettings(false)} />
                ) : (
                    <>
                        {/* Header */}
                        <header data-tauri-drag-region style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "24px", cursor: "move" }}>
                            <div data-tauri-drag-region style={{ pointerEvents: "none" }}>
                                <h1 data-tauri-drag-region style={{ margin: 0 }}>Paste & Speech AI</h1>
                                <div style={{ display: "flex", gap: "12px", marginTop: "4px" }}>
                                    <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                                        Status: <span style={{ color: isConnected ? '#10b981' : '#f43f5e', fontWeight: 700 }}>{state.status}</span>
                                    </p>
                                    {isConnected && activeLLM && (
                                        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                                            &bull; AI: <span style={{ color: "var(--accent-primary)", fontWeight: 600 }}>{activeLLM}</span>
                                        </p>
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
                        <div className="prompt-zone" style={{ marginBottom: "24px", display: "flex", gap: "16px" }}>
                            <div style={{ flex: 1 }}>
                                <textarea
                                    className="prompt-input"
                                    placeholder="Enter instructions..."
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    style={{ width: "100%", height: "80px", resize: "none", padding: "12px", borderRadius: "8px", border: "1px solid var(--glass-border)", background: "rgba(255,255,255,0.5)" }}
                                />
                                <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px", opacity: 0.8 }}>
                                    {t("trust.ai_mistakes_notice")}
                                </div>
                            </div>
                            {/* Preview Card Mockup */}
                            <div style={{ width: "200px", height: "80px", background: "rgba(0,0,0,0.03)", borderRadius: "8px", border: "1px dashed var(--glass-border)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                Source Preview
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
