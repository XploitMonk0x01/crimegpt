import axios from 'axios';
import useAuthStore from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
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

// ─────────────── Auth Service ───────────────
export const authService = {
  login: async (badge_no, pin) => {
    const response = await api.post('/auth/login', { badge_no, pin });
    return response.data;
  },
  me: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  refresh: async (refresh_token) => {
    const response = await api.post('/auth/refresh', { refresh_token });
    return response.data;
  },
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
  register: async (data) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
};

// ─────────────── FIR Service ───────────────
export const firService = {
  generate: async (description) => {
    const response = await api.post('/fir/generate', { incident_description: description });
    return response.data;
  },
  submit: async (data) => {
    const response = await api.post('/fir/submit', data);
    return response.data;
  },
  list: async ({ status, page = 1, pageSize = 20 } = {}) => {
    const params = { page, page_size: pageSize };
    if (status) params.status = status;
    const response = await api.get('/fir/list', { params });
    return response.data;
  },
  getById: async (firId) => {
    const response = await api.get(`/fir/${firId}`);
    return response.data;
  },
  edit: async (firId, data) => {
    const response = await api.patch(`/fir/${firId}/edit`, data);
    return response.data;
  },
  review: async (firId, data) => {
    const response = await api.post(`/fir/${firId}/review`, data);
    return response.data;
  },
};

// ─────────────── Legal Intelligence Service ───────────────
export const legalService = {
  query: async (question, language = 'en') => {
    const response = await api.post(`/legal/query?question=${encodeURIComponent(question)}&language=${language}`);
    return response.data;
  },
  searchSections: async (keyword, { act, nResults = 10 } = {}) => {
    const params = { keyword, n_results: nResults };
    if (act) params.act = act;
    const response = await api.get('/legal/sections/search', { params });
    return response.data;
  },
  corpusStats: async () => {
    const response = await api.get('/legal/corpus/stats');
    return response.data;
  },
};

// ─────────────── Dashboard Service ───────────────
export const dashboardService = {
  getOfficerDashboard: async () => {
    const response = await api.get('/dashboard/officer');
    return response.data;
  },
  getInspectorDashboard: async () => {
    const response = await api.get('/dashboard/inspector');
    return response.data;
  },
  getAnalytics: async () => {
    const response = await api.get('/dashboard/analytics');
    return response.data;
  },
  getAuditLogs: async ({ offset = 0, limit = 50 } = {}) => {
    const response = await api.get('/dashboard/audit-logs', { params: { offset, limit } });
    return response.data;
  },
};

// ─────────────── Evidence Service ───────────────
export const evidenceService = {
  upload: async (file, firId, description = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fir_id', firId);
    formData.append('description', description);
    const response = await api.post('/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getCustody: async (evidenceId) => {
    const response = await api.get(`/evidence/${evidenceId}/custody`);
    return response.data;
  },
  verifyIntegrity: async (evidenceId) => {
    const response = await api.get(`/evidence/${evidenceId}/verify`);
    return response.data;
  },
};

// ─────────────── Case Linkage Service ───────────────
export const caseService = {
  findSimilar: async (firId, threshold = 0.7) => {
    const response = await api.get(`/cases/similar/${firId}`, { params: { threshold } });
    return response.data;
  },
  linkCases: async (data) => {
    const response = await api.post('/cases/link', data);
    return response.data;
  },
  getClusters: async () => {
    const response = await api.get('/cases/clusters');
    return response.data;
  },
};

// ─────────────── NLP Service ───────────────
export const nlpService = {
  transcribe: async () => {
    const response = await api.post('/nlp/transcribe');
    return response.data;
  },
  translate: async () => {
    const response = await api.post('/nlp/translate');
    return response.data;
  },
  getLanguages: async () => {
    const response = await api.get('/nlp/languages');
    return response.data;
  },
};

export default api;
