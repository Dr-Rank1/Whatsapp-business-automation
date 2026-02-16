'use client'

import Link from 'next/link'
import { useState } from 'react'
import { 
  MessageCircle, 
  Zap, 
  Users, 
  BarChart3, 
  Shield,
  ArrowRight,
  Check,
  Star,
  Clock,
  CreditCard,
  ChevronRight
} from 'lucide-react'

export default function LandingPage() {
  const [showPricing, setShowPricing] = useState(false)

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gray-900">WhatsApp Kenya</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900">Pricing</a>
              <a href="#templates" className="text-gray-600 hover:text-gray-900">Templates</a>
              <Link href="/auth/login" className="text-gray-600 hover:text-gray-900">Login</Link>
              <Link href="/auth/register" className="btn-primary">
                Start Free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-green-50 to-emerald-100 py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Automate Your WhatsApp
              <span className="text-green-600"> Business in Kenya</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Save hours every day. Respond instantly. Never lose a lead. 
              The WhatsApp automation built for Kenyan SMEs.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/register" className="btn-primary text-lg px-8 py-4 inline-flex items-center justify-center gap-2">
                Start Free Trial <ArrowRight className="w-5 h-5" />
              </Link>
              <button className="btn-secondary text-lg px-8 py-4 inline-flex items-center justify-center gap-2">
                Watch Demo
              </button>
            </div>
            <p className="mt-4 text-sm text-gray-500 flex items-center justify-center gap-2">
              <Check className="w-4 h-4 text-green-500" /> No credit card required
              <Check className="w-4 h-4 text-green-500" /> 7-day free trial
              <Check className="w-4 h-4 text-green-500" /> Cancel anytime
            </p>
          </div>

          {/* Social Proof */}
          <div className="mt-16 text-center">
            <p className="text-sm text-gray-500 mb-4">Trusted by 500+ Kenyan businesses</p>
            <div className="flex justify-center gap-8 opacity-50">
              {/* Logo placeholders */}
              <div className="h-8 w-24 bg-gray-300 rounded"></div>
              <div className="h-8 w-24 bg-gray-300 rounded"></div>
              <div className="h-8 w-24 bg-gray-300 rounded"></div>
              <div className="h-8 w-24 bg-gray-300 rounded"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Pain Points */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Stop Losing Customers to Slow Responses
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Kenyan businesses lose KES 100,000s every month to slow WhatsApp responses. 
              Here's how we solve that.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Clock,
                title: "Too Many Messages?",
                description: "Get 100s of messages daily and can't keep up. Automation handles them all instantly."
              },
              {
                icon: MessageCircle,
                title: "Losing Leads?",
                description: "Respond in seconds, not hours. Auto-replies catch every inquiry immediately."
              },
              {
                icon: BarChart3,
                title: "No Analytics?",
                description: "Know exactly what's working. Track messages, leads, and conversions."
              }
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-8 rounded-2xl shadow-sm">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                  <item.icon className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything You Need to Scale
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Powerful features designed for Kenyan businesses
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: 'Auto-Replies',
                description: 'Instant responses 24/7. Never miss a customer again.'
              },
              {
                icon: Users,
                title: 'Contact Management',
                description: 'Tag, categorize, and track every customer conversation.'
              },
              {
                icon: MessageCircle,
                title: 'Broadcast Messages',
                description: 'Send to thousands at once. Perfect for updates & promotions.'
              },
              {
                icon: Clock,
                title: 'Scheduled Messages',
                description: 'Plan messages for later. Birthdays, follow-ups, everything.'
              },
              {
                icon: BarChart3,
                title: 'Analytics',
                description: 'Know your numbers. Messages sent, delivered, responses.'
              },
              {
                icon: Shield,
                title: 'WhatsApp Safe',
                description: 'Built-in rate limits to keep your account safe.'
              }
            ].map((feature, idx) => (
              <div key={idx} className="flex gap-4">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <feature.icon className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">{feature.title}</h3>
                  <p className="text-sm text-gray-600">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Templates */}
      <section id="templates" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Pre-Built Templates for Kenyan Business
            </h2>
            <p className="text-gray-600">
              Just fill in your details and send. No more typing from scratch.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                title: 'Order Confirmation',
                description: 'Confirm orders with Jumia-style details',
                color: 'bg-blue-50'
              },
              {
                title: 'M-Pesa Payment Request',
                description: 'Send payment instructions instantly',
                color: 'bg-green-50'
              },
              {
                title: 'Delivery Updates',
                description: 'Track and notify about deliveries',
                color: 'bg-purple-50'
              },
              {
                title: 'Real Estate Inquiry',
                description: 'Property details and viewing scheduling',
                color: 'bg-yellow-50'
              },
              {
                title: 'Car Sales Follow-up',
                description: 'Vehicle details and negotiation',
                color: 'bg-red-50'
              },
              {
                title: 'Booking Confirmation',
                description: 'Event and appointment confirmations',
                color: 'bg-indigo-50'
              }
            ].map((template, idx) => (
              <div key={idx} className={`${template.color} p-6 rounded-xl`}>
                <h3 className="font-semibold text-gray-900 mb-2">{template.title}</h3>
                <p className="text-sm text-gray-600">{template.description}</p>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <button className="btn-primary inline-flex items-center gap-2">
              View All Templates <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Simple, Affordable Pricing
            </h2>
            <p className="text-gray-600">
              No hidden fees. Pay via M-Pesa or card.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {/* Free */}
            <div className="border rounded-2xl p-6">
              <h3 className="text-lg font-semibold">Free</h3>
              <p className="text-3xl font-bold mt-2">KES 0</p>
              <p className="text-gray-500 text-sm">forever</p>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 100 messages/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 50 contacts
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 5 templates
                </li>
              </ul>
              <Link href="/auth/register" className="btn-secondary w-full mt-6 block text-center">
                Get Started
              </Link>
            </div>

            {/* Starter */}
            <div className="border-2 border-green-500 rounded-2xl p-6 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-500 text-white text-sm rounded-full">
                Popular
              </div>
              <h3 className="text-lg font-semibold">Starter</h3>
              <p className="text-3xl font-bold mt-2">KES 1,499</p>
              <p className="text-gray-500 text-sm">per month</p>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 2,000 messages/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 500 contacts
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> Bulk sending
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> Scheduling
                </li>
              </ul>
              <Link href="/auth/register?plan=starter" className="btn-primary w-full mt-6 block text-center">
                Start Free Trial
              </Link>
            </div>

            {/* Pro */}
            <div className="border rounded-2xl p-6">
              <h3 className="text-lg font-semibold">Pro</h3>
              <p className="text-3xl font-bold mt-2">KES 3,999</p>
              <p className="text-gray-500 text-sm">per month</p>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 10,000 messages/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 2,000 contacts
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> CRM features
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> Team accounts
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> Analytics
                </li>
              </ul>
              <Link href="/auth/register?plan=pro" className="btn-secondary w-full mt-6 block text-center">
                Start Free Trial
              </Link>
            </div>

            {/* Agency */}
            <div className="border rounded-2xl p-6">
              <h3 className="text-lg font-semibold">Agency</h3>
              <p className="text-3xl font-bold mt-2">KES 9,999</p>
              <p className="text-gray-500 text-sm">per month</p>
              <ul className="mt-6 space-y-3">
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 50,000 messages/month
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> 25 team members
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> White-label
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> API access
                </li>
                <li className="flex items-center gap-2 text-sm">
                  <Check className="w-4 h-4 text-green-500" /> Priority support
                </li>
              </ul>
              <Link href="/auth/register?plan=agency" className="btn-secondary w-full mt-6 block text-center">
                Contact Sales
              </Link>
            </div>
          </div>

          {/* Payment Methods */}
          <div className="mt-12 text-center">
            <p className="text-gray-500 mb-4">Accepted payment methods</p>
            <div className="flex justify-center gap-4">
              <div className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium">M-Pesa</div>
              <div className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium">Visa</div>
              <div className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium">Mastercard</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-green-600 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Automate Your WhatsApp?
          </h2>
          <p className="text-green-100 mb-8 text-lg">
            Join 500+ Kenyan businesses saving hours every day.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register" className="bg-white text-green-600 px-8 py-4 rounded-lg font-semibold inline-flex items-center justify-center gap-2">
              Start Free 7-Day Trial <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold inline-flex items-center justify-center gap-2">
              Talk to Sales
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-white text-xl">WhatsApp Kenya</span>
              </div>
              <p className="text-sm">
                The WhatsApp automation platform built for Kenyan SMEs.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white">Features</a></li>
                <li><a href="#pricing" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Templates</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
            © 2024 WhatsApp Kenya. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
