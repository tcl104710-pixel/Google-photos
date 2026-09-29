import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Configure standard axios client for backend API
export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auth = {
  getLoginUrl: () => `${API_BASE}/auth/google`,
  checkSyncStatus: async () => {
    const res = await api.get('/user/sync-status');
    return res.data;
  },
};

export const session = {
  start: async () => {
    const res = await api.post('/session/start');
    return res.data; // { session_id }
  },
  sendMessage: async (sessionId, text) => {
    const res = await api.post(`/session/${sessionId}/message`, { text });
    return res.data; // { response_text, candidates, context_snapshot }
  },
  sendFeedback: async (sessionId, photoId, feedback) => {
    const res = await api.post(`/session/${sessionId}/feedback`, { photo_id: photoId, feedback });
    return res.data; // { candidates, context_snapshot }
  },
  end: async (sessionId) => {
    const res = await api.post(`/session/${sessionId}/end`);
    return res.data;
  },
};
