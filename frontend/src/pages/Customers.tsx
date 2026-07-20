import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import type { Customer } from '../types'

export default function Customers() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', country: '', phone: '' })
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const { data: customers = [], isLoading } = useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: () => api.get('/customers?limit=100').then(r => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => api.post('/customers', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] })
      setShowForm(false)
      setForm({ name: '', email: '', country: '', phone: '' })
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create customer')
    },
  })

  const filtered = customers.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase()) ||
    c.country.toLowerCase().includes(search.toLowerCase())
  )

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-400">Loading customers...</div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Customers</h1>
          <p className="text-gray-400 mt-1">{filtered.length} of {customers.length} customers</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + Add Customer
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-gray-900 rounded-xl border border-gray-700 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">New Customer</h2>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-gray-400 text-sm block mb-1">Name *</label>
              <input
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Email *</label>
              <input
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Country Code *</label>
              <input
                value={form.country}
                onChange={e => setForm({ ...form, country: e.target.value.toUpperCase() })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="US"
                maxLength={2}
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Phone</label>
              <input
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="+1234567890"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => createMutation.mutate(form)}
              disabled={!form.name || !form.email || !form.country}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Customer'}
            </button>
            <button
              onClick={() => { setShowForm(false); setError('') }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Search */}
      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500"
        placeholder="Search by name, email or country..."
      />

      {/* Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-800 bg-gray-800/50">
              <th className="text-left px-6 py-4">Name</th>
              <th className="text-left px-6 py-4">Email</th>
              <th className="text-left px-6 py-4">Country</th>
              <th className="text-left px-6 py-4">KYC</th>
              <th className="text-left px-6 py-4">Risk Level</th>
              <th className="text-left px-6 py-4">Risk Score</th>
              <th className="text-left px-6 py-4">Transactions</th>
              <th className="text-left px-6 py-4">Volume</th>
              <th className="text-left px-6 py-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.id} className="border-b border-gray-800 hover:bg-gray-800/30 transition-colors">
                <td className="px-6 py-4">
                  <div className="font-medium text-white">{c.name}</div>
                  {c.is_sanctioned && (
                    <span className="text-xs text-red-400 font-medium">⚠ SANCTIONED</span>
                  )}
                </td>
                <td className="px-6 py-4 text-gray-400">{c.email}</td>
                <td className="px-6 py-4 text-gray-400">{c.country}</td>
                <td className="px-6 py-4"><KYCBadge status={c.kyc_status} /></td>
                <td className="px-6 py-4"><RiskBadge level={c.risk_level} /></td>
                <td className="px-6 py-4 text-gray-300">{c.risk_score.toFixed(1)}</td>
                <td className="px-6 py-4 text-gray-300">{c.total_transactions}</td>
                <td className="px-6 py-4 text-gray-300">${c.total_volume.toLocaleString()}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    c.is_active ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-400'
                  }`}>
                    {c.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {search ? 'No customers match your search' : 'No customers found'}
          </div>
        )}
      </div>
    </div>
  )
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    low: 'bg-blue-900 text-blue-300',
    medium: 'bg-yellow-900 text-yellow-300',
    high: 'bg-orange-900 text-orange-300',
    critical: 'bg-red-900 text-red-300',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[level] || 'bg-gray-700 text-gray-300'}`}>
      {level}
    </span>
  )
}

function KYCBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    approved: 'bg-green-900 text-green-300',
    pending: 'bg-yellow-900 text-yellow-300',
    rejected: 'bg-red-900 text-red-300',
    suspended: 'bg-gray-700 text-gray-400',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || 'bg-gray-700 text-gray-300'}`}>
      {status}
    </span>
  )
}