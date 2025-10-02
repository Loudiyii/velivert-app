import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) => api.post('/auth/login', { email, password }),
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    api.post('/auth/register', data),
  getCurrentUser: () => api.get('/auth/me'),
}

// Station API
export const stationsApi = {
  getCurrentStatus: () => api.get('/stations/current'),
  getById: (stationId: string) => api.get(`/stations/${stationId}`),
  getHistory: (stationId: string, params: any) => api.get(`/stations/${stationId}/history`, { params }),
}

// Bikes API
export const bikesApi = {
  getCurrentStatus: () => api.get('/bikes/current'),
  getById: (bikeId: string) => api.get(`/bikes/${bikeId}`),
  getDisabled: () => api.get('/bikes/disabled/list'),
}

// Interventions API
export const interventionsApi = {
  getAll: (params: any) => api.get('/interventions/', { params }),
  list: (params: any) => api.get('/interventions/', { params }),
  getPending: () => api.get('/interventions/pending'),
  getById: (id: string) => api.get(`/interventions/${id}`),
  create: (data: any) => api.post('/interventions/', data),
  update: (id: string, data: any) => api.patch(`/interventions/${id}`, data),
}

// Analytics API
export const analyticsApi = {
  getOccupancyHeatmap: (params: any) => api.get('/analytics/stations/occupancy-heatmap', { params }),
  getIdleBikes: (params: any) => api.get('/analytics/bikes/idle-detection', { params }),
  getStationOccupancy: (stationId: string, params: any) =>
    api.get(`/analytics/stations/${stationId}/occupancy-rate`, { params }),
}

// Routes API
export const routesApi = {
  optimize: (data: any) => api.post('/routes/optimize', data),
}

export default api