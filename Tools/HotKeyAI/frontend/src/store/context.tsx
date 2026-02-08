
import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { apiClient, ConnectionDefinition, HotkeyDefinition, Settings } from '../api/client';

// State Interface
interface AppState {
    status: 'initializing' | 'connected' | 'offline' | 'error';
    hotkeys: HotkeyDefinition[];
    connections: ConnectionDefinition[];
    settings: Settings | null;
    uiText: Record<string, string>;
    history: any[];
    activeDefaults: {
        llm?: string;
        stt?: string;
    };
    lastOutput: string;
}

// Initial State
const initialState: AppState = {
    status: 'initializing',
    hotkeys: [],
    connections: [],
    settings: null,
    uiText: {},
    history: [],
    activeDefaults: {},
    lastOutput: ""
};

// Actions
type Action =
    | { type: 'SET_STATUS'; payload: AppState['status'] }
    | { type: 'SET_DATA'; payload: { hotkeys: HotkeyDefinition[], uiText: Record<string, string>, settings: Settings, connections: ConnectionDefinition[] } }
    | { type: 'SET_HISTORY'; payload: any[] }
    | { type: 'SET_LAST_OUTPUT'; payload: string }
    | { type: 'UPDATE_SETTINGS'; payload: Settings }
    | { type: 'UPDATE_CONNECTIONS'; payload: ConnectionDefinition[] };

// Reducer
function appReducer(state: AppState, action: Action): AppState {
    switch (action.type) {
        case 'SET_STATUS':
            return { ...state, status: action.payload };
        case 'SET_DATA':
            return {
                ...state,
                hotkeys: action.payload.hotkeys,
                uiText: action.payload.uiText,
                settings: action.payload.settings,
                connections: action.payload.connections,
                activeDefaults: {
                    llm: action.payload.settings.routing_defaults?.default_llm_connection_id,
                    stt: action.payload.settings.routing_defaults?.default_stt_connection_id
                }
            };
        case 'SET_HISTORY':
            return { ...state, history: action.payload };
        case 'SET_LAST_OUTPUT':
            return { ...state, lastOutput: action.payload };
        case 'UPDATE_SETTINGS':
            return {
                ...state,
                settings: action.payload,
                activeDefaults: {
                    llm: action.payload.routing_defaults?.default_llm_connection_id,
                    stt: action.payload.routing_defaults?.default_stt_connection_id
                }
            };
        case 'UPDATE_CONNECTIONS':
            return { ...state, connections: action.payload };
        default:
            return state;
    }
}

// Context
const AppContext = createContext<{
    state: AppState;
    dispatch: React.Dispatch<Action>;
    refreshData: () => Promise<void>;
    refreshHistory: () => Promise<void>;
} | undefined>(undefined);

// Provider
export const AppProvider = ({ children }: { children: ReactNode }) => {
    const [state, dispatch] = useReducer(appReducer, initialState);

    const refreshData = async () => {
        try {
            await apiClient.healthCheck();
            const [hotkeys, uiText, settings, connections] = await Promise.all([
                apiClient.getHotkeys(),
                apiClient.getUiText(),
                apiClient.getSettings(),
                apiClient.getConnections()
            ]);

            dispatch({
                type: 'SET_DATA',
                payload: { hotkeys, uiText, settings, connections }
            });
            dispatch({ type: 'SET_STATUS', payload: 'connected' });
        } catch (e) {
            console.error("Failed to refresh data", e);
            dispatch({ type: 'SET_STATUS', payload: 'offline' });
        }
    };

    const refreshHistory = async () => {
        try {
            const history = await apiClient.getHistory();
            dispatch({ type: 'SET_HISTORY', payload: history });
        } catch (e) {
            console.error("Failed to refresh history", e);
        }
    };

    useEffect(() => {
        refreshData();
        // health check polling
        const interval = setInterval(() => {
            apiClient.healthCheck().then(() => {
                if (state.status === 'offline') refreshData();
            }).catch(() => {
                if (state.status === 'connected') dispatch({ type: 'SET_STATUS', payload: 'offline' });
            });
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <AppContext.Provider value={{ state, dispatch, refreshData, refreshHistory }}>
            {children}
        </AppContext.Provider>
    );
};

// Hook
export const useApp = () => {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error("useApp must be used within an AppProvider");
    }
    return context;
};
