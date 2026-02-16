'use client'

import { useEffect, useState } from 'react'
import { billingApi } from '@/lib/api'
import { useAuth } from '@/components/providers/AuthProvider'
import { Check, X, Crown, Zap, Star, Loader2 } from 'lucide-react'

interface Plan {
  id: number
  name: string
  tier: string
  description: string
  price_monthly: string
  price_yearly: string
  monthly_message_limit: number
  max_contacts: number
  max_campaigns: number
  allow_scheduling: boolean
  allow_analytics: boolean
  allow_bulk_sending: boolean
  priority_support: boolean
  is_popular: boolean
}

interface SubscriptionStats {
  subscription: {
    status: string
    plan_name: string
    plan_tier: string
    current_period_end: string
    is_trialing: boolean
  }
  usage: {
    messages_sent: number
    message_limit: number
    messages_remaining: number
    usage_percentage: number
    contact_count: number
    max_contacts: number
  }
  features: {
    allow_scheduling: boolean
    allow_analytics: boolean
    allow_bulk_sending: boolean
    priority_support: boolean
  }
  alerts: Array<{
    type: string
    message: string
  }>
}

export default function SubscriptionPage() {
  const { user } = useAuth()
  const [plans, setPlans] = useState<Plan[]>([])
  const [stats, setStats] = useState<SubscriptionStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly')
  const [upgrading, setUpgrading] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [plansData, statsData] = await Promise.all([
        billingApi.getPlans(),
        billingApi.getStats()
      ])
      setPlans(plansData)
      setStats(statsData)
    } catch (err) {
      console.error('Failed to fetch data:', err)
      setError('Failed to load subscription data')
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = async (planId: number) => {
    setUpgrading(planId)
    setError(null)

    try {
      const { checkout_url } = await billingApi.createCheckout(planId, billingInterval)
      window.location.href = checkout_url
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create checkout session')
      setUpgrading(null)
    }
  }

  const handleManageBilling = async () => {
    try {
      const { portal_url } = await billingApi.createPortalSession()
      window.location.href = portal_url
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to open billing portal')
    }
  }

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'enterprise': return <Crown className="w-5 h-5" />
      case 'pro': return <Star className="w-5 h-5" />
      case 'starter': return <Zap className="w-5 h-5" />
      default: return null
    }
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'enterprise': return 'bg-purple-600'
      case 'pro': return 'bg-blue-600'
      case 'starter': return 'bg-green-600'
      default: return 'bg-gray-600'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  const currentTier = stats?.subscription?.plan_tier || 'free'

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Subscription Plans</h1>
        <p className="text-gray-600 mt-1">Choose the plan that fits your needs</p>
      </div>

      {/* Current Plan */}
      {stats && (
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Current Plan</h2>
              <p className="text-gray-600">
                {stats.subscription.plan_name} - {stats.subscription.status}
              </p>
              {stats.subscription.is_trialing && (
                <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded">
                  Trial ends {new Date(stats.subscription.current_period_end).toLocaleDateString()}
                </span>
              )}
            </div>
            <button
              onClick={handleManageBilling}
              className="btn btn-secondary"
            >
              Manage Billing
            </button>
          </div>

          {/* Usage Progress */}
          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Messages this month</span>
              <span className="font-medium">
                {stats.usage.messages_sent} / {stats.usage.message_limit}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  stats.usage.usage_percentage >= 90 ? 'bg-red-500' :
                  stats.usage.usage_percentage >= 75 ? 'bg-yellow-500' :
                  'bg-green-500'
                }`}
                style={{ width: `${Math.min(stats.usage.usage_percentage, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {stats.usage.messages_remaining} messages remaining
            </p>
          </div>

          {/* Alerts */}
          {stats.alerts && stats.alerts.length > 0 && (
            <div className="mt-4 space-y-2">
              {stats.alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg text-sm ${
                    alert.type === 'danger' ? 'bg-red-50 text-red-700' :
                    'bg-yellow-50 text-yellow-700'
                  }`}
                >
                  {alert.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Billing Interval Toggle */}
      <div className="flex justify-center">
        <div className="bg-gray-100 p-1 rounded-lg flex">
          <button
            onClick={() => setBillingInterval('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingInterval === 'monthly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingInterval('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              billingInterval === 'yearly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Yearly
            <span className="ml-2 text-green-600 text-xs">Save 20%</span>
          </button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const isCurrentPlan = plan.tier === currentTier
          const price = billingInterval === 'monthly' ? plan.price_monthly : plan.price_yearly

          return (
            <div
              key={plan.id}
              className={`card relative ${
                plan.is_popular ? 'ring-2 ring-primary-500' : ''
              } ${isCurrentPlan ? 'bg-primary-50 border-primary-200' : ''}`}
            >
              {plan.is_popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary-600 text-white text-xs font-medium rounded-full">
                  Most Popular
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${getTierColor(plan.tier)} text-white`}>
                  {getTierIcon(plan.tier)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                  <p className="text-sm text-gray-500">
                    {plan.tier.charAt(0).toUpperCase() + plan.tier.slice(1)}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <span className="text-3xl font-bold text-gray-900">${price}</span>
                <span className="text-gray-500">/{billingInterval === 'monthly' ? 'mo' : 'yr'}</span>
              </div>

              <p className="text-sm text-gray-600 mb-4">{plan.description}</p>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>{plan.monthly_message_limit.toLocaleString()} messages/month</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>{plan.max_contacts} contacts</span>
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>{plan.max_campaigns} campaigns</span>
                </li>
                {plan.allow_scheduling && (
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-500" />
                    <span>Scheduled Messages</span>
                  </li>
                )}
                {plan.allow_analytics && (
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-500" />
                    <span>Advanced Analytics</span>
                  </li>
                )}
                {plan.allow_bulk_sending && (
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-500" />
                    <span>Bulk Sending</span>
                  </li>
                )}
                {plan.priority_support && (
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-500" />
                    <span>Priority Support</span>
                  </li>
                )}
              </ul>

              {isCurrentPlan ? (
                <button disabled className="btn bg-gray-200 text-gray-600 cursor-not-allowed">
                  Current Plan
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={upgrading === plan.id}
                  className={`btn ${plan.tier === 'enterprise' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  {upgrading === plan.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Upgrade'
                  )}
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Error Message */}
      {error && (
        <div className="fixed bottom-4 right-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 max-w-md">
          {error}
        </div>
      )}
    </div>
  )
}
