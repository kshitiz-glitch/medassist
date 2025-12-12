/**
 * API Client
 * Axios configuration and API service functions
 */

import axios from 'axios';
import type { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Types
export interface User {
    id: string;
    email: string;
    role: 'patient' | 'doctor' | 'admin';
    is_active: boolean;
    created_at: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface Doctor {
    id: string;
    user_id: string;
    name: string;
    specialty: string;
    phone?: string;
    bio?: string;
    available_slots: Record<string, Array<{ start: string; end: string }>>;
    consultation_duration: number;
    created_at: string;
}

export interface Patient {
    id: string;
    user_id: string;
    name: string;
    phone?: string;
    date_of_birth?: string;
    medical_history: Record<string, unknown>;
    created_at: string;
}

export interface Appointment {
    id: string;
    doctor_id: string;
    patient_id: string;
    scheduled_time: string;
    duration_minutes: number;
    status: 'scheduled' | 'completed' | 'cancelled' | 'no_show' | 'rescheduled';
    symptoms?: string;
    diagnosis?: string;
    notes?: string;
    google_calendar_event_id?: string;
    confirmation_sent: boolean;
    created_at: string;
    doctor_name?: string;  // Added for display purposes
    doctor?: Doctor;
    patient?: Patient;
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
}

export interface ChatResponse {
    message: string;
    session_id: string;
    tools_used: string[];
    context: Record<string, unknown>;
}

export interface ConversationHistory {
    id: string;
    session_id: string;
    messages: ChatMessage[];
    context: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

export interface AvailabilitySlot {
    time: string;
    datetime: string;
    available: boolean;
}

export interface DoctorStats {
    doctor_id: string;
    doctor_name: string;
    today_appointments: number;
    yesterday_visits: number;
    tomorrow_appointments: number;
    total_patients: number;
}

// Auth API
export const authApi = {
    login: async (email: string, password: string): Promise<LoginResponse> => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await api.post<LoginResponse>('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.data;
    },

    register: async (data: {
        email: string;
        password: string;
        name: string;
        role: 'patient' | 'doctor';
    }): Promise<LoginResponse> => {
        const response = await api.post<LoginResponse>('/auth/register', data);
        return response.data;
    },

    getCurrentUser: async (): Promise<User> => {
        const response = await api.get<User>('/auth/me');
        return response.data;
    },

    getProfile: async (): Promise<Doctor | Patient> => {
        const response = await api.get('/auth/me/profile');
        return response.data;
    },
};

// Chat API
export const chatApi = {
    sendMessage: async (message: string, sessionId?: string): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/chat/message', {
            message,
            session_id: sessionId,
        });
        return response.data;
    },

    getHistory: async (sessionId?: string, limit = 10): Promise<ConversationHistory[]> => {
        const params = new URLSearchParams();
        if (sessionId) params.append('session_id', sessionId);
        params.append('limit', limit.toString());

        const response = await api.get<ConversationHistory[]>(`/chat/history?${params}`);
        return response.data;
    },

    getSession: async (sessionId: string): Promise<ConversationHistory> => {
        const response = await api.get<ConversationHistory>(`/chat/session/${sessionId}`);
        return response.data;
    },

    clearSession: async (sessionId: string): Promise<void> => {
        await api.delete(`/chat/session/${sessionId}`);
    },

    createNewSession: async (): Promise<{ session_id: string }> => {
        const response = await api.post<{ session_id: string }>('/chat/new-session');
        return response.data;
    },

    getPromptHistory: async (limit = 50): Promise<Array<{
        id: string;
        session_id: string;
        prompt: string;
        response: string;
        tools_used: string[];
        created_at: string;
    }>> => {
        const response = await api.get(`/chat/prompts?limit=${limit}`);
        return response.data;
    },

    getPromptStats: async (): Promise<{
        total_prompts: number;
        avg_processing_time_ms: number;
        most_used_tools: Array<{ tool: string; count: number }>;
    }> => {
        const response = await api.get('/chat/prompts/stats');
        return response.data;
    },
};

// Doctors API
export const doctorsApi = {
    list: async (specialty?: string): Promise<Doctor[]> => {
        const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : '';
        const response = await api.get<Doctor[]>(`/doctors${params}`);
        return response.data;
    },

    getById: async (id: string): Promise<Doctor> => {
        const response = await api.get<Doctor>(`/doctors/${id}`);
        return response.data;
    },

    search: async (name: string): Promise<Doctor[]> => {
        const response = await api.get<Doctor[]>(`/doctors/search/${encodeURIComponent(name)}`);
        return response.data;
    },

    getAvailability: async (doctorId: string, date?: string): Promise<{
        doctor_id: string;
        doctor_name: string;
        date?: string;
        day?: string;
        available_slots: AvailabilitySlot[];
        consultation_duration: number;
    }> => {
        const params = date ? `?date=${date}` : '';
        const response = await api.get(`/doctors/${doctorId}/availability${params}`);
        return response.data;
    },

    getStats: async (doctorId: string): Promise<DoctorStats> => {
        const response = await api.get<DoctorStats>(`/doctors/${doctorId}/stats`);
        return response.data;
    },

    update: async (doctorId: string, data: Partial<Doctor>): Promise<Doctor> => {
        const response = await api.put<Doctor>(`/doctors/${doctorId}`, data);
        return response.data;
    },
};

// Patients API
export const patientsApi = {
    getCurrent: async (): Promise<Patient> => {
        const response = await api.get<Patient>('/patients/me');
        return response.data;
    },

    updateCurrent: async (data: Partial<Patient>): Promise<Patient> => {
        const response = await api.put<Patient>('/patients/me', data);
        return response.data;
    },

    getAppointments: async (options?: {
        status?: string;
        upcoming_only?: boolean;
    }): Promise<Appointment[]> => {
        const params = new URLSearchParams();
        if (options?.status) params.append('status', options.status);
        if (options?.upcoming_only) params.append('upcoming_only', 'true');

        const response = await api.get<Appointment[]>(`/patients/me/appointments?${params}`);
        return response.data;
    },
};

// Appointments API
export const appointmentsApi = {
    create: async (data: {
        doctor_id: string;
        scheduled_time: string;
        duration_minutes?: number;
        symptoms?: string;
    }): Promise<Appointment> => {
        const response = await api.post<Appointment>('/appointments', data);
        return response.data;
    },

    list: async (options?: {
        status?: string;
        date?: string;
    }): Promise<Appointment[]> => {
        const params = new URLSearchParams();
        if (options?.status) params.append('status', options.status);
        if (options?.date) params.append('date', options.date);

        const response = await api.get<Appointment[]>(`/appointments?${params}`);
        return response.data;
    },

    getById: async (id: string): Promise<Appointment> => {
        const response = await api.get<Appointment>(`/appointments/${id}`);
        return response.data;
    },

    update: async (id: string, data: Partial<Appointment>): Promise<Appointment> => {
        const response = await api.put<Appointment>(`/appointments/${id}`, data);
        return response.data;
    },

    cancel: async (id: string, reason?: string): Promise<void> => {
        const params = reason ? `?reason=${encodeURIComponent(reason)}` : '';
        await api.delete(`/appointments/${id}${params}`);
    },

    complete: async (id: string, data?: {
        diagnosis?: string;
        notes?: string;
    }): Promise<void> => {
        await api.post(`/appointments/${id}/complete`, data);
    },
};

export default api;
