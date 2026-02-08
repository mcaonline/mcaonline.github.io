const BASE_URL = "http://localhost:8000";

export interface HotkeyDefinition {
    id?: string;
    kind: 'builtin' | 'custom';
    mode: 'ai_transform' | 'local_transform' | 'static_text_paste' | 'prompt_prefill_only';
    display_key: string;
    description_key: string;
    enabled: boolean;
    sequence: number;
}

export interface ConnectionDefinition {
    connection_id: string;
    provider_id: string;
    model_id: string;
    endpoint_url?: string;
    system_prompt?: string;
}

export const apiClient = {
    healthCheck: async () => {
        const response = await fetch(`${BASE_URL}/health`);
        return response.json();
    },

    getHotkeys: async (): Promise<HotkeyDefinition[]> => {
        const response = await fetch(`${BASE_URL}/hotkeys`);
        return response.json();
    },

    getUiText: async (): Promise<Record<string, string>> => {
        const response = await fetch(`${BASE_URL}/ui-text`);
        return response.json();
    },

    executeHotkey: async (id: string) => {
        const response = await fetch(`${BASE_URL}/execute/${id}`, {
            method: "POST",
        });
        return response.json();
    },

    getConnections: async (): Promise<ConnectionDefinition[]> => {
        const response = await fetch(`${BASE_URL}/connections`);
        return response.json();
    },

    createConnection: async (connection: ConnectionDefinition) => {
        const response = await fetch(`${BASE_URL}/connections`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(connection)
        });
        return response.json();
    },

    deleteConnection: async (id: string) => {
        const response = await fetch(`${BASE_URL}/connections/${id}`, {
            method: "DELETE"
        });
        return response.json();
    },

    saveSecret: async (connectionId: string, secretValue: string) => {
        const response = await fetch(`${BASE_URL}/secrets?connection_id=${connectionId}&secret_value=${encodeURIComponent(secretValue)}`, {
            method: "POST"
        });
        return response.json();
    }
};
