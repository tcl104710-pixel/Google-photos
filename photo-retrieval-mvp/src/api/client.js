import axios from 'axios';

let API_BASE = import.meta.env.VITE_API_BASE_URL || '';
if (API_BASE && !API_BASE.startsWith('http')) {
  API_BASE = 'https://' + API_BASE;
}

// Configure standard axios client for backend API
export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auth = {
  getLoginUrl: () => `${API_BASE}/api/auth/google`,
  checkSyncStatus: async () => {
    const res = await api.get('/api/user/sync-status');
    return res.data;
  },
};

export const session = {
  start: async () => {
    const res = await api.post('/api/session/start');
    return res.data; // { session_id }
  },
  sendMessage: async (sessionId, text) => {
    const res = await api.post(`/api/session/${sessionId}/message`, { text });
    return res.data; // { response_text, candidates, context_snapshot }
  },
  sendFeedback: async (sessionId, photoId, feedback) => {
    const res = await api.post(`/api/session/${sessionId}/feedback`, { photo_id: photoId, feedback });
    return res.data; // { candidates, context_snapshot }
  },
  end: async (sessionId) => {
    const res = await api.post(`/api/session/${sessionId}/end`);
    return res.data;
  },
};
