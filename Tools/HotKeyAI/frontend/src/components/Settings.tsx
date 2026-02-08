import { useState, useEffect } from "react";
import { apiClient, ConnectionDefinition } from "../api/client";

interface SettingsProps {
    onBack: () => void;
    t: (key: string) => string;
}

const CURATED_MODELS: Record<string, string[]> = {
    openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-preview", "o1-mini"],
    azure: ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-35-turbo"],
    anthropic: ["claude-3-5-sonnet-latest", "claude-3-opus-latest", "claude-3-haiku-20240307"],
    google: ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
    mistral: ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
    groq: ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma-7b-it"],
    ollama: ["llama3", "phi3", "mistral", "gemma"],
    mock: ["mock-model"]
};

const PROVIDERS = [
    { id: "openai", name: "OpenAI" },
    { id: "azure", name: "Azure OpenAI" },
    { id: "anthropic", name: "Anthropic" },
    { id: "google", name: "Google Gemini" },
    { id: "mistral", name: "Mistral AI" },
    { id: "groq", name: "Groq" },
    { id: "ollama", name: "Ollama (Local)" },
    { id: "mock", name: "Mock / Test" }
];

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
        const init = async () => {
            const data = await apiClient.getConnections();
            const connList = data || [];
            setConnections(connList);
            // Auto-fill ID for the default provider on first load
            const autoId = generateUniqueId("openai", connList);
            setNewConn(prev => ({ ...prev, connection_id: autoId }));
        };
        init();
    }, []);

    const loadConnections = async () => {
        try {
            const data = await apiClient.getConnections();
            setConnections(data || []);
        } catch (e) {
            console.error("Failed to load connections", e);
        }
    };

    const generateUniqueId = (provider: string, existing: ConnectionDefinition[]) => {
        let base = provider.toLowerCase();
        let counter = 1;
        let candidate = base;
        while (existing.some(c => c.connection_id === candidate)) {
            counter++;
            candidate = `${base}_${counter}`;
        }
        return candidate;
    };

    const handleProviderChange = (providerId: string) => {
        const defaultModel = CURATED_MODELS[providerId]?.[0] || "";
        const autoId = generateUniqueId(providerId, connections);
        setNewConn({
            ...newConn,
            provider_id: providerId,
            model_id: defaultModel,
            connection_id: autoId
        });
    };

    const handleAddConnection = async () => {
        if (!newConn.connection_id || (!secret && newConn.provider_id !== 'ollama')) {
            alert("Connection ID and API Key are required (except for local providers)");
            return;
        }
        setLoading(true);
        try {
            await apiClient.createConnection(newConn as ConnectionDefinition);
            if (secret) {
                await apiClient.saveSecret(newConn.connection_id!, secret);
            }
            // Reset but keep it ready for next with new auto ID
            const updatedConns = await apiClient.getConnections();
            setConnections(updatedConns || []);
            const nextId = generateUniqueId(newConn.provider_id || "openai", updatedConns || []);
            setNewConn({
                connection_id: nextId,
                provider_id: newConn.provider_id,
                model_id: CURATED_MODELS[newConn.provider_id || "openai"]?.[0] || ""
            });
            setSecret("");
        } catch (e) {
            alert("Error saving connection. Check backend logs.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm(`Are you sure you want to delete "${id}"?`)) {
            await apiClient.deleteConnection(id);
            await loadConnections();
        }
    };

    return (
        <div className="container">
            <div className="glass-pane">
                <header style={{ display: "flex", alignItems: "center", gap: "20px", marginBottom: "32px" }}>
                    <button className="secondary" onClick={onBack} style={{ padding: "8px 12px" }}>&larr; Back</button>
                    <h1 style={{ margin: 0, fontSize: "1.8rem" }}>{t("label.settings")}</h1>
                </header>

                <section style={{ marginBottom: "40px" }}>
                    <h2 style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--accent-primary)" }}>Add New Connection</h2>
                    <div style={{ display: "grid", gap: "16px", background: "rgba(0,0,0,0.02)", padding: "20px", borderRadius: "var(--radius-md)", border: "1px solid var(--glass-border)" }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                            <div>
                                <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>Provider</label>
                                <select
                                    value={newConn.provider_id}
                                    onChange={e => handleProviderChange(e.target.value)}
                                >
                                    {PROVIDERS.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                </select>
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>Connection ID (Auto-filled)</label>
                                <input
                                    placeholder="e.g. MyOpenAI"
                                    value={newConn.connection_id}
                                    onChange={e => setNewConn({ ...newConn, connection_id: e.target.value })}
                                />
                            </div>
                        </div>

                        <div>
                            <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>Model ID</label>
                            <div style={{ display: "flex", gap: "8px" }}>
                                <select
                                    style={{ flex: 1 }}
                                    value={newConn.model_id}
                                    onChange={e => setNewConn({ ...newConn, model_id: e.target.value })}
                                >
                                    {CURATED_MODELS[newConn.provider_id || "openai"]?.map(m => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                    <option value="custom">-- Custom Model ID --</option>
                                </select>
                                {newConn.model_id === "custom" && (
                                    <input
                                        style={{ flex: 1 }}
                                        placeholder="Enter custom model id"
                                        onChange={e => setNewConn({ ...newConn, model_id: e.target.value })}
                                    />
                                )}
                            </div>
                        </div>

                        {newConn.provider_id !== 'ollama' && (
                            <div>
                                <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>API Key</label>
                                <input
                                    type="password"
                                    placeholder="sk-..."
                                    value={secret}
                                    onChange={e => setSecret(e.target.value)}
                                />
                            </div>
                        )}

                        <button onClick={handleAddConnection} disabled={loading} style={{ marginTop: "8px" }}>
                            {loading ? "Saving..." : "Add Connection"}
                        </button>
                    </div>
                </section>

                <section>
                    <h2 style={{ fontSize: "1.2rem", marginBottom: "16px" }}>Managed Connections</h2>
                    <div className="connection-list">
                        {connections.length === 0 && (
                            <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)", background: "rgba(0,0,0,0.01)", borderRadius: "var(--radius-md)", border: "1px dashed var(--glass-border)" }}>
                                No active connections. Add one above to enable AI features.
                            </div>
                        )}
                        {connections.map(c => (
                            <div key={c.connection_id} className="hotkey-card" style={{ padding: "16px 20px" }}>
                                <div>
                                    <div style={{ fontWeight: 700 }}>{c.connection_id}</div>
                                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                        {c.provider_id.toUpperCase()} &bull; {c.model_id}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(c.connection_id)}
                                    style={{ background: "transparent", color: "#f43f5e", border: "1px solid #f43f5e", boxShadow: "none", padding: "6px 12px", fontSize: "0.8rem" }}
                                >
                                    Remove
                                </button>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}
