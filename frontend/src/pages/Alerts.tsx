import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import type { Alert, ComplianceAssessment } from '../types'

export default function Alerts() {
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [assessments, setAssessments] = useState<Record<string, ComplianceAssessment>>({})
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

  const assessMutation = useMutation({
    mutationFn: (alertId: string) =>
      api.post<ComplianceAssessment>(`/compliance/alerts/${alertId}/assess`).then(r => r.data),
    onSuccess: assessment =>
      setAssessments(prev => ({ ...prev, [assessment.alert_id]: assessment })),
  })

  const filtered = alerts.filter(a => {
    if (severityFilter && a.severity !== severityFilter) return false
    if (statusFilter && a.status !== statusFilter) return false
    return true
  })

  const open = alerts.filter(a => a.status === 'open').length
  const critical = alerts.filter(a => a.severity === 'critical').length

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-gray-400">Loading alerts...</div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <p className="text-gray-400 mt-1">
          {filtered.length} of {alerts.length} alerts — {open} open — {critical} critical
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Open', value: alerts.filter(a => a.status === 'open').length, color: 'text-yellow-400' },
          { label: 'Critical', value: alerts.filter(a => a.severity === 'critical').length, color: 'text-red-400' },
          { label: 'Resolved', value: alerts.filter(a => a.status === 'resolved').length, color: 'text-green-400' },
          { label: 'Escalated', value: alerts.filter(a => a.status === 'escalated').length, color: 'text-orange-400' },
        ].map(s => (
          <div key={s.label} className="bg-gray-900 rounded-xl border border-gray-800 p-4">
            <p className="text-gray-400 text-sm">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={severityFilter}
          onChange={e => setSeverityFilter(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_review">In Review</option>
          <option value="escalated">Escalated</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>
        {(severityFilter || statusFilter) && (
          <button
            onClick={() => { setSeverityFilter(''); setStatusFilter('') }}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filtered.length === 0 && (
          <div className="text-center py-12 text-gray-500 bg-gray-900 rounded-xl border border-gray-800">
            {severityFilter || statusFilter ? 'No alerts match your filters' : 'No alerts found'}
          </div>
        )}
        {filtered.map(a => (
          <div key={a.id} className={`bg-gray-900 rounded-xl border p-5 ${
            a.severity === 'critical' ? 'border-red-800' :
            a.severity === 'high' ? 'border-orange-800' :
            a.severity === 'medium' ? 'border-yellow-800' :
            'border-gray-800'
          }`}>
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <SeverityBadge severity={a.severity} />
                  <StatusBadge status={a.status} />
                  <span className="text-gray-500 text-xs font-mono">{a.id.slice(0, 8)}...</span>
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

              <div className="flex flex-col items-end gap-2 ml-4 flex-shrink-0">
                {a.status === 'open' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => reviewMutation.mutate({ id: a.id, status: 'resolved' })}
                      disabled={reviewMutation.isPending}
                      className="px-3 py-1.5 bg-green-800 hover:bg-green-700 text-green-200 rounded text-xs font-medium transition-colors disabled:opacity-50"
                    >
                      Resolve
                    </button>
                    <button
                      onClick={() => reviewMutation.mutate({ id: a.id, status: 'false_positive' })}
                      disabled={reviewMutation.isPending}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs font-medium transition-colors disabled:opacity-50"
                    >
                      False Positive
                    </button>
                    <button
                      onClick={() => reviewMutation.mutate({ id: a.id, status: 'escalated' })}
                      disabled={reviewMutation.isPending}
                      className="px-3 py-1.5 bg-red-900 hover:bg-red-800 text-red-200 rounded text-xs font-medium transition-colors disabled:opacity-50"
                    >
                      Escalate
                    </button>
                  </div>
                )}

                {a.status !== 'open' && (
                  <span className="text-gray-500 text-xs">
                    {a.status === 'resolved' ? '✓ Resolved' :
                     a.status === 'escalated' ? '⬆ Escalated' :
                     a.status === 'false_positive' ? '✗ False Positive' : ''}
                  </span>
                )}

                <button
                  onClick={() => assessMutation.mutate(a.id)}
                  disabled={assessMutation.isPending}
                  className="px-3 py-1.5 bg-indigo-900 hover:bg-indigo-800 text-indigo-200 rounded text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {assessments[a.id] ? 'Re-run Legal Opinion' : 'Get Legal Opinion'}
                </button>
              </div>
            </div>

            {assessments[a.id] && (
              <ComplianceOpinionPanel assessment={assessments[a.id]} />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function ComplianceOpinionPanel({ assessment }: { assessment: ComplianceAssessment }) {
  const actionLabels: Record<string, string> = {
    close_no_action: 'Close — no further action required',
    enhanced_monitoring: 'Continue enhanced monitoring',
    enhanced_due_diligence: 'Perform Enhanced Due Diligence (EDD)',
    file_sar: 'File a Suspicious Activity Report (SAR)',
    block_and_file_ofac_report: 'Block assets and file an OFAC blocked-property report',
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-800 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-indigo-300 text-xs font-semibold uppercase tracking-wide">
          Compliance Officer Agent
        </span>
        <span className="text-gray-500 text-xs">
          confidence {Math.round(assessment.confidence * 100)}%
        </span>
      </div>

      <p className="text-white text-sm font-medium">
        {actionLabels[assessment.recommended_action] || assessment.recommended_action}
      </p>

      <div className="flex flex-wrap gap-2 text-xs">
        {assessment.regulatory_citations.map(c => (
          <span
            key={c.statute}
            title={c.requirement}
            className="px-2 py-1 rounded bg-gray-800 text-gray-300 border border-gray-700"
          >
            {c.statute}
          </span>
        ))}
      </div>

      {(assessment.sar_filing_deadline || assessment.ofac_report_deadline) && (
        <p className="text-yellow-400 text-xs">
          {assessment.ofac_report_deadline &&
            `OFAC report due ${new Date(assessment.ofac_report_deadline).toLocaleDateString()}. `}
          {assessment.sar_filing_deadline &&
            `SAR filing due ${new Date(assessment.sar_filing_deadline).toLocaleDateString()}.`}
        </p>
      )}

      <pre className="text-gray-400 text-xs whitespace-pre-wrap font-sans bg-gray-950 rounded-lg p-3 border border-gray-800">
        {assessment.narrative}
      </pre>
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