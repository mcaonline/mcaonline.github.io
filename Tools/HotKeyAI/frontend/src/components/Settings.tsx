
import { useState } from "react";
import { useApp } from "../store/context";
import { apiClient, ConnectionDefinition } from "../api/client";

interface SettingsProps {
    onBack: () => void;
}

type Tab = 'general' | 'actions' | 'connections' | 'history';

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

    const handleToggleAction = async (id: string, enabled: boolean) => {
        console.log(`[Mock] Toggling action ${id} to ${enabled}`);
        await refreshData();
    };

    return (
        <div style={{ padding: "20px", height: "100%", display: "flex", flexDirection: "column" }}>
            <header data-tauri-drag-region style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "20px", cursor: "move" }}>
                <button className="secondary" onClick={onBack}>{t("label.back")}</button>
                <h1 data-tauri-drag-region style={{ margin: 0, fontSize: "1.5rem" }}>{t("label.settings")}</h1>
            </header>

            <div className="tabs" style={{ display: "flex", gap: "12px", borderBottom: "1px solid var(--glass-border)", marginBottom: "20px" }}>
                {(['general', 'actions', 'connections', 'history'] as Tab[]).map(tab => (
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
                        {t("label." + tab)}
                    </button>
                ))}
            </div>

            <div className="content" style={{ flex: 1, overflowY: "auto" }}>
                {activeTab === 'general' && (
                    <div style={{ display: "grid", gap: "20px" }}>
                        <section>
                            <h3>{t("label.appearance")}</h3>
                            <div style={{ display: "grid", gap: "12px", background: "rgba(0,0,0,0.02)", padding: "12px", borderRadius: "8px" }}>
                                <label>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                                        <span style={{ fontSize: "0.9rem" }}>{t("label.window_opacity")}</span>
                                        <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>{Math.round((state.settings?.app?.ui_opacity ?? 0.95) * 100)}%</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0.1"
                                        max="1.0"
                                        step="0.05"
                                        value={state.settings?.app?.ui_opacity ?? 0.95}
                                        onChange={(e) => {
                                            const val = parseFloat(e.target.value);
                                            const currentApp = state.settings?.app || { theme: 'system', language: 'en', ui_opacity: 0.95, ui_decorations: false };
                                            apiClient.updateSettings({ app: { ...currentApp, ui_opacity: val } }).then(refreshData);
                                        }}
                                        style={{ width: "100%" }}
                                    />
                                </label>
                                <label style={{ display: "flex", alignItems: "center", gap: "12px", cursor: "pointer" }}>
                                    <input
                                        type="checkbox"
                                        checked={state.settings?.app?.ui_decorations ?? false}
                                        onChange={(e) => {
                                            const currentApp = state.settings?.app || { theme: 'system', language: 'en', ui_opacity: 0.95, ui_decorations: false };
                                            apiClient.updateSettings({ app: { ...currentApp, ui_decorations: e.target.checked } }).then(refreshData);
                                        }}
                                    />
                                    <span style={{ fontSize: "0.9rem" }}>{t("label.window_decorations")}</span>
                                </label>
                            </div>
                        </section>
                        <section>
                            <h3>{t("label.global_shortcuts")}</h3>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px", background: "rgba(0,0,0,0.02)", borderRadius: "8px" }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>{t("label.main_trigger")}</div>
                                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{t("label.main_trigger_desc")}</div>
                                </div>
                                <div style={{ fontWeight: 700, background: "var(--surface-2)", padding: "4px 8px", borderRadius: "4px" }}>{state.settings?.actions?.main_trigger?.chord ?? "Ctrl+V,V"}</div>
                            </div>
                        </section>
                        <section>
                            <h3>{t("label.routing_defaults")}</h3>
                            <div style={{ display: "grid", gap: "12px" }}>
                                <label>
                                    <span style={{ display: "block", fontSize: "0.9rem", marginBottom: "4px" }}>{t("label.default_text_ai")}</span>
                                    <select
                                        value={state.activeDefaults.llm || ""}
                                        onChange={(e) => apiClient.updateSettings({ routing_defaults: { ...state.settings?.routing_defaults, default_llm_connection_id: e.target.value } }).then(refreshData)}
                                        style={{ width: "100%", padding: "8px" }}
                                    >
                                        <option value="">{t("label.select_connection")}</option>
                                        {state.connections.filter(c => c.capabilities.includes('llm')).map(c => (
                                            <option key={c.connection_id} value={c.connection_id}>{c.connection_id} ({c.model_id})</option>
                                        ))}
                                    </select>
                                </label>
                            </div>
                        </section>
                    </div>
                )}

                {activeTab === 'actions' && (
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3>{t("label.actions")}</h3>
                            <button onClick={() => {
                                // Template for new action
                                const newAction = {
                                    id: crypto.randomUUID(),
                                    kind: 'user',
                                    mode: 'ai_transform',
                                    display_key: 'label.new_action',
                                    description_key: 'label.custom_ai_command',
                                    enabled: true,
                                    prompt_template: "Summarize this text",
                                    capability_requirements: [{ capability: 'llm', min_sequence: 1 }]
                                };
                                apiClient.createAction(newAction as any).then(refreshData);
                            }}>{t("label.add_new")}</button>
                        </div>
                        {state.actions.map(a => (
                            <div key={a.id} style={{ padding: "12px", borderBottom: "1px solid var(--glass-border)", background: "rgba(0,0,0,0.02)" }}>
                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{t(a.display_key)}</div>
                                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{t(a.description_key)}</div>
                                    </div>
                                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                        <input
                                            type="checkbox"
                                            checked={a.enabled}
                                            onChange={(e) => handleToggleAction(a.id!, e.target.checked)}
                                        />
                                        {a.kind === 'user' && (
                                            <button onClick={async () => {
                                                if (confirm("Delete this action?")) {
                                                    await apiClient.deleteAction(a.id!);
                                                    refreshData();
                                                }
                                            }} style={{ padding: "4px 8px", background: "transparent", color: "#f43f5e", border: "1px solid #f43f5e", fontSize: "0.7rem", borderRadius: "4px" }}>
                                                {t("label.del")}
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* Configuration Fields */}
                                <div style={{ display: "grid", gap: "8px", paddingLeft: "12px", borderLeft: "2px solid var(--glass-border)" }}>
                                    {/* Global Hotkey Trigger */}
                                    <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "8px" }}>
                                        <span style={{ minWidth: "60px", color: "var(--text-secondary)" }}>{t("label.trigger")}:</span>
                                        <input
                                            placeholder={t("placeholder.action_trigger")}
                                            defaultValue={a.direct_hotkey || ""}
                                            onBlur={(e) => {
                                                const val = e.target.value.trim();
                                                if (val !== (a.direct_hotkey || "")) {
                                                    apiClient.updateAction(a.id!, { ...a, direct_hotkey: val || undefined }).then(refreshData);
                                                }
                                            }}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') e.currentTarget.blur();
                                            }}
                                            style={{ padding: "4px 8px", borderRadius: "4px", border: "1px solid var(--glass-border)", background: "rgba(255,255,255,0.05)", width: "100%", color: "var(--text-primary)" }}
                                        />
                                    </label>

                                    {/* Prompt Template for Custom Actions */}
                                    {a.kind === 'user' && (
                                        <label style={{ fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "8px" }}>
                                            <span style={{ minWidth: "60px", color: "var(--text-secondary)" }}>{t("label.prompt")}:</span>
                                            <input
                                                defaultValue={a.prompt_template || ""}
                                                onBlur={(e) => {
                                                    const val = e.target.value;
                                                    if (val !== a.prompt_template) {
                                                        apiClient.updateAction(a.id!, { ...a, prompt_template: val }).then(refreshData);
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
                )}

                {activeTab === 'connections' && (
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3>{t("label.active_connections")}</h3>
                            <button onClick={() => { setConnForm({ capabilities: ['llm'] }); setIsEditingConn(false); setActiveTab('connections'); /* scroll to form */ }}>{t("label.add_new")}</button>
                        </div>
                        <div style={{ display: "grid", gap: "12px", marginBottom: "32px" }}>
                            {state.connections.length === 0 && <div style={{ opacity: 0.5, fontStyle: "italic" }}>{t("label.no_connections")}</div>}
                            {state.connections.map(c => (
                                <div key={c.connection_id} style={{ padding: "12px", background: "rgba(0,0,0,0.02)", borderRadius: "8px", border: "1px solid var(--glass-border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{c.connection_id}</div>
                                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.provider_id} • {c.model_id}</div>
                                    </div>
                                    <div style={{ display: "flex", gap: "8px" }}>
                                        <button onClick={() => handleEditConnection(c)} className="secondary" style={{ padding: "4px 8px", fontSize: "0.8rem" }}>{t("label.edit")}</button>
                                        <button onClick={() => handleDeleteConnection(c.connection_id!)} style={{ color: "#f43f5e", padding: "4px 8px", fontSize: "0.8rem", border: "1px solid #f43f5e", background: "transparent" }}>{t("label.delete")}</button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <h3>{isEditingConn ? t("label.edit") : t("label.add_new")} {t("label.add_edit_connection")}</h3>
                        <div style={{ display: "grid", gap: "12px", padding: "20px", background: "rgba(0,0,0,0.02)", borderRadius: "8px" }}>
                            <input
                                placeholder={t("placeholder.connection_id")}
                                value={connForm.connection_id || ""}
                                onChange={e => setConnForm({ ...connForm, connection_id: e.target.value })}
                                disabled={isEditingConn}
                            />
                            <select
                                value={connForm.provider_id || ""}
                                onChange={e => setConnForm({ ...connForm, provider_id: e.target.value })}
                            >
                                <option value="">{t("label.select_provider")}</option>
                                {state.providers.filter(p => p.provider_id !== 'mock').map(p => (
                                    <option key={p.provider_id} value={p.provider_id}>{p.display_name}</option>
                                ))}
                            </select>
                            <input
                                placeholder={t("placeholder.model_id")}
                                value={connForm.model_id || ""}
                                onChange={e => setConnForm({ ...connForm, model_id: e.target.value })}
                            />
                            <input
                                type="password"
                                placeholder={t("placeholder.api_key")}
                                value={secret}
                                onChange={e => setSecret(e.target.value)}
                            />
                            <button onClick={handleSaveConnection} disabled={loading} style={{ background: "var(--accent-primary)", color: "white", padding: "8px 16px", borderRadius: "4px", border: "none" }}>{loading ? t("label.saving") : isEditingConn ? t("label.update_connection") : t("label.save_connection")}</button>
                            {isEditingConn && <button onClick={() => { setIsEditingConn(false); setConnForm({ capabilities: ['llm'] }); setSecret(""); }} className="secondary">{t("label.cancel_edit")}</button>}
                        </div>
                    </div>
                )}

                {activeTab === 'history' && (
                    <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                            <h3>{t("label.session_history")}</h3>
                            <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={state.settings?.history?.enabled || false}
                                    onChange={(e) => apiClient.updateSettings({ history: { enabled: e.target.checked, max_entries: state.settings?.history?.max_entries ?? 10 } }).then(refreshData)}
                                />
                                {t("label.enable_history")}
                            </label>
                        </div>
                        {state.history.length === 0 ? (
                            <div style={{ textAlign: "center", padding: "20px", opacity: 0.5 }}>{t("label.no_history")}</div>
                        ) : (
                            state.history.map((h, i) => (
                                <div key={i} style={{ padding: "12px", borderBottom: "1px solid var(--glass-border)" }}>
                                    <div style={{ fontWeight: 600 }}>{h.action_id}</div>
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
