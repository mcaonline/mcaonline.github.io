import { useState, useEffect } from "react";
import { apiClient, HotkeyDefinition } from "../api/client";

export default function Panel() {
    const [hotkeys, setHotkeys] = useState<HotkeyDefinition[]>([]);
    const [status, setStatus] = useState("Connecting...");
    const [lastOutput, setLastOutput] = useState("");

    useEffect(() => {
        const checkConnection = async (retries = 5) => {
            for (let i = 0; i < retries; i++) {
                try {
                    console.log(`Checking connection (attempt ${i + 1})...`);
                    await apiClient.healthCheck();
                    console.log("Connected to backend");
                    setStatus("Connected");
                    loadHotkeys();
                    return;
                } catch (e) {
                    console.warn("Backend not ready yet, retrying...", e);
                    await new Promise(r => setTimeout(r, 1000));
                }
            }
            setStatus("Offline");
        };

        checkConnection();
    }, []);

    const loadHotkeys = async () => {
        try {
            console.log("Loading hotkeys...");
            const list = await apiClient.getHotkeys();
            console.log("Hotkeys loaded:", list);
            setHotkeys(list);
        } catch (e) {
            console.error("Failed to load hotkeys:", e);
        }
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

    return (
        <div className="container" style={{ padding: "20px" }}>
            <h1>HotKeyAI Panel</h1>
            <p>Status: {status}</p>

            <div className="hotkey-list">
                <h2>Available Hotkeys</h2>
                {hotkeys.map((hk) => (
                    <div key={hk.id || hk.display_key} style={{ marginBottom: "10px", border: "1px solid #ccc", padding: "10px" }}>
                        <strong>{hk.display_key}</strong>: {hk.description_key}
                        <button onClick={() => execute(hk.id!)} style={{ marginLeft: "10px" }}>
                            Run
                        </button>
                    </div>
                ))}
            </div>

            <div className="output-area" style={{ marginTop: "20px", background: "#eee", padding: "10px" }}>
                <h3>Output:</h3>
                <pre>{lastOutput}</pre>
            </div>
        </div>
    );
}
