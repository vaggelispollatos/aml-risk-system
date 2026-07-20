import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import type { Customer } from '../types'

export default function Customers() {
  const { data: customers = [], isLoading } = useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: () => api.get('/customers?limit=100').then(r => r.data),
  })

  if (isLoading) return <div className="text-gray-400">Loading...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Customers</h1>
          <p className="text-gray-400 mt-1">{customers.length} total customers</p>
        </div>
      </div>

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
            {customers.map(c => (
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
        {customers.length === 0 && (
          <div className="text-center py-12 text-gray-500">No customers found</div>
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