import axios from 'axios';

// Configure standard axios client for backend API
export const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auth = {
  getLoginUrl: () => 'http://localhost:8000/auth/google',
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
