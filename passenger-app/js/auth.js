import { apiRequest } from './api.js';

export const auth = {
  getToken() {
    return localStorage.getItem('transitnow_passenger_token');
  },

  getUser() {
    const userStr = localStorage.getItem('transitnow_passenger_user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setSession(token, user) {
    localStorage.setItem('transitnow_passenger_token', token);
    localStorage.setItem('transitnow_passenger_user', JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem('transitnow_passenger_token');
    localStorage.removeItem('transitnow_passenger_user');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async login(username, password) {
    const res = await apiRequest('/api/auth/passenger/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setSession(res.access_token, res.user);
    return res;
  },

  async register(data) {
    const res = await apiRequest('/api/auth/passenger/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    this.setSession(res.access_token, res.user);
    return res;
  },

  async logout() {
    try {
      await apiRequest('/api/auth/passenger/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout api notification error:', e);
    }
    this.clearSession();
    window.location.href = '/passenger/login';
  },

  async fetchProfile() {
    return await apiRequest('/api/passenger/profile');
  }
};
