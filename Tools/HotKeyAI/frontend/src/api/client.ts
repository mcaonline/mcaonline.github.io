
import type { components } from './generated-types';

// --- Types derived from OpenAPI-generated schema (SSoT: Python Pydantic models) ---
export type ConnectionDefinition = components['schemas']['ConnectionDefinition'];
export type ActionDefinition = components['schemas']['ActionDefinition'];
export type ProviderInfo = components['schemas']['ProviderInfoResponse'];
export type HistoryEntry = components['schemas']['HistoryEntryResponse'];
export type ExecuteResponse = components['schemas']['ExecuteResponse'];
export type StatusResponse = components['schemas']['StatusResponse'];
export type HealthResponse = components['schemas']['HealthResponse'];

// Settings type kept manual — backend returns model_dump() without a typed response_model,
// so OpenAPI schema shows `unknown`. Must match SettingsSchema in config/settings.py.
export type Settings = {
    schema_version: number;
    app: {
        theme: string;
        language: string;
        ui_opacity: number;
        ui_decorations: boolean;
    };
    actions: {
        main_trigger: {
            chord: string;
            second_v_timeout_ms: number;
        };
    };
    routing_defaults: {
        default_llm_connection_id?: string;
        default_stt_connection_id?: string;
    };
    history: {
        enabled: boolean;
        max_entries: number;
    };
    privacy: {
        trust_notice_ack_for_direct_ai: boolean;
    };
    diagnostics: {
        debug_payload_logging: boolean;
    };
    connections: ConnectionDefinition[];
};

const API_BASE = "http://localhost:8000";

export const apiClient = {
    healthCheck: async (): Promise<HealthResponse> => {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("Health check failed");
        return res.json();
    },

    getConnections: async (): Promise<ConnectionDefinition[]> => {
        const res = await fetch(`${API_BASE}/connections`);
        if (!res.ok) throw new Error("Failed to fetch connections");
        return res.json();
    },

    createConnection: async (conn: ConnectionDefinition): Promise<ConnectionDefinition> => {
        const res = await fetch(`${API_BASE}/connections`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(conn)
        });
        if (!res.ok) throw new Error("Failed to create connection");
        return res.json();
    },

    updateConnection: async (id: string, conn: ConnectionDefinition): Promise<ConnectionDefinition> => {
        const res = await fetch(`${API_BASE}/connections/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(conn)
        });
        if (!res.ok) throw new Error("Failed to update connection");
        return res.json();
    },

    deleteConnection: async (id: string): Promise<StatusResponse> => {
        const res = await fetch(`${API_BASE}/connections/${id}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Failed to delete connection");
        return res.json();
    },

    saveSecret: async (id: string, secret: string): Promise<StatusResponse> => {
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

    updateSettings: async (settings: Partial<Settings>): Promise<Settings> => {
        const res = await fetch(`${API_BASE}/settings`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings)
        });
        if (!res.ok) throw new Error("Failed to update settings");
        return res.json();
    },

    getActions: async (): Promise<ActionDefinition[]> => {
        const res = await fetch(`${API_BASE}/actions`);
        if (!res.ok) throw new Error("Failed to fetch actions");
        return res.json();
    },

    createAction: async (action: ActionDefinition): Promise<ActionDefinition> => {
        const res = await fetch(`${API_BASE}/actions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(action)
        });
        if (!res.ok) throw new Error("Failed to create action");
        return res.json();
    },

    updateAction: async (id: string, action: ActionDefinition): Promise<ActionDefinition> => {
        const res = await fetch(`${API_BASE}/actions/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(action)
        });
        if (!res.ok) throw new Error("Failed to update action");
        return res.json();
    },

    deleteAction: async (id: string): Promise<StatusResponse> => {
        const res = await fetch(`${API_BASE}/actions/${id}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Failed to delete action");
        return res.json();
    },

    getProviders: async (): Promise<ProviderInfo[]> => {
        const res = await fetch(`${API_BASE}/providers`);
        if (!res.ok) throw new Error("Failed to fetch providers");
        return res.json();
    },

    getUiText: async (): Promise<Record<string, string>> => {
        const res = await fetch(`${API_BASE}/ui-text`);
        if (!res.ok) throw new Error("Failed to fetch UI text");
        return res.json();
    },

    getHistory: async (): Promise<HistoryEntry[]> => {
        const res = await fetch(`${API_BASE}/history`);
        if (!res.ok) throw new Error("Failed to fetch history");
        return res.json();
    },

    executeAction: async (id: string, payload?: Record<string, unknown>): Promise<ExecuteResponse> => {
        const res = await fetch(`${API_BASE}/actions/${id}/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload || {})
        });
        if (!res.ok) throw new Error("Failed to execute action");
        return res.json();
    },

    shutdown: async () => {
        try {
            await fetch(`${API_BASE}/shutdown`, { method: "POST" });
        } catch (e) {
            // Ignore error if connection reset (expected)
        }
    }
};
