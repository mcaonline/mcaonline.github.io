
import { useState } from "react";
import { useApp } from "../store/context";
import { apiClient, ConnectionDefinition } from "../api/client";

interface SettingsProps {
    onBack: () => void;
}

type Tab = 'general' | 'hotkeys' | 'connections' | 'history';

export default function Settings({ onBack }: SettingsProps) {
    const { state, refreshData } = useApp();
    const [activeTab, setActiveTab] = useState<Tab>('general');
    const [loading, setLoading] = useState(false);

    // Connection Form State
    const [connForm, setConnForm] = useState<Partial<ConnectionDefinition>>({ capabilities: ['llm'] });
    const [secret, setSecret] = useState("");
    const [isEditingConn, setIsEditingConn] = useState(false);

    const t = (key: string) => state.uiText[key] || key;

    const handleSaveConnection = async () => {
        if (!connForm.connection_id || !connForm.provider_id) {
            alert("Connection ID and Provider are required");
            return;
        }
        setLoading(true);
        try {
            const payload = { ...connForm } as ConnectionDefinition;
            if (isEditingConn) {
                await apiClient.updateConnection(connForm.connection_id, payload);
            } else {
                await apiClient.createConnection(payload);
            }
            if (secret) {
                await apiClient.saveSecret(connForm.connection_id, secret);
            }
            await refreshData();
            setConnForm({ capabilities: ['llm'] });
            setSecret("");
            setIsEditingConn(false);
            setActiveTab('connections');
        } catch (e) {
            console.error("Failed to save connection", e);
            alert("Failed to save connection");
        } finally {
            setLoading(false);
        }
    };


    const handleEditConnection = (conn: ConnectionDefinition) => {
        setConnForm(conn);
        setIsEditingConn(true);
        setSecret("");
    };

    const handleDeleteConnection = async (id: string) => {
        if (!confirm(`Delete connection ${id}?`)) return;
        await apiClient.deleteConnection(id);
        await refreshData();
    };

    const handleToggleHotkey = async (id: string, enabled: boolean) => {
        // Optimistic update
        // const updatedHotkeys = state.hotkeys.map(h => h.id === id ? { ...h, enabled } : h);
        console.log(`[Mock] Toggling hotkey ${id} to ${enabled}`);
        await refreshData();
    };

    return (
        <div style={{ padding: "20px", height: "100%", display: "flex", flexDirection: "column" }}>
            <header data-tauri-drag-region style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "20px", cursor: "move" }}>
                <button className="secondary" onClick={onBack}>&larr; Back</button>
                <h1 data-tauri-drag-region style={{ margin: 0, fontSize: "1.5rem" }}>Settings</h1>
            </header>

            <div className="tabs" style={{ display: "flex", gap: "12px", borderBottom: "1px solid var(--glass-border)", marginBottom: "20px" }}>
                {(['general', 'hotkeys', 'connections', 'history'] as Tab[]).map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        style={{
                            background: "transparent",
                            borderBottom: activeTab === tab ? "2px solid var(--accent-primary)" : "none",
                            borderRadius: 0,
                            paddingBottom: "8px",
                            fontWeight: activeTab === tab ? 600 : 400
                        }}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            <div className="content" style={{ flex: 1, overflowY: "auto" }}>
                {activeTab === 'general' && (
                    <div style={{ display: "grid", gap: "20px" }}>
                        <section>
                            <h3>Global Shortcuts</h3>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px", background: "rgba(0,0,0,0.02)", borderRadius: "8px" }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>Main Trigger</div>
                                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>The chord to open the panel</div>
                                </div>
                                <div style={{ fontWeight: 700, background: "var(--surface-2)", padding: "4px 8px", borderRadius: "4px" }}>Ctrl + V, V</div>
                            </div>
                        </section>
                        <section>
                            <h3>Routing Defaults</h3>
                            <div style={{ display: "grid", gap: "12px" }}>
                                <label>
                                    <span style={{ display: "block", fontSize: "0.9rem", marginBottom: "4px" }}>Default Text AI</span>
                                    <select
                                        value={state.activeDefaults.llm || ""}
                                        onChange={(e) => apiClient.updateSettings({ routing_defaults: { ...state.settings?.routing_defaults, default_llm_connection_id: e.target.value } }).then(refreshData)}
                                        style={{ width: "100%", padding: "8px" }}
                                    >
                                        <option value="">Select a connection...</option>
                                        {state.connections.filter(c => c.capabilities.includes('llm')).map(c => (
                                            <option key={c.connection_id} value={c.connection_id}>{c.connection_id} ({c.model_id})</option>
                                        ))}
                                    </select>
                                </label>
                            </div>
                        </section>
                    </div>
                )}

                <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <h3>Hotkeys</h3>
                        <button onClick={() => {
                            // Template for new hotkey
                            const newHk = {
                                id: crypto.randomUUID(),
                                kind: 'user',
                                mode: 'ai_transform',
                                display_key: 'New Hotkey',
                                description_key: 'Custom AI Command',
                                enabled: true,
                                prompt_template: "Summarize this text",
                                capability_requirements: [{ capability: 'llm', min_sequence: 1 }]
                            };
                            // For MVP, we just create it immediately and let user edit (editing not fully implemented yet, but creation is step 1)
                            // Ideally we'd show a modal.
                            apiClient.createHotkey(newHk as any).then(refreshData);
                        }}>Add New</button>
                    </div>
                    {state.hotkeys.map(hk => (
                        <div key={hk.id} style={{ padding: "12px", borderBottom: "1px solid var(--glass-border)", background: "rgba(0,0,0,0.02)" }}>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{t(hk.display_key)}</div>
                                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{t(hk.description_key)}</div>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                    <input
                                        type="checkbox"
                                        checked={hk.enabled}
                                        onChange={(e) => handleToggleHotkey(hk.id, e.target.checked)}
                                    />
                                    {hk.kind === 'user' && (
                                        <button onClick={async () => {
                                            if (confirm("Delete this hotkey?")) {
                                                await apiClient.deleteHotkey(hk.id);
                                                refreshData();
                                            }
                                        }} style={{ padding: "4px 8px", background: "transparent", color: "#f43f5e", border: "1px solid #f43f5e", fontSize: "0.7rem", borderRadius: "4px" }}>
                                            Del
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Configuration Fields */}
                            <div style={{ display: "grid", gap: "8px", paddingLeft: "12px", borderLeft: "2px solid var(--glass-border)" }}>
                                {/* Global Hotkey Trigger */}
                                <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "8px" }}>
                                    <span style={{ minWidth: "60px", color: "var(--text-secondary)" }}>Trigger:</span>
                                    <input
                                        placeholder="e.g. <ctrl>+<alt>+k"
                                        defaultValue={hk.direct_hotkey || ""}
                                        onBlur={(e) => {
                                            const val = e.target.value.trim();
                                            if (val !== (hk.direct_hotkey || "")) {
                                                apiClient.updateHotkey(hk.id, { ...hk, direct_hotkey: val || undefined }).then(refreshData);
                                            }
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter') e.currentTarget.blur();
                                        }}
                                        style={{ padding: "4px 8px", borderRadius: "4px", border: "1px solid var(--glass-border)", background: "rgba(255,255,255,0.05)", width: "100%", color: "var(--text-primary)" }}
                                    />
                                </label>

                                {/* Prompt Template for Custom Hotkeys */}
                                {hk.kind === 'user' && (
                                    <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "8px" }}>
                                        <span style={{ minWidth: "60px", color: "var(--text-secondary)" }}>Prompt:</span>
                                        <input
                                            defaultValue={hk.prompt_template || ""}
                                            onBlur={(e) => {
                                                const val = e.target.value;
                                                if (val !== hk.prompt_template) {
                                                    apiClient.updateHotkey(hk.id, { ...hk, prompt_template: val }).then(refreshData);
                                                }
                                            }}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') e.currentTarget.blur();
                                            }}
                                            style={{ padding: "4px 8px", borderRadius: "4px", border: "1px solid var(--glass-border)", background: "rgba(255,255,255,0.05)", width: "100%", color: "var(--text-primary)" }}
                                        />
                                    </label>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {activeTab === 'connections' && (
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3>Active Connections</h3>
                            <button onClick={() => { setConnForm({ capabilities: ['llm'] }); setIsEditingConn(false); setActiveTab('connections'); /* scroll to form */ }}>Add New</button>
                        </div>
                        <div style={{ display: "grid", gap: "12px", marginBottom: "32px" }}>
                            {state.connections.length === 0 && <div style={{ opacity: 0.5, fontStyle: "italic" }}>No connections found.</div>}
                            {state.connections.map(c => (
                                <div key={c.connection_id} style={{ padding: "12px", background: "rgba(0,0,0,0.02)", borderRadius: "8px", border: "1px solid var(--glass-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{c.connection_id}</div>
                                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.provider_id} • {c.model_id}</div>
                                    </div>
                                    <div style={{ display: "flex", gap: "8px" }}>
                                        <button onClick={() => handleEditConnection(c)} className="secondary" style={{ padding: "4px 8px", fontSize: "0.8rem" }}>Edit</button>
                                        <button onClick={() => handleDeleteConnection(c.connection_id)} style={{ color: "#f43f5e", padding: "4px 8px", fontSize: "0.8rem", border: "1px solid #f43f5e", background: "transparent" }}>Delete</button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <h3>{isEditingConn ? "Edit" : "Add"} Connection</h3>
                        <div style={{ display: "grid", gap: "12px", padding: "20px", background: "rgba(0,0,0,0.02)", borderRadius: "8px" }}>
                            <input
                                placeholder="Connection ID (e.g. my-gpt)"
                                value={connForm.connection_id || ""}
                                onChange={e => setConnForm({ ...connForm, connection_id: e.target.value })}
                                disabled={isEditingConn}
                            />
                            <select
                                value={connForm.provider_id || ""}
                                onChange={e => setConnForm({ ...connForm, provider_id: e.target.value })}
                            >
                                <option value="">Select Provider</option>
                                <option value="openai">OpenAI</option>
                                <option value="anthropic">Anthropic</option>
                                <option value="google">Google</option>
                                <option value="mistral">Mistral</option>
                            </select>
                            <input
                                placeholder="Model ID"
                                value={connForm.model_id || ""}
                                onChange={e => setConnForm({ ...connForm, model_id: e.target.value })}
                            />
                            <input
                                type="password"
                                placeholder="API Key"
                                value={secret}
                                onChange={e => setSecret(e.target.value)}
                            />
                            <button onClick={handleSaveConnection} disabled={loading} style={{ background: "var(--accent-primary)", color: "white", padding: "8px 16px", borderRadius: "4px", border: "none" }}>{loading ? "Saving..." : isEditingConn ? "Update Connection" : "Save Connection"}</button>
                            {isEditingConn && <button onClick={() => { setIsEditingConn(false); setConnForm({ capabilities: ['llm'] }); setSecret(""); }} className="secondary">Cancel Edit</button>}
                        </div>
                    </div>
                )}

                {activeTab === 'history' && (
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3>Session History</h3>
                            <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={state.settings?.history?.enabled || false}
                                    onChange={(e) => apiClient.updateSettings({ history: { enabled: e.target.checked } }).then(refreshData)}
                                />
                                Enable History
                            </label>
                        </div>
                        {state.history.length === 0 ? (
                            <div style={{ textAlign: "center", padding: "20px", opacity: 0.5 }}>No history</div>
                        ) : (
                            state.history.map((h, i) => (
                                <div key={i} style={{ padding: "12px", borderBottom: "1px solid var(--glass-border)" }}>
                                    <div style={{ fontWeight: 600 }}>{h.hotkey_id}</div>
                                    <div style={{ fontSize: "0.8rem", opacity: 0.7 }}>{h.timestamp}</div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
