import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import type { Transaction } from '../types'

export default function Transactions() {
  const { data: transactions = [], isLoading } = useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: () => api.get('/transactions?limit=100').then(r => r.data),
  })

  const flagged = transactions.filter(t => t.flagged).length
  const blocked = transactions.filter(t => t.status === 'blocked').length

  if (isLoading) return <div className="text-gray-400">Loading...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-gray-400 mt-1">{transactions.length} total — {flagged} flagged — {blocked} blocked</p>
        </div>
      </div>

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
            {transactions.map(t => (
              <tr key={t.id} className={`border-b border-gray-800 hover:bg-gray-800/30 transition-colors ${
                t.flagged ? 'bg-orange-950/20' : ''
              } ${t.status === 'blocked' ? 'bg-red-950/20' : ''}`}>
                <td className="px-6 py-4 text-gray-500 font-mono text-xs">{t.id.slice(0, 8)}...</td>
                <td className="px-6 py-4">
                  <span className="text-white font-medium uppercase">{t.type}</span>
                </td>
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
        {transactions.length === 0 && (
          <div className="text-center py-12 text-gray-500">No transactions found</div>
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