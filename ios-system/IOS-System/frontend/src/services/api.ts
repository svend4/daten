/**
 * API Service - Centralized API communication layer
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { toast } from 'sonner'

// Types
export interface ApiError {
  message: string
  code?: string
  details?: any
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  hasMore: boolean
}

// API Configuration
// In production, use same origin (empty string). In development, use VITE_API_URL or localhost
const API_BASE_URL = import.meta.env.VITE_ENV === 'production'
  ? ''
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000')
const API_TIMEOUT = 30000 // 30 seconds

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Handle 401 - Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
      toast.error('Session expired. Please login again.')
    }

    // Handle 403 - Forbidden
    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action.')
    }

    // Handle 500 - Server error
    if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.')
    }

    return Promise.reject(error)
  }
)

// API Service
class ApiService {
  // Authentication
  async login(username: string, password: string) {
    const response = await apiClient.post('/api/auth/login', { username, password })
    return response.data
  }

  async logout() {
    await apiClient.post('/api/auth/logout')
    localStorage.removeItem('auth_token')
  }

  async getCurrentUser() {
    const response = await apiClient.get('/api/auth/me')
    return response.data
  }

  // Documents
  async getDocuments(params?: {
    page?: number
    limit?: number
    search?: string
    category?: string
    status?: string
  }) {
    const response = await apiClient.get<PaginatedResponse<any>>('/api/documents', { params })
    return response.data
  }

  async getDocument(id: string) {
    const response = await apiClient.get(`/api/documents/${id}`)
    return response.data
  }

  async createDocument(data: {
    title: string
    content: string
    category?: string
    tags?: string[]
  }) {
    const response = await apiClient.post('/api/documents', data)
    return response.data
  }

  async updateDocument(id: string, data: Partial<{
    title: string
    content: string
    category?: string
    tags?: string[]
  }>) {
    const response = await apiClient.patch(`/api/documents/${id}`, data)
    return response.data
  }

  async deleteDocument(id: string) {
    await apiClient.delete(`/api/documents/${id}`)
  }

  // Search
  async search(query: string, params?: {
    limit?: number
    category?: string
  }) {
    const response = await apiClient.get('/api/search', {
      params: { q: query, ...params }
    })
    return response.data
  }

  async semanticSearch(query: string, limit: number = 10) {
    const response = await apiClient.post('/api/search/semantic', {
      query,
      limit
    })
    return response.data
  }

  // AI Features
  async summarizeDocument(documentId: string) {
    const response = await apiClient.post(`/api/ai/summarize/${documentId}`)
    return response.data
  }

  async chatWithDocument(documentId: string, message: string) {
    const response = await apiClient.post(`/api/ai/chat/${documentId}`, {
      message
    })
    return response.data
  }

  // Dashboard & Analytics
  async getDashboardStats() {
    const response = await apiClient.get('/api/dashboard')
    return response.data
  }

  async getRecentActivity(limit: number = 10) {
    const response = await apiClient.get('/api/activity/recent', {
      params: { limit }
    })
    return response.data
  }

  // Tags
  async getTags() {
    const response = await apiClient.get('/api/tags')
    return response.data
  }

  async createTag(name: string, description?: string, color?: string) {
    const response = await apiClient.post('/api/tags', {
      name,
      description,
      color
    })
    return response.data
  }

  // Knowledge Graph
  async getGraphEntity(entityId: string) {
    const response = await apiClient.get(`/api/graph/entity/${entityId}`)
    return response.data
  }

  async getEntityRelations(entityId: string) {
    const response = await apiClient.get(`/api/graph/entity/${entityId}/relations`)
    return response.data
  }

  // Health Check
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  }
}

// Export singleton instance
export const api = new ApiService()
export default api
