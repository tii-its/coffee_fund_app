
export interface TestUserOverrides {
  id?: string
  display_name?: string
  role?: 'user' | 'admin' | 'treasurer'
  is_active?: boolean
  email?: string
  created_at?: string
  qr_code?: string | null
}

export function makeUser(overrides: TestUserOverrides = {}) {
  return {
  id: overrides.id || 'u_' + Math.random().toString(36).slice(2,10),
    display_name: overrides.display_name || 'User ' + Math.random().toString(36).slice(2,7),
    role: overrides.role || 'user',
    is_active: overrides.is_active ?? true,
    email: overrides.email || 'test@example.com',
    created_at: overrides.created_at || new Date().toISOString(),
    qr_code: overrides.qr_code ?? null,
  }
}
