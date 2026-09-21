import { driverApiRequest } from './driver-api.js';

export const driverAuth = {
  getToken() {
    return localStorage.getItem('transitnow_driver_token');
  },

  getDriver() {
    const dStr = localStorage.getItem('transitnow_driver_data');
    try {
      return dStr ? JSON.parse(dStr) : null;
    } catch {
      return null;
    }
  },

  setSession(token, driver) {
    localStorage.setItem('transitnow_driver_token', token);
    localStorage.setItem('transitnow_driver_data', JSON.stringify(driver));
  },

  clearSession() {
    localStorage.removeItem('transitnow_driver_token');
    localStorage.removeItem('transitnow_driver_data');
    localStorage.removeItem('transitnow_active_trip');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async login(driver_id, password) {
    const res = await driverApiRequest('/api/auth/driver/login', {
      method: 'POST',
      body: JSON.stringify({ driver_id, password })
    });
    this.setSession(res.access_token, res.user);
    return res;
  },

  async logout() {
    try {
      await driverApiRequest('/api/auth/driver/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Driver logout notification error:', e);
    }
    this.clearSession();
    window.location.href = '/driver-app/login';
  },

  async fetchProfile() {
    return await driverApiRequest('/api/driver/profile');
  }
};
