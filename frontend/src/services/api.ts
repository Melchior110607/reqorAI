import axios from 'axios';
import { AuthResponse, LoginData, RegisterData, User, Client, Request, RequestWithClient } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (data: LoginData): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateCurrentUser: async (data: Partial<User>): Promise<User> => {
    const response = await api.put('/auth/me', data);
    return response.data;
  },
};

// Clients API
export const clientsAPI = {
  getAll: async (): Promise<Client[]> => {
    const response = await api.get('/clients');
    return response.data;
  },

  getById: async (id: number): Promise<Client> => {
    const response = await api.get(`/clients/${id}`);
    return response.data;
  },

  create: async (data: Omit<Client, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Client> => {
    const response = await api.post('/clients', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Client>): Promise<Client> => {
    const response = await api.put(`/clients/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/clients/${id}`);
  },
};

// Requests API
export const requestsAPI = {
  getAll: async (params?: {
    request_type?: string;
    status?: string;
    priority?: string;
    client_id?: number;
  }): Promise<RequestWithClient[]> => {
    const response = await api.get('/requests', { params });
    return response.data;
  },

  getById: async (id: number): Promise<RequestWithClient> => {
    const response = await api.get(`/requests/${id}`);
    return response.data;
  },

  getByClient: async (clientId: number, requestType?: string): Promise<Request[]> => {
    const params = requestType ? { request_type: requestType } : {};
    const response = await api.get(`/requests/client/${clientId}`, { params });
    return response.data;
  },

  create: async (data: Omit<Request, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Request> => {
    const response = await api.post('/requests', data);
    return response.data;
  },

  update: async (id: number, data: Partial<Request>): Promise<Request> => {
    const response = await api.put(`/requests/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/requests/${id}`);
  },

  regenerateDraft: async (requestId: number): Promise<any> => {
    const response = await api.post(`/requests/${requestId}/regenerate-draft`);
    return response.data;
  },

  sendDraftResponse: async (requestId: number, attachments?: File[]): Promise<any> => {
    if (attachments && attachments.length > 0) {
      // If we have attachments, use FormData
      const formData = new FormData();
      attachments.forEach(file => {
        formData.append('attachments', file);
      });
      
      const response = await api.post(`/requests/${requestId}/send-draft`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } else {
      // No attachments, regular POST
      const response = await api.post(`/requests/${requestId}/send-draft`);
      return response.data;
    }
  },

  configureReminder: async (requestId: number, config: {
    reminder_enabled: boolean;
    reminder_frequency: string;
    reminder_message?: string;
  }): Promise<any> => {
    const response = await api.post(`/requests/${requestId}/configure-reminder`, null, {
      params: config
    });
    return response.data;
  },

  sendReminderNow: async (requestId: number): Promise<any> => {
    const response = await api.post(`/requests/${requestId}/send-reminder-now`);
    return response.data;
  },

  getFollowUps: async (requestId: number): Promise<any[]> => {
    const response = await api.get(`/requests/${requestId}/follow-ups`);
    return response.data;
  },

  getConversationThread: async (requestId: number): Promise<any> => {
    const response = await api.get(`/requests/${requestId}/conversation-thread`);
    return response.data;
  },
};

// Dashboard API
export const dashboardAPI = {
  getOverview: async (): Promise<any> => {
    const response = await api.get('/dashboard/overview');
    return response.data;
  },

  getCalendar: async (year: number, month: number): Promise<any> => {
    const response = await api.get('/dashboard/calendar', {
      params: { year, month }
    });
    return response.data;
  },

  getUpcoming: async (days?: number): Promise<any[]> => {
    const response = await api.get('/dashboard/upcoming', {
      params: days ? { days } : {}
    });
    return response.data;
  },

  getOverdueCount: async (): Promise<number> => {
    const response = await api.get('/dashboard/overdue-count');
    return response.data;
  },
};

// Knowledge Base API
export const knowledgeAPI = {
  uploadDocument: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  getDocuments: async (): Promise<any[]> => {
    const response = await api.get('/knowledge/documents');
    return response.data;
  },
  
  deleteDocument: async (docId: number): Promise<void> => {
    await api.delete(`/knowledge/documents/${docId}`);
  }
};

// AI Agent API
export const agentAPI = {
  processEmail: async (emailId: number): Promise<any> => {
    const response = await api.post(`/email/process-with-agent/${emailId}`);
    return response.data;
  }
};

export default api;
