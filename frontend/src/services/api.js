import axios from 'axios';
import useAuthStore from '../store/authStore';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor to add JWT
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response Interceptor to handle unauthorized
api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    useAuthStore.getState().logout();
  }
  return Promise.reject(error);
});

export const authService = {
  login: async (badge_no, pin) => {
    const response = await api.post('/auth/login', { badge_no, pin });
    return response.data;
  },
  me: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

export const legalService = {
  query: async (question, language = 'en') => {
    const response = await api.post(`/legal/query?question=${encodeURIComponent(question)}&language=${language}`);
    return response.data;
  }
};

export const firService = {
  generate: async (description) => {
    const response = await api.post('/fir/generate', { incident_desc: description });
    return response.data;
  }
};

export default api;
