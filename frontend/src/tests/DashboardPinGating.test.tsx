import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '@/components/Toast'
import Dashboard from '@/pages/Dashboard'
// api client fully mocked below

// Mock i18n translation hook
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, opts?: any) => {
    if (k === 'pin.confirmAccessTitle') return `Confirm access for ${opts?.name || ''}`
    const map: Record<string,string> = {
      'kiosk.selectUser': 'Select User',
      'pin.noUserSelectedMessage': 'Select a user to view dashboard details',
      'pin.confirmAccessMessage': 'Enter this user\'s PIN to view their dashboard.',
      'pin.placeholder': 'Enter PIN',
      'pin.required': 'PIN required',
      'pin.confirmAccess': 'Confirm Access',
      'pin.accessGranted': 'Access granted',
      'pin.accessDenied': 'Access denied'
    }
    return map[k] || k
  })
}))

// Mock store (zustand)
vi.mock('@/store', async () => {
  const actual = await vi.importActual<any>('zustand')
  const create = actual.create
  const store: any = {
    selectedUser: null,
    setSelectedUser: (u: any) => { store.selectedUser = u },
    language: 'en',
    setLanguage: () => {},
    sidebarOpen: true,
    setSidebarOpen: () => {},
    currentUser: null,
    setCurrentUser: (u: any) => { store.currentUser = u },
    treasurerAuthenticated: false,
    setTreasurerAuthenticated: () => {},
    authTimestamp: null,
    setAuthTimestamp: () => {},
  }
  const useAppStore = create(() => store)
  return { useAppStore }
})

// Mock API client calls used in Dashboard queries
vi.mock('@/api/client', async () => {
  return {
    usersApi: {
      getAll: vi.fn().mockResolvedValue({ data: [ { id: 'u1', display_name: 'Test User', role: 'user', email: 't@t.t', is_active: true } ] }),
      getBalance: vi.fn().mockResolvedValue({ data: { user_id: 'u1', balance_cents: 500 } }),
      getAllBalances: vi.fn().mockResolvedValue({ data: [] }),
      getAboveThreshold: vi.fn().mockResolvedValue({ data: [] }),
      getBelowThreshold: vi.fn().mockResolvedValue({ data: [] }),
      verifyPin: vi.fn((_id: string, pin: string) => {
        if (pin === '1234') return Promise.resolve({ data: { message: 'ok' } })
        return Promise.reject({ response: { data: { detail: 'Invalid PIN' } } })
      }),
    },
    consumptionsApi: { getUserRecent: vi.fn().mockResolvedValue({ data: [] }) },
    moneyMovesApi: { getAll: vi.fn().mockResolvedValue({ data: [] }) },
    productsApi: { getTopConsumers: vi.fn().mockResolvedValue({ data: [] }), getLatest: vi.fn().mockResolvedValue({ data: null }) },
  }
})

const renderDashboard = () => {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Dashboard />
      </ToastProvider>
    </QueryClientProvider>
  )
}

describe('Dashboard PIN gating', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows PIN panel after selecting a user', async () => {
    renderDashboard()
    // Wait for user picker
    const userBtn = await screen.findByTestId('user-btn-u1')
    fireEvent.click(userBtn)
    await screen.findByText(/Confirm access for/i)
    expect(screen.getByPlaceholderText('Enter PIN')).toBeInTheDocument()
  })

  it('shows error toast when PIN invalid', async () => {
    renderDashboard()
    const userBtn = await screen.findByTestId('user-btn-u1')
    fireEvent.click(userBtn)
    await screen.findByText(/Confirm access for/i)
    const input = screen.getByPlaceholderText('Enter PIN') as HTMLInputElement
    fireEvent.change(input, { target: { value: '9999' } })
    fireEvent.click(screen.getByText('Confirm Access'))
    await waitFor(() => {
      expect(screen.getByText('Access denied')).toBeInTheDocument()
    })
  })

  it('grants access and shows success toast on correct PIN', async () => {
    renderDashboard()
    const userBtn = await screen.findByTestId('user-btn-u1')
    fireEvent.click(userBtn)
    await screen.findByText(/Confirm access for/i)
    const input = screen.getByPlaceholderText('Enter PIN') as HTMLInputElement
    fireEvent.change(input, { target: { value: '1234' } })
    fireEvent.click(screen.getByText('Confirm Access'))
    await waitFor(() => {
      expect(screen.getByText('Access granted')).toBeInTheDocument()
    })
    // Dashboard header should show user name now
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument()
    })
  })
})
