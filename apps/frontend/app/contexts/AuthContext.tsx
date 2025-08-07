'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

// Types
interface User {
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

interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface SignupData {
  email: string
  username: string
  password: string
  confirm_password: string
  full_name?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  signup: (userData: SignupData) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  isLoggedIn: boolean
}

// Constants
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000/api/v1' 
  : '/api/v1'

const TOKEN_KEY = 'brain_net_access_token'
const REFRESH_TOKEN_KEY = 'brain_net_refresh_token'

// Token management functions
const setTokens = (tokens: AuthTokens): void => {
  if (typeof window === 'undefined') return
  
  const Cookies = require('js-cookie')
  Cookies.set(TOKEN_KEY, tokens.access_token, { 
    expires: tokens.expires_in / (24 * 60 * 60),
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
  
  Cookies.set(REFRESH_TOKEN_KEY, tokens.refresh_token, { 
    expires: 7,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  })
}

const getAccessToken = (): string | undefined => {
  if (typeof window === 'undefined') return undefined
  
  const Cookies = require('js-cookie')
  return Cookies.get(TOKEN_KEY)
}

const getRefreshToken = (): string | undefined => {
  if (typeof window === 'undefined') return undefined
  
  const Cookies = require('js-cookie')
  return Cookies.get(REFRESH_TOKEN_KEY)
}

const clearTokens = (): void => {
  if (typeof window === 'undefined') return
  
  const Cookies = require('js-cookie')
  Cookies.remove(TOKEN_KEY)
  Cookies.remove(REFRESH_TOKEN_KEY)
}

const isAuthenticated = (): boolean => {
  return !!getAccessToken()
}

// API functions
const authApi = {
  async login(credentials: { email: string; password: string }): Promise<AuthTokens> {
    const axios = require('axios')
    const response = await axios.post(`${API_BASE_URL}/auth/login`, credentials)
    return response.data
  },

  async signup(userData: SignupData): Promise<User> {
    const axios = require('axios')
    const response = await axios.post(`${API_BASE_URL}/auth/signup`, userData)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const axios = require('axios')
    const response = await axios.get(`${API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`
      }
    })
    return response.data
  },

  async logout(): Promise<void> {
    try {
      const axios = require('axios')
      await axios.post(`${API_BASE_URL}/auth/logout`)
    } finally {
      clearTokens()
    }
  }
}

// Context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isLoggedIn = !!user && isAuthenticated()

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (typeof window !== 'undefined' && isAuthenticated()) {
          try {
            const userData = await authApi.getCurrentUser()
            setUser(userData)
          } catch (error) {
            console.error('Failed to get user data:', error)
            clearTokens()
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (email: string, password: string): Promise<void> => {
    try {
      setLoading(true)
      setError(null)
      
      const tokens: AuthTokens = await authApi.login({ email, password })
      setTokens(tokens)
      
      const userData = await authApi.getCurrentUser()
      setUser(userData)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const signup = async (userData: SignupData): Promise<void> => {
    try {
      setLoading(true)
      setError(null)
      
      await authApi.signup(userData)
      
      // After successful signup, log the user in
      await login(userData.email, userData.password)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Signup failed'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const logout = async (): Promise<void> => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      clearTokens()
    }
  }

  const refreshUser = async (): Promise<void> => {
    if (isAuthenticated()) {
      try {
        const userData = await authApi.getCurrentUser()
        setUser(userData)
      } catch (error) {
        console.error('Failed to refresh user data:', error)
        await logout()
      }
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    signup,
    logout,
    refreshUser,
    isLoggedIn,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
} 