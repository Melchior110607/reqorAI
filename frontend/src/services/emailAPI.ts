import api from './api';
import { EmailConnection, InterceptedEmail, EmailProvider, AuthUrlResponse } from '@/types/email';

export const emailAPI = {
  // OAuth Authentication
  getAuthUrl: async (provider: EmailProvider): Promise<AuthUrlResponse> => {
    const response = await api.get(`/email/auth-url/${provider}`);
    return response.data;
  },

  handleCallback: async (provider: EmailProvider, code: string, state: string): Promise<EmailConnection> => {
    const response = await api.post(`/email/callback/${provider}`, { code, state });
    return response.data;
  },

  // Connections Management
  getConnections: async (): Promise<EmailConnection[]> => {
    const response = await api.get('/email/connections');
    return response.data;
  },

  deleteConnection: async (connectionId: number): Promise<void> => {
    await api.delete(`/email/connections/${connectionId}`);
  },

  syncEmails: async (connectionId: number): Promise<{ message: string }> => {
    const response = await api.post(`/email/sync/${connectionId}`);
    return response.data;
  },

  // Intercepted Emails
  getInterceptedEmails: async (): Promise<InterceptedEmail[]> => {
    const response = await api.get('/email/intercepted');
    return response.data;
  },

  classifyEmail: async (emailId: number): Promise<any> => {
    const response = await api.post(`/email/classify/${emailId}`);
    return response.data;
  },
};
