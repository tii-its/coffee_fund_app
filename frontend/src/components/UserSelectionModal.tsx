import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { AxiosResponse } from 'axios'
import { usersApi } from '@/api/client'
import UserPinInputModal from './UserPinInputModal'
import type { User } from '@/api/types'

interface UserSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  onUserSelected: (user: User) => void
  title?: string
  description?: string
}

const UserSelectionModal: React.FC<UserSelectionModalProps> = ({
  isOpen,
  onClose,
  onUserSelected,
  title,
  description,
}) => {
  const { t } = useTranslation()
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showPinModal, setShowPinModal] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users', 'active'],
    queryFn: () => usersApi.getAll({ active_only: true }).then((res: AxiosResponse<User[]>) => res.data),
    enabled: isOpen,
  })

  const handleUserClick = (user: User) => {
    setSelectedUser(user)
    setShowPinModal(true)
  }

  const handlePinSubmit = async (user: User, pin: string) => {
    setIsVerifying(true)
    try {
      // Verify user PIN
      await usersApi.verifyUserPin(user.id, pin)
      setShowPinModal(false)
      setSelectedUser(null)
      onUserSelected(user)
      onClose()
    } catch (error) {
      throw error // Let UserPinInputModal handle the error display
    } finally {
      setIsVerifying(false)
    }
  }

  const handlePinModalClose = () => {
    setShowPinModal(false)
    setSelectedUser(null)
  }

  const handleClose = () => {
    setSelectedUser(null)
    setShowPinModal(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              {title || t('user.selectUser')}
            </h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {description && (
            <p className="text-gray-600 mb-4">{description}</p>
          )}

          <div className="overflow-y-auto max-h-[60vh]">
            {isLoading ? (
              <div className="flex justify-center items-center h-32">
                <div className="loading"></div>
              </div>
            ) : users.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {t('user.noUsers')}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {users.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleUserClick(user)}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 text-left transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {user.display_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {user.display_name}
                        </div>
                        <div className="text-sm text-gray-500 truncate">
                          {user.email}
                        </div>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            user.role === 'treasurer' 
                              ? 'bg-purple-100 text-purple-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {user.role === 'treasurer' ? t('user.treasurerRole') : t('user.userRole')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end mt-6">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              {t('common.cancel')}
            </button>
          </div>
        </div>
      </div>

      <UserPinInputModal
        isOpen={showPinModal}
        onClose={handlePinModalClose}
        onSubmit={handlePinSubmit}
        user={selectedUser}
        isLoading={isVerifying}
      />
    </>
  )
}

export default UserSelectionModal