import { useState, useEffect } from "react";
import { apiClient, ConnectionDefinition } from "../api/client";
import ConfirmDialog from "./ConfirmDialog";

interface SettingsProps {
    onBack: () => void;
    t: (key: string) => string;
}

type Capability = 'llm' | 'stt' | 'ocr';

interface ProviderInfo {
    id: string;
    name: string;
    capabilities: Capability[];
}

const PROVIDERS: ProviderInfo[] = [
    { id: "openai", name: "OpenAI Cloud", capabilities: ['llm', 'stt'] },
    { id: "azure", name: "Azure OpenAI", capabilities: ['llm', 'stt'] },
    { id: "anthropic", name: "Anthropic", capabilities: ['llm'] },
    { id: "google", name: "Google Gemini", capabilities: ['llm', 'stt'] },
    { id: "mistral", name: "Mistral AI", capabilities: ['llm', 'stt'] },
    { id: "groq", name: "Groq", capabilities: ['llm'] },
    { id: "openai_oss", name: "OpenAI OSS / Local", capabilities: ['llm'] },
    { id: "ollama", name: "Ollama (Local)", capabilities: ['llm'] },
    { id: "tesseract", name: "Tesseract OCR", capabilities: ['ocr'] },
    { id: "mock", name: "Mock / Test", capabilities: ['llm', 'stt', 'ocr'] }
];

const CURATED_MODELS: Record<string, Record<string, string[]>> = {
    llm: {
        openai: ["gpt-5.3", "gpt-5.3-mini", "gpt-5.2", "gpt-5.2-mini", "o5-mini"],
        azure: ["gpt-5.3", "gpt-5.3-mini", "gpt-5.2", "gpt-5.2-mini", "o5-mini"],
        anthropic: ["claude-4.1", "claude-4.1-oxford", "claude-4.1-mini"],
        google: ["gemini-3-pro", "gemini-3-flash", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        mistral: ["mistral-large-2", "mistral-large", "mistral-medium", "mistral-small", "mixtral-8x7b", "mixtral-8x22b"],
        groq: ["grok-4", "grok-4-heavy"],
        openai_oss: ["gpt-oss-120b", "gpt-oss-20b"],
        ollama: ["llama4", "phi3", "mixtral8x7b", "gemma3"],
        mock: ["mock-llm-model"]
    },
    stt: {
        openai: ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "gpt-4o-transcribe-diarize"],
        azure: ["gpt-4o-transcribe", "gpt-4o-mini-transcribe"],
        google: ["gemini-2.5-pro", "gemini-2.5-flash"],
        mistral: ["voxtral-mini-latest"],
        mock: ["mock-stt-model"]
    },
    ocr: {
        tesseract: ["tesseract-5.2", "tesseract-5.0"],
        mock: ["mock-ocr-model"]
    }
};

