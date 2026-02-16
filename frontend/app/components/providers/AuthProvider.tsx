'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { authApi } from '@/lib/api'

interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  whatsapp_connected: boolean
  subscription_tier: string
  api_usage_limit: number
  api_usage_count: number
  timezone: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const refreshUser = async () => {
    try {
      const token = Cookies.get('access_token')
      if (!token) {
        setUser(null)
        return
      }
      
      const response = await authApi.getUser()
      setUser(response.user)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      setUser(null)
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
    }
  }

  const login = async (username: string, password: string) => {
    const response = await authApi.login(username, password)
    
    Cookies.set('access_token', response.access)
    Cookies.set('refresh_token', response.refresh)
    setUser(response.user)
    
    router.push('/dashboard')
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }
    
    setUser(null)
    router.push('/auth/login')
  }

  useEffect(() => {
    const initAuth = async () => {
      await refreshUser()
      setIsLoading(false)
    }
    
    initAuth()
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
