import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  // Accepts either register({ username, email, password })
  // or register(username, email, password)
  register: async (usernameOrData, email, password) => {
    const payload =
      typeof usernameOrData === 'object'
        ? usernameOrData
        : { username: usernameOrData, email, password };
    const response = await api.post('/auth/register', payload);
    return response.data;
  },
};

// Resume API
export const resumeAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getAll: async () => {
    const response = await api.get('/resumes/'); // trailing slash added
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/resumes/${id}`);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/resumes/${id}`);
  },
};

// Job API
export const jobAPI = {
  create: async (jobData) => {
    const response = await api.post('/jobs/', jobData); // trailing slash added
    return response.data;
  },
  getAll: async () => {
    const response = await api.get('/jobs/'); // trailing slash added
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },
  match: async (jobId, resumeIds = null) => {
    const response = await api.post(`/jobs/${jobId}/match`, {
      resume_ids: resumeIds,
    });
    return response.data;
  },
  getRankings: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/rankings`);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/jobs/${id}`);
  },
};

export default api;