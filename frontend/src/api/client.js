import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const client = axios.create({ baseURL: API_BASE });

// Inject JWT on every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('medicare_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('medicare_token');
      localStorage.removeItem('medicare_user');
      window.location.href = '/auth';
    }
    return Promise.reject(err);
  }
);

export default client;
