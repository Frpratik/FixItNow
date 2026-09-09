import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT access token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fixitnow_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('fixitnow_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefresh } = res.data;
          localStorage.setItem('fixitnow_access_token', access_token);
          if (newRefresh) {
            localStorage.setItem('fixitnow_refresh_token', newRefresh);
          }
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('fixitnow_access_token');
          localStorage.removeItem('fixitnow_refresh_token');
          localStorage.removeItem('fixitnow_user');
          window.location.href = '/login';
          return Promise.reject(refreshErr);
        }
      }
    }
    return Promise.reject(error);
  }
);
