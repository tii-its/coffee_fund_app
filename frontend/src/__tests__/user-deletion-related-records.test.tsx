import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TestProviders } from '@/tests/TestProviders'
import Users from '@/pages/Users'
import { makeUser } from '@/tests/factories'

vi.mock('@/api/client', () => {
  return {
    usersApi: {
      getAll: vi.fn(),
      delete: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    }
  }
})

vi.mock('@/hooks/usePerActionPin', () => ({
  usePerActionPin: () => ({
    requestPin: vi.fn().mockResolvedValue({ actorId: 'admin-1', pin: '1234' }),
    pinModal: null,
  })
}))

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (k: string) => {
      const map: Record<string,string> = {
        'navigation.users': 'Users',
        'user.createUser': 'Create User',
        'user.displayName': 'Display Name',
        'user.role': 'Role',
        'common.status': 'Status',
        'common.date': 'Date',
        'common.actions': 'Actions',
        'common.edit': 'Edit',
        'common.delete': 'Delete',
        'common.cancel': 'Cancel',
        'user.deleteUser': 'Delete User',
        'user.deleteConfirmation.warningTitle': 'User has related records',
        'user.deleteConfirmation.warningMessage': 'The user has related records.',
        'user.deleteConfirmation.relatedRecords': 'Related records:',
        'user.deleteConfirmation.consequences': 'User will be deactivated but history preserved.',
        'user.deleteConfirmation.records.consumptions': 'Consumptions',
        'user.deleteConfirmation.records.moneyMoves': 'Money moves',
        'user.deleteConfirmation.delete': 'Delete User',
        'user.deleteConfirmation.deactivate': 'Deactivate User',
        'user.deleteConfirmation.simpleMessage': 'Are you sure?',
      }
      return map[k] || k
    }
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
  I18nextProvider: ({ children }: any) => <>{children}</>,
}))

import { usersApi } from '@/api/client'

const wrapper = (ui: React.ReactNode) => <TestProviders>{ui}</TestProviders>

describe('User deletion with related records 409 flow', () => {
  const targetUser = makeUser({ id: 'u1', display_name: 'Has History', role: 'user' })

  beforeEach(() => {
    vi.clearAllMocks()
  ;(usersApi.getAll as any).mockResolvedValue({ data: [ targetUser ] })
    // First delete attempt returns 409 requiring confirmation
  ;(usersApi.delete as any).mockRejectedValueOnce({
      response: {
        status: 409,
        data: { detail: { confirmation_required: true, related_records: { consumptions: true, money_moves: true } } }
      }
    })
    // Second (force) attempt resolves success
  ;(usersApi.delete as any).mockResolvedValue({ data: { message: 'deactivated' } })
  })

  it('prompts for related-records confirmation and then deactivates on force', async () => {
    render(wrapper(<Users />))

    await screen.findByText(targetUser.display_name)

  fireEvent.click(screen.getByText('Delete'))
  const deleteUserTexts = await screen.findAllByText('Delete User')
  expect(deleteUserTexts.length).toBeGreaterThan(0)

    // First confirm triggers 409 path: modal remains open and force button appears
    fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    await waitFor(() => {
      // Force deactivate button should now be rendered
      expect(screen.getByTestId('force-deactivate-btn')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('force-deactivate-btn'))

    await waitFor(() => {
  expect((usersApi.delete as any)).toHaveBeenCalledTimes(2)
    })

    await waitFor(() => {
      expect(screen.queryByText('Delete User')).not.toBeInTheDocument()
    })
  })
})
