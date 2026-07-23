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
  // Lightweight variant — extracts only recommended_sections for live NLP suggestions
  analyzeNarrative: async (description) => {
    try {
      const response = await api.post('/fir/generate', { incident_description: description });
      if (response.data?.success) {
        return response.data?.data?.recommended_sections || [];
      }
    } catch {
      // best-effort — silently ignore
    }
    return [];
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
  upload: async (file, firId, description = '', tags = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('fir_id', firId);
    formData.append('description', description);
    formData.append('tags', tags);
    const response = await api.post('/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  listByFir: async (firId) => {
    const response = await api.get(`/evidence/fir/${firId}`);
    return response.data;
  },
  downloadUrl: (evidenceId) => {
    return `${api.defaults.baseURL}/evidence/${evidenceId}/download`;
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
  transcribe: async (audioBlob, { language = 'en', prompt } = {}) => {
    const formData = new FormData();
    const extension = audioBlob.type?.includes('webm') ? 'webm' : 'wav';
    formData.append('file', audioBlob, `incident-audio.${extension}`);
    if (language) formData.append('language', language);
    if (prompt) formData.append('prompt', prompt);
    const response = await api.post('/nlp/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  translate: async (text, sourceLang = 'en', targetLang = 'hi') => {
    const formData = new FormData();
    formData.append('text', text);
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);
    const response = await api.post('/nlp/translate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getLanguages: async () => {
    const response = await api.get('/nlp/languages');
    return response.data;
  },
};

// ─────────────── Document Generation Service ───────────────
export const documentService = {
  getTypes: async () => {
    const response = await api.get('/documents/types');
    return response.data;
  },
  generate: async (firId, documentType, { language = 'en', additionalContext } = {}) => {
    const response = await api.post('/documents/generate', {
      fir_id: firId,
      document_type: documentType,
      language,
      additional_context: additionalContext,
    });
    return response.data;
  },
  exportPdf: async (data) => {
    const response = await api.post('/documents/export-pdf', data, {
      responseType: 'blob',
    });
    return response.data;
  },
};

// ─────────────── Case Diary Service ───────────────
export const caseDiaryService = {
  getEntryTypes: async () => {
    const response = await api.get('/diary/types');
    return response.data;
  },
  addEntry: async (firId, data) => {
    const response = await api.post(`/diary/${firId}/entry`, data);
    return response.data;
  },
  getDiary: async (firId) => {
    const response = await api.get(`/diary/${firId}`);
    return response.data;
  },
  deleteEntry: async (entryId) => {
    const response = await api.delete(`/diary/entry/${entryId}`);
    return response.data;
  },
};

// ─────────────── Search Service ───────────────
export const searchService = {
  searchFirs: async (query, { page = 1, pageSize = 20 } = {}) => {
    const response = await api.get('/search', {
      params: { q: query, page, page_size: pageSize },
    });
    return response.data;
  },
};

// ─────────────── CCTNS & BharatPol Interoperability Service ───────────────
export const cctnsService = {
  syncFir: async (firId) => {
    const response = await api.post(`/cctns/sync-fir/${firId}`);
    return response.data;
  },
  verifyPerson: async (query) => {
    const response = await api.get('/cctns/verify-person', { params: { query } });
    return response.data;
  },
  getStatus: async (firId) => {
    const response = await api.get(`/cctns/status/${firId}`);
    return response.data;
  },
};

// ─────────────── LERS Cyber Portal Service ───────────────
export const lersService = {
  getPlatforms: async () => {
    const response = await api.get('/lers/platforms');
    return response.data;
  },
  getRequestTypes: async () => {
    const response = await api.get('/lers/request-types');
    return response.data;
  },
  generate: async (payload) => {
    const response = await api.post('/lers/generate', payload);
    return response.data;
  },
};

export default api;

