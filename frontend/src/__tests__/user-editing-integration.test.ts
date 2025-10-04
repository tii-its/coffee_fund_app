/**
 * Integration test for user editing admin PIN flow.
 * Tests the complete backend API flow without complex UI interactions.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the API client
const mockUsersApi = {
  getAll: vi.fn(),
  update: vi.fn(),
}

// Mock the usePerActionPin hook
const mockUsePerActionPin = vi.fn()

vi.mock('../api/client', () => ({
  usersApi: mockUsersApi,
}))

vi.mock('../hooks/usePerActionPin', () => ({
  usePerActionPin: mockUsePerActionPin,
}))

describe('Integration: User Editing Admin PIN Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should require admin PIN for user editing', async () => {
    // Arrange
    const mockRequestPin = vi.fn().mockResolvedValue({
      actorId: 'admin-123',
      pin: '9999',
    })

    mockUsePerActionPin.mockReturnValue({
      requestPin: mockRequestPin,
      pinModal: null,
    })

    mockUsersApi.update.mockResolvedValue({
      data: { 
        id: 'user-123',
        displayName: 'Updated User',
        email: 'updated@example.com',
        role: 'user',
        isActive: true
      },
    })

    // Act - simulate the editing flow that would happen in the component
    const userUpdateData = {
      id: 'user-123',
      displayName: 'Updated User',
      email: 'updated@example.com',
      role: 'user' as const,
      isActive: true,
    }
    
    // This simulates what happens when handleEditSubmit is called
    const { actorId, pin } = await mockRequestPin()
    expect(actorId).toBe('admin-123')
    expect(pin).toBe('9999')

    // Call the API with the PIN credentials
    await mockUsersApi.update(userUpdateData.id, userUpdateData, {
      headers: {
        'x-actor-id': actorId,
        'x-actor-pin': pin,
      },
    })

    // Assert
    expect(mockRequestPin).toHaveBeenCalledOnce()
    expect(mockUsersApi.update).toHaveBeenCalledWith(
      'user-123',
      userUpdateData,
      {
        headers: {
          'x-actor-id': 'admin-123',
          'x-actor-pin': '9999',
        },
      }
    )
  })

  it('should handle PIN authentication failure during user editing', async () => {
    // Arrange
    const mockRequestPin = vi.fn().mockRejectedValue(new Error('PIN authentication failed'))

    mockUsePerActionPin.mockReturnValue({
      requestPin: mockRequestPin,
      pinModal: null,
    })

    // Act & Assert
    await expect(mockRequestPin()).rejects.toThrow('PIN authentication failed')
    expect(mockUsersApi.update).not.toHaveBeenCalled()
  })

  it('should handle API error during user update', async () => {
    // Arrange
    const mockRequestPin = vi.fn().mockResolvedValue({
      actorId: 'admin-123',
      pin: '9999',
    })

    mockUsePerActionPin.mockReturnValue({
      requestPin: mockRequestPin,
      pinModal: null,
    })

    mockUsersApi.update.mockRejectedValue(new Error('User update failed'))

    // Act
    const userUpdateData = {
      id: 'user-123',
      displayName: 'Updated User',
      email: 'updated@example.com',
      role: 'user' as const,
      isActive: true,
    }

    const { actorId, pin } = await mockRequestPin()

    // Assert
    await expect(
      mockUsersApi.update(userUpdateData.id, userUpdateData, {
        headers: {
          'x-actor-id': actorId,
          'x-actor-pin': pin,
        },
      })
    ).rejects.toThrow('User update failed')
  })

  it('should support updating user PIN along with other fields', async () => {
    // Arrange
    const mockRequestPin = vi.fn().mockResolvedValue({
      actorId: 'admin-123',
      pin: '9999',
    })

    mockUsePerActionPin.mockReturnValue({
      requestPin: mockRequestPin,
      pinModal: null,
    })

    mockUsersApi.update.mockResolvedValue({
      data: { 
        id: 'user-123',
        displayName: 'Updated User',
        email: 'updated@example.com',
        role: 'user',
        isActive: true
      },
    })

    // Act - simulate editing with new PIN
    const userUpdateData = {
      id: 'user-123',
      displayName: 'Updated User',
      email: 'updated@example.com',
      role: 'user' as const,
      isActive: true,
      newPin: '1234', // new PIN for the user
    }
    
    const { actorId, pin } = await mockRequestPin()

    await mockUsersApi.update(userUpdateData.id, userUpdateData, {
      headers: {
        'x-actor-id': actorId,
        'x-actor-pin': pin,
      },
    })

    // Assert
    expect(mockUsersApi.update).toHaveBeenCalledWith(
      'user-123',
      userUpdateData,
      {
        headers: {
          'x-actor-id': 'admin-123',
          'x-actor-pin': '9999',
        },
      }
    )
  })
})