import axios from 'axios'
import type {
  User,
  UserBalance,
  UserCreate,
  UserUpdate,
  Product,
  ProductCreate,
  ProductUpdate,
  ProductConsumptionStats,
  Consumption,
  ConsumptionCreate,
  MoneyMove,
  MoneyMoveCreate,
  AuditEntry,
  Settings,
  HealthCheck,
  StockPurchase,
  StockPurchaseWithCreator,
  StockPurchaseCreate,
  StockPurchaseUpdate,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Error interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Users API
export const usersApi = {
  getAll: (params?: { skip?: number; limit?: number; active_only?: boolean }) =>
    api.get<User[]>('/users/', { params }),
  
  getById: (id: string) =>
    api.get<User>(`/users/${id}`),
  
  create: (user: UserCreate, pin: string, creator_id?: string) =>
    api.post<User>('/users/', { user, pin }, { params: { creator_id } }),
  
  update: (id: string, user: UserUpdate, pin: string, actor_id?: string) =>
    api.put<User>(`/users/${id}`, { user_update: user, pin }, { params: { actor_id } }),
  
  delete: (id: string, pin: string, actor_id?: string) =>
    api.delete(`/users/${id}`, {
      data: { pin },
      params: { actor_id }
    }),
  
  getBalance: (id: string) =>
    api.get<UserBalance>(`/users/${id}/balance`),
  
  getQRCode: (id: string) =>
    api.get<{ qr_code: string }>(`/users/${id}/qr-code`),
  
  getAllBalances: () =>
    api.get<UserBalance[]>('/users/balances/all'),
  
  getBelowThreshold: (threshold_cents?: number) =>
    api.get<UserBalance[]>('/users/balances/below-threshold', {
      params: { threshold_cents },
    }),
  
  getAboveThreshold: (threshold_cents?: number) =>
    api.get<UserBalance[]>('/users/balances/above-threshold', {
      params: { threshold_cents },
    }),
}

// Products API
export const productsApi = {
  getAll: (params?: { skip?: number; limit?: number; active_only?: boolean }) =>
    api.get<Product[]>('/products/', { params }),
  
  getById: (id: string) =>
    api.get<Product>(`/products/${id}`),
  
  create: (product: ProductCreate, creator_id?: string) =>
    api.post<Product>('/products/', product, { params: { creator_id } }),
  
  update: (id: string, product: ProductUpdate, actor_id?: string) =>
    api.put<Product>(`/products/${id}`, product, { params: { actor_id } }),
  
  delete: (id: string, actor_id?: string) =>
    api.delete(`/products/${id}`, { params: { actor_id } }),
  
  getLatest: () =>
    api.get<Product | null>('/products/latest'),
  
  getTopConsumers: (limit_per_product?: number) =>
    api.get<ProductConsumptionStats[]>('/products/top-consumers', {
      params: { limit_per_product },
    }),
}

// Consumptions API
export const consumptionsApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    user_id?: string
    product_id?: string
  }) => api.get<Consumption[]>('/consumptions/', { params }),
  
  getById: (id: string) =>
    api.get<Consumption>(`/consumptions/${id}`),
  
  create: (consumption: ConsumptionCreate, creator_id: string) =>
    api.post<Consumption>('/consumptions/', consumption, {
      params: { creator_id },
    }),
  
  getUserRecent: (user_id: string, limit?: number) =>
    api.get<Consumption[]>(`/consumptions/user/${user_id}/recent`, {
      params: { limit },
    }),
}

// Money Moves API
export const moneyMovesApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    user_id?: string
    status?: 'pending' | 'confirmed' | 'rejected'
  }) => api.get<MoneyMove[]>('/money-moves/', { params }),
  
  getById: (id: string) =>
    api.get<MoneyMove>(`/money-moves/${id}`),
  
  create: (moneyMove: MoneyMoveCreate, creator_id: string) =>
    api.post<MoneyMove>('/money-moves/', moneyMove, {
      params: { creator_id },
    }),
  
  getPending: (params?: { skip?: number; limit?: number }) =>
    api.get<MoneyMove[]>('/money-moves/pending', { params }),
  
  confirm: (id: string, confirmer_id: string) =>
    api.patch<MoneyMove>(`/money-moves/${id}/confirm`, null, {
      params: { confirmer_id },
    }),
  
  reject: (id: string, rejector_id: string) =>
    api.patch<MoneyMove>(`/money-moves/${id}/reject`, null, {
      params: { rejector_id },
    }),
}

// Audit API
export const auditApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    actor_id?: string
    entity?: string
    entity_id?: string
  }) => api.get<AuditEntry[]>('/audit/', { params }),
  
  getById: (id: string) =>
    api.get<AuditEntry>(`/audit/${id}`),
}

// Exports API
export const exportsApi = {
  consumptions: (limit?: number) =>
    api.get('/exports/consumptions', {
      params: { limit },
      responseType: 'blob',
    }),
  
  moneyMoves: (limit?: number) =>
    api.get('/exports/money-moves', {
      params: { limit },
      responseType: 'blob',
    }),
  
  balances: () =>
    api.get('/exports/balances', {
      responseType: 'blob',
    }),
}

// Settings API
export const settingsApi = {
  get: () => api.get<Settings>('/settings/'),
  
  health: () => api.get<HealthCheck>('/settings/health'),
}

// Stock Purchases API
export const stockPurchasesApi = {
  getAll: (params?: {
    skip?: number
    limit?: number
    cash_out_processed?: boolean
  }) => api.get<StockPurchaseWithCreator[]>('/stock-purchases/', { params }),
  
  getById: (id: string) =>
    api.get<StockPurchaseWithCreator>(`/stock-purchases/${id}`),
  
  create: (stockPurchase: StockPurchaseCreate, creator_id: string) =>
    api.post<StockPurchase>('/stock-purchases/', stockPurchase, {
      params: { creator_id },
    }),
  
  update: (id: string, stockPurchase: StockPurchaseUpdate, actor_id: string) =>
    api.patch<StockPurchase>(`/stock-purchases/${id}`, stockPurchase, {
      params: { actor_id },
    }),
  
  processCashOut: (id: string, actor_id: string) =>
    api.patch<StockPurchase>(`/stock-purchases/${id}/cash-out`, null, {
      params: { actor_id },
    }),
  
  delete: (id: string, actor_id: string) =>
    api.delete(`/stock-purchases/${id}`, { params: { actor_id } }),
}

export default api