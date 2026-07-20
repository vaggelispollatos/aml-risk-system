import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import type { Alert } from '../types'

export default function Alerts() {
  const queryClient = useQueryClient()

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: () => api.get('/alerts?limit=100').then(r => r.data),
  })

  const reviewMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/alerts/${id}`, { status, reviewed_by: 'compliance@company.com' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const open = alerts.filter(a => a.status === 'open').length
  const critical = alerts.filter(a => a.severity === 'critical').length

  if (isLoading) return <div className="text-gray-400">Loading...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <p className="text-gray-400 mt-1">{alerts.length} total — {open} open — {critical} critical</p>
      </div>

      <div className="space-y-3">
        {alerts.length === 0 && (
          <div className="text-center py-12 text-gray-500 bg-gray-900 rounded-xl border border-gray-800">
            No alerts found
          </div>
        )}
        {alerts.map(a => (
          <div key={a.id} className={`bg-gray-900 rounded-xl border p-5 ${
            a.severity === 'critical' ? 'border-red-800' :
            a.severity === 'high' ? 'border-orange-800' :
            'border-gray-800'
          }`}>
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={a.severity} />
                  <StatusBadge status={a.status} />
                  <span className="text-gray-400 text-xs font-mono">{a.id.slice(0, 8)}...</span>
                </div>
                <p className="text-white font-medium">
                  {a.rule_triggered.replace(/_/g, ' ').toUpperCase()}
                </p>
                <p className="text-gray-400 text-sm">{a.reason}</p>
                <p className="text-gray-500 text-xs">
                  {new Date(a.created_at).toLocaleString()}
                  {a.reviewed_by && ` · Reviewed by ${a.reviewed_by}`}
                </p>
              </div>

              {a.status === 'open' && (
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => reviewMutation.mutate({ id: a.id, status: 'resolved' })}
                    className="px-3 py-1.5 bg-green-800 hover:bg-green-700 text-green-200 rounded text-xs font-medium transition-colors"
                  >
                    Resolve
                  </button>
                  <button
                    onClick={() => reviewMutation.mutate({ id: a.id, status: 'false_positive' })}
                    className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs font-medium transition-colors"
                  >
                    False Positive
                  </button>
                  <button
                    onClick={() => reviewMutation.mutate({ id: a.id, status: 'escalated' })}
                    className="px-3 py-1.5 bg-red-900 hover:bg-red-800 text-red-200 rounded text-xs font-medium transition-colors"
                  >
                    Escalate
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
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

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    open: 'bg-yellow-900 text-yellow-300',
    in_review: 'bg-blue-900 text-blue-300',
    resolved: 'bg-green-900 text-green-300',
    false_positive: 'bg-gray-700 text-gray-400',
    escalated: 'bg-red-900 text-red-300',
  }
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || 'bg-gray-700 text-gray-300'}`}>
      {status.replace('_', ' ')}
    </span>
  )
}