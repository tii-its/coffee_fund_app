import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ToastProvider, useToast } from '@/components/Toast'

const Trigger: React.FC = () => {
  const { notify } = useToast()
  React.useEffect(() => {
    notify({ text: 'Hello Toast', type: 'info', timeout: 10 })
  }, [notify])
  return <div>Trigger</div>
}

describe('ToastProvider', () => {
  it('renders a toast message when notify is called', async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    )
    await waitFor(() => {
      expect(screen.getByText('Hello Toast')).toBeInTheDocument()
    })
  })
})
