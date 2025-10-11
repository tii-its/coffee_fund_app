/**
 * Test user deletion functionality with admin PIN confirmation.
 */
import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Users from '../pages/Users'
import { usersApi } from '../api/client'
import { makeUser } from '@/tests/factories'
import { usePerActionPin } from '../hooks/usePerActionPin'
import { TestProviders } from '@/tests/TestProviders'

// Mock the API client
vi.mock('../api/client', () => ({
  usersApi: {
    getAll: vi.fn(),
    delete: vi.fn(),
  }
}))

// Mock the usePerActionPin hook
vi.mock('../hooks/usePerActionPin', () => ({
  usePerActionPin: vi.fn(),
}))

// Mock react-i18next (include initReactI18next to satisfy i18n setup)
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      const translations: Record<string, string | ((p: any) => string)> = {
        'navigation.users': 'Users',
        'user.createUser': 'Create User',
        'user.displayName': 'Display Name',
        'user.role': 'Role',
        'common.status': 'Status',
        'common.date': 'Date',
        'common.actions': 'Actions',
        'common.edit': 'Edit',
        'common.delete': 'Delete',
        'common.active': 'Active',
        'common.inactive': 'Inactive',
        'user.userRole': 'User',
        'user.treasurerRole': 'Treasurer',
        'user.adminRole': 'Admin',
        'user.deleteUser': 'Delete User',
        'user.deleteConfirmation.simpleMessage': (p: any) => `Are you sure you want to permanently delete the user "${p.userName}"? This action cannot be undone.`,
        'user.deleteConfirmation': (p: any) => `Are you sure you want to delete the user '${p.name}'?`,
        'common.cancel': 'Cancel',
      }
      const translation = translations[key]
      return typeof translation === 'function' ? translation(params) : translation || key
    },
  }),
  initReactI18next: { type: '3rdParty', init: () => {} },
  I18nextProvider: ({ children }: any) => <>{children}</>,
}))

// Mock components that aren't relevant for this test
vi.mock('../components/UserEditModal', () => ({
  default: ({ isOpen }: { isOpen: boolean }) => isOpen ? <div data-testid="edit-modal">Edit Modal</div> : null,
}))

vi.mock('../components/UserCreateModal', () => ({
  default: ({ isOpen }: { isOpen: boolean }) => isOpen ? <div data-testid="create-modal">Create Modal</div> : null,
}))

