import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import type { Transaction, Customer } from '../types'

export default function Transactions() {
  const [statusFilter, setStatusFilter] = useState('')
  const [flaggedOnly, setFlaggedOnly] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    customer_id: '',
    type: 'transfer',
    amount: '',
    currency: 'USD',
    source_country: '',
    destination_country: '',
  })
  const queryClient = useQueryClient()

  const { data: transactions = [], isLoading } = useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: () => api.get('/transactions?limit=100').then(r => r.data),
  })

  const { data: customers = [] } = useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: () => api.get('/customers?limit=100').then(r => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/transactions', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setShowForm(false)
      setForm({ customer_id: '', type: 'transfer', amount: '', currency: 'USD', source_country: '', destination_country: '' })
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create transaction')
    },
  })

  const filtered = transactions.filter(t => {
    if (flaggedOnly && !t.flagged) return false
    if (statusFilter && t.status !== statusFilter) return false
    return true
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-400">Loading transactions...</div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-gray-400 mt-1">
            {filtered.length} of {transactions.length} transactions
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + New Transaction
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="bg-gray-900 rounded-xl border border-gray-700 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white">New Transaction</h2>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-gray-400 text-sm block mb-1">Customer *</label>
              <select
                value={form.customer_id}
                onChange={e => setForm({ ...form, customer_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="">Select customer...</option>
                {customers.map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.email})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Type *</label>
              <select
                value={form.type}
                onChange={e => setForm({ ...form, type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="transfer">Transfer</option>
                <option value="deposit">Deposit</option>
                <option value="withdrawal">Withdrawal</option>
              </select>
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Amount *</label>
              <input
                type="number"
                value={form.amount}
                onChange={e => setForm({ ...form, amount: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="10000"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Currency</label>
              <select
                value={form.currency}
                onChange={e => setForm({ ...form, currency: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="JPY">JPY</option>
              </select>
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Source Country</label>
              <input
                value={form.source_country}
                onChange={e => setForm({ ...form, source_country: e.target.value.toUpperCase() })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="US"
                maxLength={2}
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Destination Country</label>
              <input
                value={form.destination_country}
                onChange={e => setForm({ ...form, destination_country: e.target.value.toUpperCase() })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="CN"
                maxLength={2}
              />
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => createMutation.mutate({
                ...form,
                amount: parseFloat(form.amount),
              })}
              disabled={!form.customer_id || !form.amount}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              {createMutation.isPending ? 'Processing...' : 'Submit Transaction'}
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

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="flagged">Flagged</option>
          <option value="blocked">Blocked</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <button
          onClick={() => setFlaggedOnly(!flaggedOnly)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
            flaggedOnly
              ? 'bg-orange-900 border-orange-700 text-orange-300'
              : 'bg-gray-900 border-gray-700 text-gray-400 hover:text-white'
          }`}
        >
          ⚠ Flagged Only
        </button>
      </div>

      {/* Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-800 bg-gray-800/50">
              <th className="text-left px-6 py-4">ID</th>
              <th className="text-left px-6 py-4">Type</th>
              <th className="text-left px-6 py-4">Amount</th>
              <th className="text-left px-6 py-4">Route</th>
              <th className="text-left px-6 py-4">Risk Score</th>
              <th className="text-left px-6 py-4">Risk Level</th>
              <th className="text-left px-6 py-4">Status</th>
              <th className="text-left px-6 py-4">Date</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(t => (
              <tr key={t.id} className={`border-b border-gray-800 hover:bg-gray-800/30 transition-colors ${
                t.status === 'blocked' ? 'bg-red-950/20' :
                t.flagged ? 'bg-orange-950/20' : ''
              }`}>
                <td className="px-6 py-4 text-gray-500 font-mono text-xs">{t.id.slice(0, 8)}...</td>
                <td className="px-6 py-4 text-white font-medium uppercase">{t.type}</td>
                <td className="px-6 py-4 text-gray-300">
                  {t.currency} {t.amount.toLocaleString()}
                </td>
                <td className="px-6 py-4 text-gray-400">
                  {t.source_country && t.destination_country
                    ? `${t.source_country} → ${t.destination_country}`
                    : t.source_country || '—'}
                </td>
                <td className="px-6 py-4">
                  <span className={`font-medium ${
                    t.risk_score > 75 ? 'text-red-400' :
                    t.risk_score > 50 ? 'text-orange-400' :
                    t.risk_score > 25 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {t.risk_score.toFixed(1)}
                  </span>
                </td>
                <td className="px-6 py-4"><RiskBadge level={t.risk_level || 'low'} /></td>
                <td className="px-6 py-4"><StatusBadge status={t.status} /></td>
                <td className="px-6 py-4 text-gray-500 text-xs">
                  {new Date(t.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {statusFilter || flaggedOnly ? 'No transactions match your filters' : 'No transactions found'}
          </div>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'bg-green-900 text-green-300',
    flagged: 'bg-orange-900 text-orange-300',
    blocked: 'bg-red-900 text-red-300',
    pending: 'bg-gray-700 text-gray-300',
    failed: 'bg-gray-700 text-gray-400',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || 'bg-gray-700 text-gray-300'}`}>
      {status}
    </span>
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