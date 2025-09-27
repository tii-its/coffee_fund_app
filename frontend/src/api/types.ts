export interface User {
  id: string
  display_name: string
  email: string
  qr_code?: string | null
  role: 'user' | 'treasurer'
  is_active: boolean
  created_at: string
}

export interface UserBalance {
  user: User
  balance_cents: number
}

export interface UserCreate {
  display_name: string
  email: string
  qr_code?: string | null
  role: 'user' | 'treasurer'
  is_active?: boolean
  pin?: string  // Required for treasurer role
}

export interface UserUpdate {
  display_name?: string
  email?: string
  qr_code?: string | null
  role?: 'user' | 'treasurer'
  is_active?: boolean
}

export interface Product {
  id: string
  name: string
  price_cents: number
  icon?: string | null
  is_active: boolean
  created_at: string
}

export interface ProductCreate {
  name: string
  price_cents: number
  icon?: string | null
  is_active?: boolean
}

export interface ProductUpdate {
  name?: string
  icon?: string | null
  price_cents?: number
  is_active?: boolean
}

export interface Consumption {
  id: string
  user_id: string
  product_id: string
  qty: number
  unit_price_cents: number
  amount_cents: number
  at: string
  created_by: string
  user: User
  product: Product
}

export interface ConsumptionCreate {
  user_id: string
  product_id: string
  qty: number
}

export interface MoneyMove {
  id: string
  type: 'deposit' | 'payout'
  user_id: string
  amount_cents: number
  note?: string | null
  created_at: string
  created_by: string
  confirmed_at?: string | null
  confirmed_by?: string | null
  status: 'pending' | 'confirmed' | 'rejected'
  user: User
}

export interface MoneyMoveCreate {
  type: 'deposit' | 'payout'
  user_id: string
  amount_cents: number
  note?: string | null
}

export interface AuditEntry {
  id: string
  actor_id: string
  action: string
  entity: string
  entity_id: string
  meta_json?: Record<string, any> | null
  at: string
  actor: User
}

export interface Settings {
  threshold_cents: number
  csv_export_limit: number
}

export interface HealthCheck {
  status: string
  message: string
}