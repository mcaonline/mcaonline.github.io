import { useState, useEffect } from "react";
import { apiClient, HotkeyDefinition } from "../api/client";
import Settings from "./Settings";

export default function Panel() {
    const [hotkeys, setHotkeys] = useState<HotkeyDefinition[]>([]);
    const [uiText, setUiText] = useState<Record<string, string>>({});
    const [status, setStatus] = useState("Connecting...");
    const [lastOutput, setLastOutput] = useState("");
    const [showSettings, setShowSettings] = useState(false);
    const [prompt, setPrompt] = useState("");

    const t = (key: string) => uiText[key] || key;

    useEffect(() => {
        const checkConnection = async (retries = 15) => {
            for (let i = 0; i < retries; i++) {
                try {
                    await apiClient.healthCheck();
                    setStatus("Connected");

                    const [hotkeyList, textCatalog] = await Promise.all([
                        apiClient.getHotkeys(),
                        apiClient.getUiText()
                    ]);

                    setHotkeys(hotkeyList);
                    setUiText(textCatalog);
                    return;
                } catch (e) {
                    await new Promise(r => setTimeout(r, 1000));
                }
            }
            setStatus("Offline");
        };

        checkConnection();
    }, []);

    const execute = async (id: string) => {
        setLastOutput("Running...");
        try {
            const res = await apiClient.executeHotkey(id);
            setLastOutput(res.result || "Done");
        } catch (e) {
            setLastOutput("Error executing hotkey");
        }
    };

    if (showSettings) {
        return <Settings onBack={() => setShowSettings(false)} t={t} />;
    }

    return (
        <div className="container">
            <div className="glass-pane">
                <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "32px" }}>
                    <div>
                        <h1>HotKeyAI</h1>
                        <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                            Status: <span style={{ color: status === 'Connected' ? '#10b981' : '#f43f5e', fontWeight: 700 }}>{status}</span>
                        </p>
                    </div>
                    <button className="secondary" onClick={() => setShowSettings(true)}>Settings</button>
                </header>

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

                <div className="hotkey-list">
                    <h2 style={{ marginBottom: "20px", borderBottom: "1px solid var(--glass-border)", paddingBottom: "10px" }}>Hotkeys</h2>
                    {hotkeys.map((hk) => (
                        <div key={hk.id || hk.display_key} className="hotkey-card">
                            <div style={{ paddingRight: "20px" }}>
                                <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>{t(hk.display_key)}</div>
                                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>{t(hk.description_key)}</div>
                            </div>
                            <button
                                onClick={() => execute(hk.id!)}
                                disabled={!hk.enabled || status !== "Connected"}
                            >
                                Run
                            </button>
                        </div>
                    ))}
                </div>

                <div className="output-area" style={{ marginTop: "40px" }}>
                    <h2 style={{ fontSize: "1.1rem", marginBottom: "12px", color: "var(--accent-primary)" }}>Latest Output</h2>
                    <pre>
                        {lastOutput || "Press a hotkey to see results..."}
                    </pre>
                </div>
            </div>
        </div>
    );
}
