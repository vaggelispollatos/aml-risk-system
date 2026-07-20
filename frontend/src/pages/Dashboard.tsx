import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import type { Customer, Transaction, Alert } from '../types'

export default function Dashboard() {
  const { data: customers = [] } = useQuery<Customer[]>({
    queryKey: ['customers'],
    queryFn: () => api.get('/customers').then(r => r.data),
  })

  const { data: transactions = [] } = useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: () => api.get('/transactions').then(r => r.data),
  })

  const { data: alerts = [] } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: () => api.get('/alerts').then(r => r.data),
  })

  const flagged = transactions.filter(t => t.flagged).length
  const openAlerts = alerts.filter(a => a.status === 'open').length
  const highRisk = customers.filter(c => c.risk_level === 'high' || c.risk_level === 'critical').length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">AML Risk Monitoring Overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Total Customers" value={customers.length} color="blue" />
        <StatCard label="High Risk Customers" value={highRisk} color="orange" />
        <StatCard label="Flagged Transactions" value={flagged} color="red" />
        <StatCard label="Open Alerts" value={openAlerts} color="yellow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Transactions</h2>
          {transactions.length === 0 ? (
            <p className="text-gray-500 text-sm">No transactions yet</p>
          ) : (
            <div className="space-y-3">
              {transactions.slice(0, 5).map(t => (
                <div key={t.id} className="flex items-center justify-between py-2 border-b border-gray-800">
                  <div>
                    <p className="text-sm text-white font-medium">{t.type.toUpperCase()}</p>
                    <p className="text-xs text-gray-400">{t.currency} {t.amount.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <StatusBadge status={t.status} />
                    <p className="text-xs text-gray-500 mt-1">Score: {t.risk_score.toFixed(1)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Alerts</h2>
          {alerts.length === 0 ? (
            <p className="text-gray-500 text-sm">No alerts yet</p>
          ) : (
            <div className="space-y-3">
              {alerts.slice(0, 5).map(a => (
                <div key={a.id} className="flex items-center justify-between py-2 border-b border-gray-800">
                  <div>
                    <p className="text-sm text-white font-medium">{a.rule_triggered.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-gray-400 truncate max-w-48">{a.reason}</p>
                  </div>
                  <SeverityBadge severity={a.severity} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Customers</h2>
        {customers.length === 0 ? (
          <p className="text-gray-500 text-sm">No customers yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-800">
                <th className="text-left pb-3">Name</th>
                <th className="text-left pb-3">Email</th>
                <th className="text-left pb-3">Country</th>
                <th className="text-left pb-3">KYC</th>
                <th className="text-left pb-3">Risk</th>
                <th className="text-left pb-3">Transactions</th>
              </tr>
            </thead>
            <tbody>
              {customers.map(c => (
                <tr key={c.id} className="border-b border-gray-800 hover:bg-gray-800">
                  <td className="py-3 text-white">{c.name}</td>
                  <td className="py-3 text-gray-400">{c.email}</td>
                  <td className="py-3 text-gray-400">{c.country}</td>
                  <td className="py-3"><KYCBadge status={c.kyc_status} /></td>
                  <td className="py-3"><RiskBadge level={c.risk_level} /></td>
                  <td className="py-3 text-gray-400">{c.total_transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: 'text-blue-400',
    orange: 'text-orange-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
  }
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className={`text-3xl font-bold mt-2 ${colors[color]}`}>{value}</p>
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

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    low: 'bg-blue-900 text-blue-300',
    medium: 'bg-yellow-900 text-yellow-300',
    high: 'bg-orange-900 text-orange-300',
    critical: 'bg-red-900 text-red-300',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[severity] || 'bg-gray-700 text-gray-300'}`}>
      {severity}
    </span>
  )
}

function RiskBadge({ level }: { level: string }) {
  return <SeverityBadge severity={level} />
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