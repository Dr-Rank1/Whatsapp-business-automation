'use client'

import { useEffect, useState } from 'react'
import { analyticsApi, scheduledApi } from '@/lib/api'
import { useAuth } from '@/components/providers/AuthProvider'
import {
  Users,
  FileText,
  Send,
  Clock,
  TrendingUp,
  CheckCircle,
  XCircle,
} from 'lucide-react'

interface DashboardStats {
  total_contacts: number
  total_templates: number
  total_campaigns: number
  total_scheduled: number
  messages_sent_today: number
  messages_sent_this_month: number
  messages_delivered: number
  messages_failed: number
  success_rate: number
}

interface UpcomingMessage {
  id: number
  contact_name: string
  contact_phone: string
  message_content: string
  scheduled_at: string
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [upcoming, setUpcoming] = useState<UpcomingMessage[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, upcomingData] = await Promise.all([
          analyticsApi.dashboard(),
          scheduledApi.upcoming(),
        ])
        setStats(statsData)
        setUpcoming(upcomingData)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const statCards = [
    {
      name: 'Total Contacts',
      value: stats?.total_contacts || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      name: 'Templates',
      value: stats?.total_templates || 0,
      icon: FileText,
      color: 'bg-purple-500',
    },
    {
      name: 'Active Campaigns',
      value: stats?.total_campaigns || 0,
      icon: Send,
      color: 'bg-green-500',
    },
    {
      name: 'Scheduled Messages',
      value: stats?.total_scheduled || 0,
      icon: Clock,
      color: 'bg-orange-500',
    },
  ]

  const messageStats = [
    {
      name: 'Sent Today',
      value: stats?.messages_sent_today || 0,
      icon: Send,
      color: 'text-primary-600',
    },
    {
      name: 'This Month',
      value: stats?.messages_sent_this_month || 0,
      icon: TrendingUp,
      color: 'text-green-600',
    },
    {
      name: 'Delivered',
      value: stats?.messages_delivered || 0,
      icon: CheckCircle,
      color: 'text-emerald-600',
    },
    {
      name: 'Failed',
      value: stats?.messages_failed || 0,
      icon: XCircle,
      color: 'text-red-600',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name || user?.username}!
        </h1>
        <p className="text-gray-600">Here's what's happening with your WhatsApp automation.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Message Stats */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Message Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {messageStats.map((stat) => (
            <div key={stat.name} className="text-center">
              <stat.icon className={`w-8 h-8 mx-auto ${stat.color}`} />
              <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
              <p className="text-sm text-gray-600">{stat.name}</p>
            </div>
          ))}
        </div>
        
        {/* Success Rate */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Success Rate</span>
            <span className="text-sm font-bold text-green-600">
              {stats?.success_rate?.toFixed(1) || 0}%
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all"
              style={{ width: `${stats?.success_rate || 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Upcoming Messages */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Messages</h2>
        {upcoming.length > 0 ? (
          <div className="space-y-3">
            {upcoming.slice(0, 5).map((msg) => (
              <div
                key={msg.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{msg.contact_name || msg.contact_phone}</p>
                  <p className="text-sm text-gray-500 truncate max-w-xs">{msg.message_content}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">
                    {new Date(msg.scheduled_at).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(msg.scheduled_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No upcoming messages scheduled</p>
        )}
      </div>
    </div>
  )
}
