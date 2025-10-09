// @ts-nocheck
import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nextProvider } from 'react-i18next'
import i18n from '../i18n'

import Dashboard from '../pages/Dashboard'
import { makeUser } from '../tests/factories'

// Global holders to avoid TDZ issues with vi.mock hoisting
// We populate these in beforeEach; factory functions access them at call time.
// @ts-ignore
globalThis.__mocks = {
  usersApi: {},
  moneyMovesApi: {},
  consumptionsApi: {},
  productsApi: {},
  store: {},
}

vi.mock('@/api/client', () => ({
  usersApi: new Proxy({}, { get: (_, prop) => (globalThis as any).__mocks.usersApi[prop] }),
  moneyMovesApi: new Proxy({}, { get: (_, prop) => (globalThis as any).__mocks.moneyMovesApi[prop] }),
  consumptionsApi: new Proxy({}, { get: (_, prop) => (globalThis as any).__mocks.consumptionsApi[prop] }),
  productsApi: new Proxy({}, { get: (_, prop) => (globalThis as any).__mocks.productsApi[prop] }),
}))

vi.mock('@/store', () => ({
  useAppStore: () => (globalThis as any).__mocks.store,
}))

vi.mock('@/components/Toast', () => ({
  useToast: () => ({ notify: vi.fn() }),
}))

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
    </QueryClientProvider>
  )
}

describe('Dashboard Top Up Flow', () => {
  const user = makeUser({ id: 'user-1', display_name: 'User One', role: 'user' })

  beforeEach(() => {
    vi.clearAllMocks()
    const mocks: any = (globalThis as any).__mocks
    // Assign fresh spies each test run
    mocks.usersApi.getAll = vi.fn().mockResolvedValue({ data: [user] })
    mocks.usersApi.verifyPin = vi.fn().mockResolvedValue({ data: { message: 'ok' } })
    mocks.usersApi.getBalance = vi.fn().mockResolvedValue({ data: { balance_cents: 0, user } })
    mocks.consumptionsApi.getUserRecent = vi.fn().mockResolvedValue({ data: [] })
    mocks.moneyMovesApi.getAll = vi.fn().mockResolvedValue({ data: [] })
    mocks.moneyMovesApi.createUserRequest = vi.fn().mockResolvedValue({
      data: { id: 'mm-auto', type: 'deposit', user_id: user.id, amount_cents: 1250, status: 'pending', created_by: user.id },
    })
    mocks.productsApi.getLatest = vi.fn().mockResolvedValue({ data: null })
    mocks.productsApi.getTopConsumers = vi.fn().mockResolvedValue({ data: [] })
    // simple mutable store imitation; setCurrentUser mutates object so re-render (triggered by other state updates) sees new value
  const storeObj: any = { currentUser: null, selectedUser: null }
    storeObj.setCurrentUser = (u: any) => { storeObj.currentUser = u }
    storeObj.setSelectedUser = (u: any) => { storeObj.selectedUser = u }
    mocks.store = storeObj
  })

  it('allows self top-up request after PIN verification and PIN re-entry in modal', async () => {
    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    )

    // Select the user (UserPicker should render a button with user name)
    await waitFor(() => expect(screen.getByText('User One')).toBeInTheDocument())
    fireEvent.click(screen.getByText('User One'))

    // Enter PIN in inline verification panel
  const pinInput = await screen.findByPlaceholderText(/Enter PIN/i)
    fireEvent.change(pinInput, { target: { value: '1234' } })
  // Confirm access button uses translated text "Confirm Access"
  const confirmAccessEls = await screen.findAllByText(/Confirm Access/i)
  const confirmBtn = confirmAccessEls.find(el => el.tagName === 'BUTTON') as HTMLButtonElement
  if (!confirmBtn) throw new Error('Confirm Access button not found')
  fireEvent.click(confirmBtn)

    // Wait for balance card area (Top Up button should appear)
    await waitFor(() => expect(screen.getAllByText(/Top Up Balance/i).length).toBeGreaterThan(0))

    // Simulate store currentUser set after verification (Dashboard calls setCurrentUser internally already, but we ensure it here)
    ;(globalThis as any).__mocks.store.setCurrentUser(user)
    fireEvent.click(screen.getAllByText(/Top Up Balance/i)[0])

    // Fill real modal
    const amountInput = await screen.findByTestId('topup-amount')
    fireEvent.change(amountInput, { target: { value: '12.50' } })
    const pinInput2 = await screen.findByTestId('topup-pin')
    fireEvent.change(pinInput2, { target: { value: '1234' } })
    const noteInput = await screen.findByTestId('topup-note')
    fireEvent.change(noteInput, { target: { value: 'Integration test top-up' } })
    const submitBtn = await screen.findByTestId('topup-submit')
    fireEvent.click(submitBtn)

    await waitFor(() => expect((globalThis as any).__mocks.moneyMovesApi.createUserRequest).toHaveBeenCalled())
    const callPayload = (globalThis as any).__mocks.moneyMovesApi.createUserRequest.mock.calls[0][0]
    expect(callPayload.amount_cents).toBe(1250)
    expect(callPayload.note).toBe('Integration test top-up')
  })
})
