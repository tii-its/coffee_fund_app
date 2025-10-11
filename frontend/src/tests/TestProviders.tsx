import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '@/components/Toast'
import { I18nextProvider } from 'react-i18next'
import i18n from '../i18n'

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

interface TestProvidersProps { children: React.ReactNode; queryClient?: QueryClient }

export const TestProviders: React.FC<TestProvidersProps> = ({ children, queryClient }) => {
  const qc = queryClient || createTestQueryClient()
  return (
    <QueryClientProvider client={qc}>
      <I18nextProvider i18n={i18n}>
        <BrowserRouter>
          <ToastProvider>
            {children}
          </ToastProvider>
        </BrowserRouter>
      </I18nextProvider>
    </QueryClientProvider>
  )
}

// Optional helper if we want to import a single function
export function withTestProviders(ui: React.ReactNode, queryClient?: QueryClient) {
  return <TestProviders queryClient={queryClient}>{ui}</TestProviders>
}
