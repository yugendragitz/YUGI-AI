import { api } from '@/api/axios';
import type { AuthResponse, MessageResponse, User } from '@/types/auth';

export const authService = {
  async register(data: any): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  async login(data: URLSearchParams): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', data, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  async logout(): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/auth/logout');
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};
