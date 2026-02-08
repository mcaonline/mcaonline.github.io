import { useState, useEffect } from "react";
import { apiClient, HotkeyDefinition } from "../api/client";

export default function Panel() {
    const [hotkeys, setHotkeys] = useState<HotkeyDefinition[]>([]);
    const [status, setStatus] = useState("Connecting...");
    const [lastOutput, setLastOutput] = useState("");

    useEffect(() => {
        // Poll for status or just load hotkeys
        apiClient.healthCheck()
            .then(() => {
                setStatus("Connected");
                loadHotkeys();
            })
            .catch(() => setStatus("Offline"));
    }, []);

    const loadHotkeys = async () => {
        try {
            const list = await apiClient.getHotkeys();
            setHotkeys(list);
        } catch (e) {
            console.error(e);
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
