import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Kiosk from '@/pages/Kiosk'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string, opts?: any) => {
      const map: Record<string,string> = {
        'kiosk.selectUser': 'Select User',
        'kiosk.selectProduct': 'Select Product',
        'kiosk.confirmPurchase': 'Confirm Purchase',
        'kiosk.purchaseComplete': 'Purchase Complete',
        'kiosk.userBalance': 'Balance',
        'kiosk.belowThreshold': 'Below threshold',
        'pin.confirmAccessTitle': `Confirm access for ${opts?.name || ''}`,
        'pin.confirmAccessMessage': 'Enter PIN to continue',
        'pin.placeholder': 'Enter PIN',
        'pin.required': 'PIN required',
        'pin.confirmAccess': 'Confirm Access',
        'common.cancel': 'Cancel',
        'common.confirm': 'Confirm',
        'common.total': 'Total',
        'common.user': 'User',
        'common.product': 'Product',
        'common.price': 'Price',
        'common.quantity': 'Quantity',
        'errors.insufficientBalance': 'Insufficient balance',
      }
      return map[k] || k
    }
  })
}))

// Mock store (zustand)
vi.mock('@/store', async () => {
  const actual = await vi.importActual<any>('zustand')
  const create = actual.create
  const store: any = {
    selectedUser: null,
    setSelectedUser: (u: any) => { store.selectedUser = u },
    language: 'en', setLanguage: () => {},
    sidebarOpen: false, setSidebarOpen: () => {},
    currentUser: null, setCurrentUser: () => {},
    treasurerAuthenticated: false, setTreasurerAuthenticated: () => {},
    authTimestamp: null, setAuthTimestamp: () => {},
  }
  const useAppStore = create(() => store)
  return { useAppStore }
})

// Mock API client calls used in Kiosk
vi.mock('@/api/client', () => {
  return {
    usersApi: {
      getAll: vi.fn().mockResolvedValue({ data: [ { id: 'u1', display_name: 'Alice', role: 'user', email: 'a@a.a', is_active: true } ] }),
      getBalance: vi.fn().mockResolvedValue({ data: { user: { id: 'u1', display_name: 'Alice' }, balance_cents: 1500 } }),
      verifyPin: vi.fn((_id: string, pin: string) => {
        if (pin === '1234') return Promise.resolve({ data: { message: 'ok' } })
        return Promise.reject({ response: { data: { detail: 'Invalid PIN' } } })
      }),
    },
    productsApi: {
      getAll: vi.fn().mockResolvedValue({ data: [ { id: 'p1', name: 'Coffee', price_cents: 100, is_active: true } ] }),
    },
    consumptionsApi: {
      create: vi.fn().mockResolvedValue({ data: { id: 'c1' } }),
    },
  }
})

const renderKiosk = () => {
  const qc = new QueryClient()
  return render(
    <QueryClientProvider client={qc}>
      <Kiosk />
    </QueryClientProvider>
  )
}

describe('Kiosk single PIN flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('verifies user PIN once then allows purchase without second PIN prompt', async () => {
    renderKiosk()
    // select user
    const userBtns = await screen.findAllByTestId('user-btn-u1')
    fireEvent.click(userBtns[0])
    await screen.findByText(/Confirm access for/i)

    // enter correct PIN
    const pinInput = screen.getByPlaceholderText('Enter PIN') as HTMLInputElement
    fireEvent.change(pinInput, { target: { value: '1234' } })
    fireEvent.click(screen.getByText('Confirm Access'))

    // product selection
    await screen.findByText('Select Product')
    const productCard = await screen.findByText('Coffee')
    fireEvent.click(productCard)

    // confirm page should appear directly with confirm button
    await screen.findByText('Confirm Purchase')

    // ensure no additional PIN input present
    const pinInputs = screen.queryAllByPlaceholderText('Enter PIN')
    expect(pinInputs.length).toBe(0)

    fireEvent.click(screen.getByText('Confirm'))

    await waitFor(() => {
      expect(screen.getByText('Purchase Complete')).toBeInTheDocument()
    })
  })

  it('shows error for invalid PIN and requires retry', async () => {
    renderKiosk()
    const userBtns = await screen.findAllByTestId('user-btn-u1')
    fireEvent.click(userBtns[0])
    await screen.findByText(/Confirm access for/i)
    const pinInput = screen.getByPlaceholderText('Enter PIN') as HTMLInputElement
    fireEvent.change(pinInput, { target: { value: '0000' } })
    fireEvent.click(screen.getByText('Confirm Access'))
    await waitFor(() => {
      expect(screen.getByText('Invalid PIN')).toBeInTheDocument()
    })
  })
})
