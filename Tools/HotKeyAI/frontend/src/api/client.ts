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

export const apiClient = {
    healthCheck: async () => {
        const response = await fetch(`${BASE_URL}/health`);
        return response.json();
    },

    getHotkeys: async (): Promise<HotkeyDefinition[]> => {
        const response = await fetch(`${BASE_URL}/hotkeys`);
        return response.json();
    },

    executeHotkey: async (id: string) => {
        const response = await fetch(`${BASE_URL}/execute/${id}`, {
            method: "POST",
        });
        return response.json();
    },
};
