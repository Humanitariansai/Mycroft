import axios from 'axios';

const API_BASE_URL = 'http://localhost:8004';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const talentAPI = {
  // Health check
  getHealth: () => api.get('/health'),

  // Talent profiles
  getTalentProfiles: () => api.get('/api/talent/profiles'),
  getTalentProfile: (id) => api.get(`/api/talent/profiles/${id}`),

  // Companies
  getCompanyProfiles: () => api.get('/api/companies/profiles'),
  getCompanyProfile: (id) => api.get(`/api/companies/profiles/${id}`),
  getCompanyTalentMetrics: (id) => api.get(`/api/companies/${id}/talent-metrics`),

  // Movements
  getTalentMovements: () => api.get('/api/movements'),
  getMovementSummary: () => api.get('/api/movements/summary'),

  // Investment Signals
  getRecentSignals: () => api.get('/api/signals/recent'),

  // Analytics
  getInfluenceLeaders: () => api.get('/api/analytics/influence-leaders'),
  getMovementTrends: () => api.get('/api/analytics/movement-trends'),

  // Demo functions
  generateDemoMovement: () => api.get('/api/demo/generate-predictive-movement'),
};

export default talentAPI;