export default function Settings({ onBack, t }: SettingsProps) {
    const [connections, setConnections] = useState<ConnectionDefinition[]>([]);
    const [activeTab, setActiveTab] = useState<'connections' | 'general'>('connections');
    const [capability, setCapability] = useState<Capability>('llm');
    const [generalSettings, setGeneralSettings] = useState<any>(null);
    const [newConn, setNewConn] = useState<Partial<ConnectionDefinition>>({
        connection_id: "",
        provider_id: "openai",
        model_id: "gpt-5.3",
        capabilities: ["llm"]
    });
    const [isEditing, setIsEditing] = useState(false);
    const [secret, setSecret] = useState("");
    const [loading, setLoading] = useState(false);

    const [dialog, setDialog] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        onConfirm: () => void;
        confirmLabel?: string;
        isAlert?: boolean;
    }>({
        isOpen: false,
        title: "",
        message: "",
        onConfirm: () => { }
    });

    const showAlert = (title: string, message: string) => {
        setDialog({
            isOpen: true,
            title,
            message,
            isAlert: true,
            onConfirm: () => setDialog(prev => ({ ...prev, isOpen: false }))
        });
    };

    const showConfirm = (title: string, message: string, onConfirm: () => void, confirmLabel = "OK") => {
        setDialog({
            isOpen: true,
            title,
            message,
            isAlert: false,
            onConfirm: () => {
                onConfirm();
                setDialog(prev => ({ ...prev, isOpen: false }));
            },
            confirmLabel
        });
    };

    useEffect(() => {
        const init = async () => {
            const data = await apiClient.getConnections();
            const connList = data || [];
            setConnections(connList);
            updateAutoId('llm', 'openai', connList);

            try {
                const s = await apiClient.getSettings();
                setGeneralSettings(s);
            } catch (e) {
                console.error("Failed to load settings", e);
            }
        };
        init();
    }, []);

    const updateGeneralSetting = async (key: string, value: any) => {
        const updated = { ...generalSettings, [key]: value };
        setGeneralSettings(updated);
        await apiClient.updateSettings({ [key]: value });
    };

    const updateRoutingDefault = async (type: string, id: string) => {
        const currentRouting = generalSettings?.routing_defaults || {};
        const updatedRouting = { ...currentRouting, [type]: id };
        updateGeneralSetting('routing_defaults', updatedRouting);
    };

    const generateUniqueId = (cap: string, provider: string, existing: ConnectionDefinition[]) => {
        let base = `${provider}_${cap}`.toLowerCase();
        let counter = 1;
        let candidate = base;
        while (existing.some(c => c.connection_id === candidate)) {
            counter++;
            candidate = `${base}_${counter}`;
        }
        return candidate;
    };

    const updateAutoId = (cap: string, providerId: string, existing: ConnectionDefinition[]) => {
        const autoId = generateUniqueId(cap, providerId, existing);
        const models = CURATED_MODELS[cap]?.[providerId] || CURATED_MODELS['llm']?.[providerId] || [];
        setNewConn(prev => ({
            ...prev,
            connection_id: autoId,
            provider_id: providerId,
            model_id: models[0] || "custom",
            // Keep existing capabilities if we are editing, otherwise set trial cap
            capabilities: (isEditing && prev.capabilities?.length) ? prev.capabilities : [cap]
        }));
    };

    const handleCapabilityChange = (cap: Capability) => {
        setCapability(cap);
        const firstProvider = PROVIDERS.find(p => p.capabilities.includes(cap))?.id || "";
        updateAutoId(cap, firstProvider, connections);
    };

    const handleProviderChange = (providerId: string) => {
        updateAutoId(capability, providerId, connections);
    };

    const handleAddConnection = async () => {
        if (!newConn.connection_id) {
            showAlert("Action Required", "Connection ID is required");
            return;
        }
        if (!newConn.capabilities || newConn.capabilities.length === 0) {
            showAlert("Action Required", "At least one capability must be selected");
            return;
        }
        setLoading(true);
        try {
            if (isEditing) {
                await apiClient.updateConnection(newConn.connection_id!, newConn as ConnectionDefinition);
            } else {
                await apiClient.createConnection(newConn as ConnectionDefinition);
            }

            if (secret) {
                await apiClient.saveSecret(newConn.connection_id!, secret);
            }
            const updatedConns = await apiClient.getConnections();
            setConnections(updatedConns || []);
            setIsEditing(false);
            setSecret("");
            updateAutoId(capability, newConn.provider_id || "openai", updatedConns || []);
        } catch (e) {
            showAlert("Error", "Error saving connection.");
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (conn: ConnectionDefinition) => {
        setNewConn(conn);
        setIsEditing(true);
        setSecret(""); // Reset secret as we don't fetch it
        // Focus or scroll to form
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const toggleCapability = (cap: Capability) => {
        const caps = newConn.capabilities || [];
        if (caps.includes(cap)) {
            setNewConn({ ...newConn, capabilities: caps.filter(c => c !== cap) });
        } else {
            setNewConn({ ...newConn, capabilities: [...caps, cap] });
        }
    };

    const handleDelete = async (id: string) => {
        showConfirm("Bestätigung", `Möchten Sie " ${id} " wirklich löschen?`, async () => {
            await apiClient.deleteConnection(id);
            const data = await apiClient.getConnections();
            setConnections(data || []);
        }, "Löschen");
    };

    const availableProviders = (PROVIDERS || []).filter(p => p.capabilities?.includes(capability));

    if (!capability) return null;

    return (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "400px" }}>
            <header data-tauri-drag-region style={{ display: "flex", alignItems: "center", gap: "20px", marginBottom: "32px", cursor: "move" }}>
                <button className="secondary" onClick={onBack} style={{ padding: "8px 12px" }}>&larr; Back</button>
                <h1 data-tauri-drag-region style={{ margin: 0, fontSize: "1.8rem", flex: 1 }}>{t("label.settings")}</h1>
            </header>

            <div style={{ display: "flex", gap: "24px", marginBottom: "32px", borderBottom: "1px solid var(--glass-border)" }}>
                <button
                    className={activeTab === 'connections' ? "tab-active" : "secondary"}
                    onClick={() => setActiveTab('connections')}
                    style={{ background: "transparent", border: "none", borderBottom: activeTab === 'connections' ? "2px solid var(--accent-primary)" : "none", borderRadius: 0, paddingBottom: "12px", boxShadow: "none" }}
                >
                    Connections
                </button>
                <button
                    className={activeTab === 'general' ? "tab-active" : "secondary"}
                    onClick={() => setActiveTab('general')}
                    style={{ background: "transparent", border: "none", borderBottom: activeTab === 'general' ? "2px solid var(--accent-primary)" : "none", borderRadius: 0, paddingBottom: "12px", boxShadow: "none" }}
                >
                    General
                </button>
            </div>

            {activeTab === 'connections' ? (
                <>
                    <section style={{ marginBottom: "40px" }}>
                        <h2 style={{ fontSize: "1.2rem", marginBottom: "16px", color: "var(--accent-primary)" }}>Add New {capability === 'llm' ? 'Text (LLM)' : capability === 'stt' ? 'Speech (STT)' : 'Photo (OCR)'} Connection</h2>

                        <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                            {(['llm', 'stt', 'ocr'] as Capability[]).map(cap => (
                                <button
                                    key={cap}
                                    className={capability === cap ? "" : "secondary"}
                                    onClick={() => handleCapabilityChange(cap)}
                                    style={{ flex: 1, padding: "8px", fontSize: "0.85rem" }}
                                >
                                    {cap === 'llm' ? 'Text (LLM)' : cap === 'stt' ? 'Speech (STT)' : 'Photo (OCR)'}
                                </button>
                            ))}
                        </div>

                        <div style={{ display: "grid", gap: "16px", background: "rgba(0,0,0,0.02)", padding: "20px", borderRadius: "var(--radius-md)", border: "1px solid var(--glass-border)" }}>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>Provider</label>
                                    <select
                                        value={newConn.provider_id}
                                        onChange={e => handleProviderChange(e.target.value)}
                                    >
                                        {availableProviders.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px", fontWeight: 600 }}>Connection ID</label>
                                    <input
                                        placeholder="e.g. MyConnection"
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
                                        {(CURATED_MODELS[capability]?.[newConn.provider_id || ""] || []).map(m => (
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

                            {!['ollama', 'tesseract', 'openai_oss', 'mock'].includes(newConn.provider_id || "") && (
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

                            <div style={{ marginBottom: "8px" }}>
                                <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "8px", fontWeight: 600 }}>Enabled Capabilities</label>
                                <div style={{ display: "flex", gap: "16px" }}>
                                    {PROVIDERS.find(p => p.id === newConn.provider_id)?.capabilities.map(cap => (
                                        <label key={cap} style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer", fontSize: "0.9rem" }}>
                                            <input
                                                type="checkbox"
                                                checked={newConn.capabilities?.includes(cap)}
                                                onChange={() => toggleCapability(cap)}
                                                style={{ width: "18px", height: "18px" }}
                                            />
                                            {cap.toUpperCase()}
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <button onClick={handleAddConnection} disabled={loading} style={{ marginTop: "12px", background: isEditing ? "var(--accent-hover)" : "var(--accent-primary)" }}>
                                {loading ? "Saving..." : isEditing ? "Update Connection" : `Add Connection`}
                            </button>
                            {isEditing && (
                                <button className="secondary" onClick={() => { setIsEditing(false); updateAutoId(capability, "openai", connections); }} style={{ marginTop: "4px" }}>
                                    Cancel Edit
                                </button>
                            )}
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
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 700 }}>{c.connection_id}</div>
                                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                            {c.provider_id.toUpperCase()} &bull; {c.model_id} &bull; {(c.capabilities || []).join(", ").toUpperCase()}
                                        </div>
                                    </div>
                                    <div style={{ display: "flex", gap: "8px" }}>
                                        <button
                                            className="secondary"
                                            onClick={() => handleEdit(c)}
                                            style={{ padding: "6px 12px", fontSize: "0.8rem", boxShadow: "none" }}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(c.connection_id)}
                                            style={{ background: "transparent", color: "#f43f5e", border: "1px solid #f43f5e", boxShadow: "none", padding: "6px 12px", fontSize: "0.8rem" }}
                                        >
                                            Remove
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                </>
            ) : (
                <div style={{ display: "grid", gap: "32px" }}>
                    <section>
                        <h2 style={{ fontSize: "1.2rem", marginBottom: "16px" }}>Core Settings</h2>
                        <div style={{ background: "rgba(0,0,0,0.02)", padding: "24px", borderRadius: "12px", border: "1px solid var(--glass-border)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>Session History</div>
                                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Track recent hotkey outputs locally.</div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={generalSettings?.history?.enabled}
                                    onChange={e => updateGeneralSetting('history', { ...generalSettings.history, enabled: e.target.checked })}
                                    style={{ width: "24px", height: "24px" }}
                                />
                            </div>
                            <hr style={{ opacity: 0.1, margin: "16px 0" }} />
                            <div style={{ marginBottom: "20px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>UI Transparency</div>
                                        <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Adjust panel transparency.</div>
                                    </div>
                                    <div style={{ fontWeight: 700, color: "var(--accent-primary)" }}>{Math.round((1 - (generalSettings?.app?.ui_opacity ?? 0.95)) * 100)}%</div>
                                </div>
                                <input
                                    type="range"
                                    min="0.0"
                                    max="0.6"
                                    step="0.01"
                                    value={1 - (generalSettings?.app?.ui_opacity ?? 0.95)}
                                    onChange={e => updateGeneralSetting('app', { ...generalSettings.app, ui_opacity: 1 - parseFloat(e.target.value) })}
                                    style={{ width: "100%", height: "6px", appearance: "none", background: "var(--glass-border)", borderRadius: "3px", outline: "none" }}
                                />
                            </div>
                            <hr style={{ opacity: 0.1, margin: "16px 0" }} />
                            <div style={{ fontWeight: 600, marginBottom: "12px" }}>Default Routing</div>
                            <div style={{ display: "grid", gap: "12px" }}>
                                <div>
                                    <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px" }}>Default Text Processing (AI)</label>
                                    <select
                                        value={generalSettings?.routing_defaults?.default_llm_connection_id}
                                        onChange={e => updateRoutingDefault('default_llm_connection_id', e.target.value)}
                                    >
                                        <option value="">-- Let Paste & Speech AI Decide --</option>
                                        {connections.filter(c => c.capabilities?.includes('llm')).map(c => (
                                            <option key={c.connection_id} value={c.connection_id}>{c.connection_id}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: "block", fontSize: "0.8rem", marginBottom: "4px" }}>Default Speech Processing (STT)</label>
                                    <select
                                        value={generalSettings?.routing_defaults?.default_stt_connection_id}
                                        onChange={e => updateRoutingDefault('default_stt_connection_id', e.target.value)}
                                    >
                                        <option value="">-- Use System Default --</option>
                                        {connections.filter(c => c.capabilities?.includes('stt')).map(c => (
                                            <option key={c.connection_id} value={c.connection_id}>{c.connection_id}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            )}

            <ConfirmDialog
                {...dialog}
                onReset={() => setDialog(prev => ({ ...prev, isOpen: false }))}
            />
        </div>
    );
}
