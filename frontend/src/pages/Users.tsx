import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDate } from '@/lib/utils'
import { usersApi } from '@/api/client'
import { usePerActionPin } from '@/hooks/usePerActionPin'
import type { User, UserUpdate, UserCreate } from '@/api/types'
import type { AxiosResponse } from 'axios'
import UserEditModal from '@/components/UserEditModal'
import UserCreateModal from '@/components/UserCreateModal'
import UserDeleteConfirmationModal from '@/components/UserDeleteConfirmationModal'
// usersApi already imported above

const Users: React.FC = () => {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    hasRelatedRecords: boolean
    relatedRecords?: any
  } | null>(null)

  // Admin gating removed: treasurer role should gate access (handled by route protection outside this component)
  
  // User creation requires admin role specifically
  const { requestPin: requestAdminPin, pinModal: adminPinModal } = usePerActionPin({ 
    requiredRole: 'admin',
    title: 'Admin PIN Required for User Creation'
  })

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.getAll({ active_only: false }).then((res: AxiosResponse<User[]>) => res.data),
  })

  // Removed global adminPin usage

  const createUserMutation = useMutation({
    mutationFn: async (userCreate: UserCreate) => {
      const { actorId, pin } = await requestAdminPin()
      if (!actorId || !pin) throw new Error('Admin PIN required')
      return usersApi.create({ actor_id: actorId, actor_pin: pin, user: userCreate })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setCreateModalOpen(false)
    },
    onError: (error: any) => {
      console.error('Failed to create user:', error)
    },
  })

  const updateUserMutation = useMutation({
    mutationFn: async ({ userId, userUpdate }: { userId: string, userUpdate: UserUpdate }) => {
      const { actorId, pin } = await requestAdminPin()
      if (!actorId || !pin) throw new Error('Admin PIN required')
      return usersApi.update(userId, userUpdate, { actorId, pin })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setEditModalOpen(false)
      setSelectedUser(null)
    },
    onError: (error: any) => {
      console.error('Failed to update user:', error)
    },
  })

  const deleteUserMutation = useMutation({
    mutationFn: async ({ userId, force = false }: { userId: string, force?: boolean }) => {
      const { actorId, pin } = await requestAdminPin()
      if (!actorId || !pin) throw new Error('Admin PIN required')
      return usersApi.delete(userId, { actorId, pin }, force)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setSelectedUser(null)
      setDeleteModalOpen(false)
      setDeleteConfirmation(null)
    },
    onError: (error: any) => {
      console.error('Failed to delete user:', error)
      // Handle specific error cases
      if (error.response?.status === 409) {
        const errorDetail = error.response?.data?.detail
        if (typeof errorDetail === 'object' && errorDetail.confirmation_required) {
          // Show confirmation dialog with related records info
          setDeleteConfirmation({
            hasRelatedRecords: true,
            relatedRecords: errorDetail.related_records
          })
          setDeleteModalOpen(true)
          return // Don't show error, show confirmation instead
        } else {
          alert(t('user.deleteError.hasRelatedRecords', 'Cannot delete user with related records'))
        }
      } else if (error.response?.status === 400) {
        alert(t('user.deleteError.lastAdmin', 'Cannot delete the last remaining admin user'))
      } else {
        alert(t('user.deleteError.general', 'Failed to delete user. Please try again.'))
      }
    },
  })

  const handleCreate = () => {
    setCreateModalOpen(true)
  }

  const handleEdit = (user: User) => {
    setSelectedUser(user)
    setEditModalOpen(true)
  }

  const handleDelete = (user: User) => {
    setSelectedUser(user)
    setDeleteModalOpen(true)
  }

  const handleDeleteConfirm = () => {
    if (!selectedUser) return
    deleteUserMutation.mutate({ userId: selectedUser.id })
  }

  const handleForceDeleteConfirm = () => {
    if (!selectedUser) return
    deleteUserMutation.mutate({ userId: selectedUser.id, force: true })
  }

  const handleCreateSubmit = async (userCreate: UserCreate) => {
    createUserMutation.mutate(userCreate)
  }

  const handleEditSubmit = async (userUpdate: UserUpdate) => {
    if (!selectedUser) return
    updateUserMutation.mutate({ userId: selectedUser.id, userUpdate })
  }

  // delete submit removed (inline confirm approach)

  // Removed admin PIN gating; page should be protected by treasurer route wrapper.

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="loading"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">{t('navigation.users')}</h2>
        <button 
          onClick={handleCreate}
          className="btn btn-primary"
        >
          {t('user.createUser')}
        </button>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('user.displayName')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('user.role')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.status')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.date')}
                </th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                  {t('common.actions')}
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user: User) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">👤</div>
                      <div>
                        <p className="font-medium text-gray-900">{user.display_name}</p>
                        {/* email removed */}
                        {user.qr_code && (
                          <p className="text-sm text-gray-500">QR: {user.qr_code}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${
                      user.role === 'admin' ? 'badge-danger' : 
                      user.role === 'treasurer' ? 'badge-info' : 'badge-success'
                    }`}>
                      {t(`user.${user.role}Role`)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${
                      user.is_active ? 'badge-success' : 'badge-danger'
                    }`}>
                      {user.is_active ? t('common.active') : t('common.inactive')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => handleEdit(user)}
                        className="btn btn-outline btn-sm hover:bg-blue-50"
                      >
                        {t('common.edit')}
                      </button>
                      <button 
                        onClick={() => handleDelete(user)}
                        className="btn btn-outline btn-sm text-red-600 hover:bg-red-50"
                      >
                        {t('common.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <UserCreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSubmit={handleCreateSubmit}
        isLoading={createUserMutation.isPending}
      />

      <UserEditModal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false)
          setSelectedUser(null)
        }}
        user={selectedUser}
        onSubmit={handleEditSubmit}
        isLoading={updateUserMutation.isPending}
      />

      <UserDeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false) 
          setSelectedUser(null)
          setDeleteConfirmation(null)
        }}
        onConfirm={handleDeleteConfirm}
        onForceConfirm={handleForceDeleteConfirm}
        userName={selectedUser?.display_name || ''}
        hasRelatedRecords={deleteConfirmation?.hasRelatedRecords || false}
        relatedRecords={deleteConfirmation?.relatedRecords}
      />

      {adminPinModal}
  </div>
  )
}

export default Users