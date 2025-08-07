/**
 * Authentication utilities and types
 */

import axios from 'axios'
import Cookies from 'js-cookie'

// Types
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  created_at?: string
  updated_at?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface SignupData {
  email: string
  username: string
  password: string
  confirm_password: string
  full_name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// Constants
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000/api/v1' 
  : '/api/v1'

const TOKEN_KEY = 'brain_net_access_token'
const REFRESH_TOKEN_KEY = 'brain_net_refresh_token'

// Token management functions (define these before interceptors)
export const setTokens = (tokens: AuthTokens): void => {
  Cookies.set(TOKEN_KEY, tokens.access_token, { 
    expires: tokens.expires_in / (24 * 60 * 60), // Convert seconds to days
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
  
  Cookies.set(REFRESH_TOKEN_KEY, tokens.refresh_token, { 
    expires: 7, // 7 days
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
}

export const getAccessToken = (): string | undefined => {
  return Cookies.get(TOKEN_KEY)
}

export const getRefreshToken = (): string | undefined => {
  return Cookies.get(REFRESH_TOKEN_KEY)
}

export const clearTokens = (): void => {
  Cookies.remove(TOKEN_KEY)
  Cookies.remove(REFRESH_TOKEN_KEY)
}

export const isAuthenticated = (): boolean => {
  return !!getAccessToken()
}

// Configure axios interceptors
axios.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = getRefreshToken()
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
          })
          
          const tokens: AuthTokens = response.data
          setTokens(tokens)
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`
          return axios(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        clearTokens()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)



// API functions
export const authApi = {
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, credentials)
    return response.data
  },

  async signup(userData: SignupData): Promise<User> {
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, userData)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await axios.get(`${API_BASE_URL}/auth/me`)
    return response.data
  },

  async logout(): Promise<void> {
    try {
      await axios.post(`${API_BASE_URL}/auth/logout`)
    } finally {
      clearTokens()
    }
  },

  async refreshToken(): Promise<AuthTokens> {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken
    })
    return response.data
  }
} 