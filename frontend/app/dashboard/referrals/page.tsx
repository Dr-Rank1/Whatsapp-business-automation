'use client'

import { useEffect, useState } from 'react'
import { billingApi } from '@/lib/api'
import { Copy, Share2, Gift, Users, CheckCircle, Loader2 } from 'lucide-react'

interface Referral {
  id: number
  referral_code: string
  referred_email: string
  status: string
  created_at: string
  signed_up_at: string | null
  subscribed_at: string | null
}

export default function ReferralsPage() {
  const [referrals, setReferrals] = useState<Referral[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [referralCode, setReferralCode] = useState<string | null>(null)

  useEffect(() => {
    fetchReferrals()
  }, [])

  const fetchReferrals = async () => {
    try {
      const data = await billingApi.getReferrals()
      setReferrals(data.results || [])
      
      // Get first referral code if exists
      if (data.results && data.results.length > 0) {
        setReferralCode(data.results[0].referral_code)
      }
    } catch (err) {
      console.error('Failed to fetch referrals:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCode = async () => {
    setCreating(true)
    try {
      const data = await billingApi.createReferral()
      setReferralCode(data.referral_code)
      setReferrals([data, ...referrals])
    } catch (err) {
      console.error('Failed to create referral:', err)
    } finally {
      setCreating(false)
    }
  }

  const handleCopyCode = () => {
    if (referralCode) {
      navigator.clipboard.writeText(referralCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleShare = () => {
    if (referralCode && navigator.share) {
      navigator.share({
        title: 'Join WhatsApp Business Automation',
        text: `Use my referral code ${referralCode} to sign up for WhatsApp Business Automation and get started!`,
        url: `${window.location.origin}/auth/register?ref=${referralCode}`
      })
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      signed_up: 'bg-blue-100 text-blue-800',
      subscribed: 'bg-green-100 text-green-800',
      rewarded: 'bg-purple-100 text-purple-800',
      expired: 'bg-gray-100 text-gray-800'
    }
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status as keyof typeof styles] || styles.pending}`}>
        {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
      </span>
    )
  }

  const referralLink = referralCode 
    ? `${window.location.origin}/auth/register?ref=${referralCode}`
    : ''

  const stats = {
    total: referrals.length,
    signedUp: referrals.filter(r => r.status !== 'pending').length,
    subscribed: referrals.filter(r => r.status === 'subscribed' || r.status === 'rewarded').length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Referral Program</h1>
        <p className="text-gray-600 mt-1">Invite friends and earn rewards</p>
      </div>

      {/* Referral Banner */}
      <div className="card bg-gradient-to-r from-primary-600 to-primary-700 text-white">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white/20 rounded-lg">
            <Gift className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold">Earn Rewards</h2>
            <p className="text-primary-100">Get 1 month free for every friend who subscribes!</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-sm text-gray-500">Total Referrals</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.signedUp}</p>
              <p className="text-sm text-gray-500">Signed Up</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Gift className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.subscribed}</p>
              <p className="text-sm text-gray-500">Subscribed</p>
            </div>
          </div>
        </div>
      </div>

      {/* Referral Code */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Your Referral Code</h2>
        
        {!referralCode ? (
          <button
            onClick={handleCreateCode}
            disabled={creating}
            className="btn btn-primary"
          >
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Creating...
              </>
            ) : (
              'Generate Referral Code'
            )}
          </button>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={referralCode}
                readOnly
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 font-mono"
              />
              <button
                onClick={handleCopyCode}
                className="btn btn-secondary"
              >
                {copied ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={handleShare}
                className="btn btn-secondary"
              >
                <Share2 className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Share link:</strong> <span className="text-primary-600">{referralLink}</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Referral History */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Referral History</h2>
        
        {referrals.length > 0 ? (
          <div className="space-y-3">
            {referrals.map((referral) => (
              <div
                key={referral.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">
                    {referral.referred_email || 'Pending signup'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {new Date(referral.created_at).toLocaleDateString()}
                  </p>
                </div>
                {getStatusBadge(referral.status)}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">
            No referrals yet. Share your code to get started!
          </p>
        )}
      </div>

      {/* How it works */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">1</span>
            </div>
            <h3 className="font-medium mb-1">Share your code</h3>
            <p className="text-sm text-gray-600">Share your unique referral link with friends</p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">2</span>
            </div>
            <h3 className="font-medium mb-1">Friend signs up</h3>
            <p className="text-sm text-gray-600">They create an account using your code</p>
          </div>
          <div className="text-center p-4">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-primary-600 font-bold">3</span>
            </div>
            <h3 className="font-medium mb-1">Earn rewards</h3>
            <p className="text-sm text-gray-600">Get 1 month free when they subscribe</p>
          </div>
        </div>
      </div>
    </div>
  )
}
