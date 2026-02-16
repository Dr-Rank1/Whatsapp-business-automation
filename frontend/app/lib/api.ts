import axios from 'axios'
import Cookies from 'js-cookie'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = Cookies.get('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refreshToken = Cookies.get('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/token/refresh/custom/`, {
            refresh: refreshToken,
          })
          
          const { access, refresh } = response.data
          Cookies.set('access_token', access)
          Cookies.set('refresh_token', refresh)
          
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        Cookies.remove('access_token')
        Cookies.remove('refresh_token')
        window.location.href = '/auth/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/login/', { username, password })
    return response.data
  },
  
  register: async (data: RegisterData) => {
    const response = await api.post('/auth/register/', data)
    return response.data
  },
  
  logout: async () => {
    const refresh = Cookies.get('refresh_token')
    if (refresh) {
      await api.post('/auth/logout/', { refresh })
    }
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
  },
  
  getUser: async () => {
    const response = await api.get('/auth/me/')
    return response.data
  },
  
  changePassword: async (oldPassword: string, newPassword: string) => {
    const response = await api.post('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: newPassword,
    })
    return response.data
  },
  
  getStats: async () => {
    const response = await api.get('/auth/stats/')
    return response.data
  },
}

// Contacts API
export const contactsApi = {
  list: async (params?: any) => {
    const response = await api.get('/contacts/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/contacts/${id}/`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await api.post('/contacts/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await api.patch(`/contacts/${id}/`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/contacts/${id}/`)
    return response.data
  },
  
  block: async (id: number) => {
    const response = await api.post(`/contacts/${id}/block/`)
    return response.data
  },
  
  unblock: async (id: number) => {
    const response = await api.post(`/contacts/${id}/unblock/`)
    return response.data
  },
}

// Templates API
export const templatesApi = {
  list: async (params?: any) => {
    const response = await api.get('/templates/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/templates/${id}/`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await api.post('/templates/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await api.patch(`/templates/${id}/`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/templates/${id}/`)
    return response.data
  },
  
  categories: async () => {
    const response = await api.get('/templates/categories/')
    return response.data
  },
}

// Campaigns API
export const campaignsApi = {
  list: async (params?: any) => {
    const response = await api.get('/campaigns/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/campaigns/${id}/`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await api.post('/campaigns/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await api.patch(`/campaigns/${id}/`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/campaigns/${id}/`)
    return response.data
  },
  
  start: async (id: number) => {
    const response = await api.post(`/campaigns/${id}/start/`)
    return response.data
  },
  
  pause: async (id: number) => {
    const response = await api.post(`/campaigns/${id}/pause/`)
    return response.data
  },
  
  cancel: async (id: number) => {
    const response = await api.post(`/campaigns/${id}/cancel/`)
    return response.data
  },
  
  stats: async () => {
    const response = await api.get('/campaigns/stats/')
    return response.data
  },
}

// Scheduled Messages API
export const scheduledApi = {
  list: async (params?: any) => {
    const response = await api.get('/scheduled/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/scheduled/${id}/`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await api.post('/scheduled/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await api.patch(`/scheduled/${id}/`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/scheduled/${id}/`)
    return response.data
  },
  
  cancel: async (id: number) => {
    const response = await api.post(`/scheduled/${id}/cancel/`)
    return response.data
  },
  
  upcoming: async () => {
    const response = await api.get('/scheduled/upcoming/')
    return response.data
  },
}

// Messages API
export const messagesApi = {
  list: async (params?: any) => {
    const response = await api.get('/messages/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await api.get(`/messages/${id}/`)
    return response.data
  },
  
  failed: async () => {
    const response = await api.get('/messages/failed/')
    return response.data
  },
  
  retry: async (id: number) => {
    const response = await api.post(`/messages/${id}/retry/`)
    return response.data
  },
}

// Analytics API
export const analyticsApi = {
  dashboard: async () => {
    const response = await api.get('/analytics/dashboard/')
    return response.data
  },
  
  chart: async (days: number = 30) => {
    const response = await api.get('/analytics/chart/', { params: { days } })
    return response.data
  },
  
  list: async (params?: any) => {
    const response = await api.get('/analytics/', { params })
    return response.data
  },
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
  phone?: string
}

// Billing API
export const billingApi = {
  getPlans: async () => {
    const response = await api.get('/billing/plans/')
    return response.data
  },
  
  getSubscription: async () => {
    const response = await api.get('/billing/subscription/')
    return response.data
  },
  
  createCheckout: async (planId: number, billingInterval: string = 'monthly', coupon?: string) => {
    const response = await api.post('/billing/checkout/', {
      plan_id: planId,
      billing_interval: billingInterval,
      coupon
    })
    return response.data
  },
  
  createPortalSession: async () => {
    const response = await api.post('/billing/portal/')
    return response.data
  },
  
  cancelSubscription: async () => {
    const response = await api.post('/billing/cancel/')
    return response.data
  },
  
  changePlan: async (planId: number) => {
    const response = await api.post('/billing/change-plan/', {
      plan_id: planId
    })
    return response.data
  },
  
  getUsage: async () => {
    const response = await api.get('/billing/usage/')
    return response.data
  },
  
  getCurrentUsage: async () => {
    const response = await api.get('/billing/usage/current/')
    return response.data
  },
  
  getBillingHistory: async (params?: any) => {
    const response = await api.get('/billing/history/', { params })
    return response.data
  },
  
  applyCoupon: async (code: string) => {
    const response = await api.post('/billing/coupon/', { code })
    return response.data
  },
  
  getStats: async () => {
    const response = await api.get('/billing/stats/')
    return response.data
  },
  
  getReferrals: async () => {
    const response = await api.get('/billing/referrals/')
    return response.data
  },
  
  createReferral: async () => {
    const response = await api.post('/billing/referrals/')
    return response.data
  },
}

// Notifications API
export const notificationsApi = {
  list: async (params?: any) => {
    const response = await api.get('/notifications/', { params })
    return response.data
  },
  
  markAsRead: async (id: number) => {
    const response = await api.post(`/notifications/${id}/read/`)
    return response.data
  },
  
  markAllAsRead: async () => {
    const response = await api.post('/notifications/mark-all-read/')
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await api.delete(`/notifications/${id}/`)
    return response.data
  },
}

// Team API
export const teamApi = {
  getMembers: async () => {
    const response = await api.get('/team/members/')
    return response.data
  },
  
  inviteMember: async (email: string, role: string) => {
    const response = await api.post('/team/invite/', { email, role })
    return response.data
  },
  
  updateMember: async (memberId: number, role: string) => {
    const response = await api.patch(`/team/members/${memberId}/`, { role })
    return response.data
  },
  
  removeMember: async (memberId: number) => {
    const response = await api.delete(`/team/members/${memberId}/`)
    return response.data
  },
}
