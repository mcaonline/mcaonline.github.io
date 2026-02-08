
const API_BASE = "http://localhost:8000"; // Adjust port if needed

export type ConnectionDefinition = {
    connection_id: string;
    provider_id: string;
    model_id: string;
    capabilities: ('llm' | 'stt' | 'ocr')[];
    secret_ref?: string;
    endpoint?: string;
};

export type HotkeyDefinition = {
    id: string;
    kind: 'builtin' | 'custom' | 'user';
    mode: 'ai_transform' | 'local_transform' | 'static_text_paste' | 'prompt_prefill_only';
    display_key: string;
    description_key: string;
    enabled: boolean;
    sequence: number;
    capability_requirements?: { capability: 'llm' | 'stt' | 'ocr' }[];
    prompt_template?: string; // For custom hotkeys
};

export type Settings = {
    app: {
        ui_opacity: number;
    };
    routing_defaults: {
        default_llm_connection_id?: string;
        default_stt_connection_id?: string;
    };
    history: {
        enabled: boolean;
    };
};

export const apiClient = {
    healthCheck: async () => {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("Health check failed");
        return res.json();
    },

    getConnections: async (): Promise<ConnectionDefinition[]> => {
        const res = await fetch(`${API_BASE}/connections`);
        if (!res.ok) throw new Error("Failed to fetch connections");
        return res.json();
    },

    createConnection: async (conn: ConnectionDefinition) => {
        const res = await fetch(`${API_BASE}/connections`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(conn)
        });
        if (!res.ok) throw new Error("Failed to create connection");
        return res.json();
    },

    updateConnection: async (id: string, conn: ConnectionDefinition) => {
        const res = await fetch(`${API_BASE}/connections/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(conn)
        });
        if (!res.ok) throw new Error("Failed to update connection");
        return res.json();
    },

    deleteConnection: async (id: string) => {
        const res = await fetch(`${API_BASE}/connections/${id}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Failed to delete connection");
        return res.json();
    },

    saveSecret: async (id: string, secret: string) => {
        const res = await fetch(`${API_BASE}/connections/${id}/secret`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ secret })
        });
        if (!res.ok) throw new Error("Failed to save secret");
        return res.json();
    },

    getSettings: async (): Promise<Settings> => {
        const res = await fetch(`${API_BASE}/settings`);
        if (!res.ok) throw new Error("Failed to fetch settings");
        return res.json();
    },

    updateSettings: async (settings: Partial<Settings>) => {
        const res = await fetch(`${API_BASE}/settings`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings)
        });
        if (!res.ok) throw new Error("Failed to update settings");
        return res.json();
    },

    getHotkeys: async (): Promise<HotkeyDefinition[]> => {
        const res = await fetch(`${API_BASE}/hotkeys`);
        if (!res.ok) throw new Error("Failed to fetch hotkeys");
        return res.json();
    },

    createHotkey: async (hotkey: HotkeyDefinition) => {
        const res = await fetch(`${API_BASE}/hotkeys`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(hotkey)
        });
        if (!res.ok) throw new Error("Failed to create hotkey");
        return res.json();
    },

    deleteHotkey: async (id: string) => {
        const res = await fetch(`${API_BASE}/hotkeys/${id}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Failed to delete hotkey");
        return res.json();
    },

    getUiText: async (): Promise<Record<string, string>> => {
        const res = await fetch(`${API_BASE}/ui-text`);
        if (!res.ok) throw new Error("Failed to fetch UI text");
        return res.json();
    },

    getHistory: async (): Promise<any[]> => {
        const res = await fetch(`${API_BASE}/history`);
        if (!res.ok) throw new Error("Failed to fetch history");
        return res.json();
    },

    executeHotkey: async (id: string, payload?: any) => {
        const res = await fetch(`${API_BASE}/hotkeys/${id}/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload || {})
        });
        if (!res.ok) throw new Error("Failed to execute hotkey");
        return res.json();
    }
};
