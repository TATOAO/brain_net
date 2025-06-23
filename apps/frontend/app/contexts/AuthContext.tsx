'use client'

/**
 * Authentication context for managing user state across the application
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, AuthTokens, authApi, setTokens, clearTokens, isAuthenticated } from '@/app/lib/auth'

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

interface SignupData {
  email: string
  username: string
  password: string
  confirm_password: string
  full_name?: string
}

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

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isLoggedIn = !!user && isAuthenticated()

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      if (isAuthenticated()) {
        try {
          const userData = await authApi.getCurrentUser()
          setUser(userData)
        } catch (error) {
          console.error('Failed to get user data:', error)
          clearTokens()
        }
      }
      setLoading(false)
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
      
      const newUser = await authApi.signup(userData)
      
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