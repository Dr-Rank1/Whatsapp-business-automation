'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/components/providers/AuthProvider'
import {
  LayoutDashboard,
  Users,
  FileText,
  Send,
  Clock,
  Settings,
  BarChart3,
  LogOut,
  MessageSquare,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Contacts', href: '/dashboard/contacts', icon: Users },
  { name: 'Templates', href: '/dashboard/templates', icon: FileText },
  { name: 'Campaigns', href: '/dashboard/campaigns', icon: Send },
  { name: 'Scheduled', href: '/dashboard/scheduled', icon: Clock },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading, logout } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 fixed h-full">
          <div className="p-6">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-8 h-8 text-primary-600" />
              <span className="font-bold text-lg">WA Automate</span>
            </div>
          </div>
          
          <nav className="px-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
          
          <div className="absolute bottom-0 w-64 p-4 border-t border-gray-200">
            <button
              onClick={logout}
              className="flex items-center gap-3 px-3 py-2 w-full text-left text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition-colors"
            >
              <LogOut className="w-5 h-5" />
              Sign out
            </button>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 ml-64">
          <main className="p-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
