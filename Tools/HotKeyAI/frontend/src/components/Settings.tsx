import { useState, useEffect } from "react";
import { apiClient, ConnectionDefinition } from "../api/client";

interface SettingsProps {
    onBack: () => void;
    t: (key: string) => string;
}

export default function Settings({ onBack, t }: SettingsProps) {
    const [connections, setConnections] = useState<ConnectionDefinition[]>([]);
    const [newConn, setNewConn] = useState<Partial<ConnectionDefinition>>({
        connection_id: "",
        provider_id: "openai",
        model_id: "gpt-4o-mini"
    });
    const [secret, setSecret] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadConnections();
    }, []);

    const loadConnections = async () => {
        try {
            const data = await apiClient.getConnections();
            setConnections(data || []);
        } catch (e) {
            console.error("Failed to load connections", e);
        }
    };

    const handleAddConnection = async () => {
        if (!newConn.connection_id || !secret) {
            alert("ID and API Key are required");
            return;
        }
        setLoading(true);
        try {
            await apiClient.createConnection(newConn as ConnectionDefinition);
            await apiClient.saveSecret(newConn.connection_id, secret);
            setNewConn({ connection_id: "", provider_id: "openai", model_id: "gpt-4o-mini" });
            setSecret("");
            await loadConnections();
        } catch (e) {
            alert("Error saving connection");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm("Delete this connection?")) {
            await apiClient.deleteConnection(id);
            await loadConnections();
        }
    };

    return (
        <div className="settings-panel">
            <header style={{ display: "flex", alignItems: "center", gap: "20px", marginBottom: "20px" }}>
                <button onClick={onBack}>&larr; Back</button>
                <h2>{t("label.settings") || "App Settings"}</h2>
            </header>

            <section style={{ background: "#f9f9f9", padding: "15px", borderRadius: "8px", marginBottom: "24px" }}>
                <h3>AI Connections</h3>
                <div className="connection-form" style={{ display: "grid", gap: "10px", marginBottom: "20px" }}>
                    <input
                        placeholder="Connection ID (e.g. MyOpenAI)"
                        value={newConn.connection_id}
                        onChange={e => setNewConn({ ...newConn, connection_id: e.target.value })}
                    />
                    <select
                        value={newConn.provider_id}
                        onChange={e => setNewConn({ ...newConn, provider_id: e.target.value })}
                    >
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="google">Google</option>
                        <option value="mock">Mock / Test</option>
                    </select>
                    <input
                        placeholder="Model ID"
                        value={newConn.model_id}
                        onChange={e => setNewConn({ ...newConn, model_id: e.target.value })}
                    />
                    <input
                        type="password"
                        placeholder="API Key"
                        value={secret}
                        onChange={e => setSecret(e.target.value)}
                    />
                    <button onClick={handleAddConnection} disabled={loading}>
                        {loading ? "Saving..." : "Add Connection"}
                    </button>
                </div>

                <div className="connection-list">
                    <h4>Saved Connections</h4>
                    {connections.length === 0 && <p style={{ color: "#888" }}>No connections configured yet.</p>}
                    {connections.map(c => (
                        <div key={c.connection_id} style={{ display: "flex", justifyContent: "space-between", padding: "8px", borderBottom: "1px solid #eee" }}>
                            <div>
                                <strong>{c.connection_id}</strong> ({c.provider_id} - {c.model_id})
                            </div>
                            <button onClick={() => handleDelete(c.connection_id)} style={{ padding: "2px 8px", background: "#fee", color: "#c00", border: "1px solid #c00" }}>
                                Delete
                            </button>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}
