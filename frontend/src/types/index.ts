export interface Customer {
  id: string
  name: string
  email: string
  phone?: string
  country: string
  kyc_status: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  total_transactions: number
  total_volume: number
  is_active: boolean
  is_sanctioned: boolean
  last_transaction_at?: string
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: string
  customer_id: string
  type: 'deposit' | 'withdrawal' | 'transfer'
  amount: number
  currency: string
  source_country?: string
  destination_country?: string
  risk_score: number
  risk_level?: string
  flagged: boolean
  status: 'pending' | 'completed' | 'failed' | 'flagged' | 'blocked'
  created_at: string
  processed_at?: string
}

export interface Alert {
  id: string
  customer_id: string
  transaction_id?: string
  rule_triggered: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  reason: string
  status: 'open' | 'in_review' | 'resolved' | 'false_positive' | 'escalated'
  reviewed: boolean
  reviewed_by?: string
  action_taken?: string
  created_at: string
}