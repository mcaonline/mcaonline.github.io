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
        console.log("[Frontend] Panel Component Mounted");
        const checkConnection = async (retries = 10) => {
            console.log("[Frontend] Starting Connection Check Sequence");
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
                    console.warn("Backend not ready yet, retrying...");
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
        <div className="container" style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h1>{t("label.hotkeys")} Panel</h1>
                <button onClick={() => setShowSettings(true)} style={{ padding: "8px 16px" }}>Settings</button>
            </header>

            <p>Status: <span style={{ color: status === 'Connected' ? 'green' : 'red' }}>{status}</span></p>

            <div className="prompt-zone" style={{ marginBottom: "30px", background: "#f5f5f5", padding: "15px", borderRadius: "8px" }}>
                <textarea
                    placeholder="Enter instructions (e.g. 'Summarize this')"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    style={{ width: "100%", height: "80px", marginBottom: "10px", padding: "10px", borderRadius: "4px", border: "1px solid #ddd" }}
                />
                <div style={{ fontSize: "12px", color: "#666" }}>
                    {t("trust.ai_mistakes_notice")}
                </div>
            </div>

            <div className="hotkey-list">
                <h2>Available Hotkeys</h2>
                {hotkeys.map((hk) => (
                    <div key={hk.id || hk.display_key} style={{
                        marginBottom: "12px",
                        border: "1px solid #eee",
                        padding: "15px",
                        borderRadius: "8px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        background: hk.enabled ? "white" : "#fafafa"
                    }}>
                        <div>
                            <strong style={{ fontSize: "1.1em" }}>{t(hk.display_key)}</strong>
                            <div style={{ fontSize: "0.9em", color: "#666", marginTop: "4px" }}>{t(hk.description_key)}</div>
                        </div>
                        <button
                            onClick={() => execute(hk.id!)}
                            disabled={!hk.enabled || status !== "Connected"}
                            style={{
                                padding: "8px 20px",
                                cursor: hk.enabled ? "pointer" : "not-allowed",
                                opacity: hk.enabled ? 1 : 0.5
                            }}
                        >
                            Run
                        </button>
                    </div>
                ))}
            </div>

            <div className="output-area" style={{ marginTop: "30px", background: "#f0f7ff", padding: "20px", borderRadius: "8px", border: "1px solid #cce5ff" }}>
                <h3 style={{ marginTop: 0 }}>Output:</h3>
                <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", background: "white", padding: "15px", borderRadius: "4px", border: "1px solid #ddd" }}>
                    {lastOutput || "Results will appear here..."}
                </pre>
            </div>
        </div>
    );
}