vi.mock('../lib/utils', () => ({
  formatDate: vi.fn((date: string) => date),
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => <TestProviders>{children}</TestProviders>

describe('Users Page - Deletion Functionality', () => {
  const mockUsers = [
    makeUser({ id: 'user1', display_name: 'Test User 1', role: 'user', created_at: '2023-01-01T00:00:00Z' }),
    makeUser({ id: 'admin1', display_name: 'Admin User', role: 'admin', created_at: '2023-01-01T00:00:00Z' }),
    makeUser({ id: 'treasurer1', display_name: 'Treasurer User', role: 'treasurer', created_at: '2023-01-01T00:00:00Z' }),
  ]

  let mockRequestPin: ReturnType<typeof vi.fn>
  let mockPinModal: JSX.Element

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()

    // Setup usePerActionPin mock
    mockRequestPin = vi.fn()
    mockPinModal = <div data-testid="pin-modal">PIN Modal</div>

    vi.mocked(usePerActionPin).mockReturnValue({
      requestPin: mockRequestPin,
      pinModal: mockPinModal,
    })

    // Setup API mocks
    vi.mocked(usersApi.getAll).mockResolvedValue({
      data: mockUsers,
    } as any)

    vi.mocked(usersApi.delete).mockResolvedValue({
      data: { message: 'User deleted successfully' },
    } as any)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders users list with delete buttons', async () => {
    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument()
    })

    // Check that users are displayed
    expect(screen.getByText('Test User 1')).toBeInTheDocument()
    expect(screen.getByText('Admin User')).toBeInTheDocument()
    expect(screen.getByText('Treasurer User')).toBeInTheDocument()

    // Check that delete buttons are present
    const deleteButtons = screen.getAllByText('Delete')
    expect(deleteButtons).toHaveLength(3)
  })

  it('shows role badges with correct colors', async () => {
    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument()
    })

    // Check role badges
    expect(screen.getByText('User')).toBeInTheDocument()
    expect(screen.getByText('Admin')).toBeInTheDocument()
    expect(screen.getByText('Treasurer')).toBeInTheDocument()

    // Verify admin role has danger class (red background)
    const adminBadge = screen.getByText('Admin').closest('.badge')
    expect(adminBadge).toHaveClass('badge-danger')

    // Verify treasurer role has info class (blue background)
    const treasurerBadge = screen.getByText('Treasurer').closest('.badge')
    expect(treasurerBadge).toHaveClass('badge-info')

    // Verify user role has success class (green background)
    const userBadge = screen.getByText('User').closest('.badge')
    expect(userBadge).toHaveClass('badge-success')
  })

  it('opens delete confirmation modal when delete button is clicked', async () => {
    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Click delete button for first user
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    // Check that delete confirmation modal appears
    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Check modal buttons
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.getByTestId('confirm-delete-btn')).toBeInTheDocument()
  })

  it('closes delete confirmation modal when cancel is clicked', async () => {
    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Open delete modal
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Click cancel
    fireEvent.click(screen.getByText('Cancel'))

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText('Delete User')).not.toBeInTheDocument()
    })
  })

  it('requests admin PIN when delete is confirmed', async () => {
    // Setup PIN request mock to return admin credentials
    mockRequestPin.mockResolvedValue({
      actorId: 'admin-id',
      pin: '9999',
    })

    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Open delete modal
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Confirm delete
  fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    // Verify PIN was requested
    await waitFor(() => {
      expect(mockRequestPin).toHaveBeenCalledTimes(1)
    })

    // Verify API delete was called with correct parameters
    await waitFor(() => {
      expect(usersApi.delete).toHaveBeenCalledWith('user1', {
        actorId: 'admin-id',
        pin: '9999',
      }, false)
    })
  })

  it('handles PIN request cancellation gracefully', async () => {
    // Setup PIN request mock to reject (user cancelled)
    mockRequestPin.mockRejectedValue(new Error('PIN required'))

    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Open delete modal and confirm
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

  fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    // Verify PIN was requested
    await waitFor(() => {
      expect(mockRequestPin).toHaveBeenCalledTimes(1)
    })

    // Verify API delete was NOT called
    expect(usersApi.delete).not.toHaveBeenCalled()
  })

  it('handles API deletion errors', async () => {
    // Setup PIN request to succeed but API to fail
    mockRequestPin.mockResolvedValue({
      actorId: 'admin-id',
      pin: '9999',
    })

    vi.mocked(usersApi.delete).mockRejectedValue(new Error('Insufficient permissions'))

    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Open delete modal and confirm
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    // For minimal coverage ensure modal still present (no auto-close on failure)
    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Note: Error handling display would require additional UI components
    // that aren't implemented yet (toast notifications, etc.)
  })

  it('closes delete modal and clears selection after successful deletion', async () => {
    mockRequestPin.mockResolvedValue({
      actorId: 'admin-id',
      pin: '9999',
    })

    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Test User 1').length).toBeGreaterThan(0)
    })

    // Open delete modal
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Confirm delete
  fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    // Wait for deletion to complete
    await waitFor(() => {
      expect(usersApi.delete).toHaveBeenCalled()
    })

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText('Delete User')).not.toBeInTheDocument()
    })
  })

  it('opens delete modal for different users sequentially', async () => {
    render(
      <TestWrapper>
        <Users />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryAllByText('Admin User').length).toBeGreaterThan(0)
    })

    // Click delete for admin user
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[1]) // Admin is second in the list

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })

    // Close modal
    fireEvent.click(screen.getByText('Cancel'))

    // Click delete for treasurer user
    await waitFor(() => {
      expect(screen.queryByText('Delete User')).not.toBeInTheDocument()
    })

    fireEvent.click(deleteButtons[2]) // Treasurer is third in the list

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument()
    })
  })
})